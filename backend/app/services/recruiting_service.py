"""
Recruiting Service
Business logic for recruiting workflow operations
"""

import asyncio
import logging
import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import pandas as pd
import re

from ..integrations.langflow.client import LangFlowClient
from ..integrations.zoho.client import ZohoClient
from ..schemas.recruiting_schemas import ProspectData, FlowConfig

logger = logging.getLogger(__name__)

class RecruitingService:
    """Service class for recruiting workflow operations"""

    def __init__(self):
        self.langflow_client = LangFlowClient()
        self.zoho_client = ZohoClient()
        self.mcp_client = ZohoClient()
        self.execution_cache = {}  # In production, use Redis
        self.outreach_cache = {}   # In production, use database

    async def execute_complete_flow(
        self,
        execution_id: str,
        prospects: List[ProspectData],
        flow_config: FlowConfig,
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the complete recruiting flow for multiple prospects"""
        try:
            logger.info(f"Starting recruiting flow execution {execution_id} for {len(prospects)} prospects")

            # Initialize execution status
            self.execution_cache[execution_id] = {
                "status": "running",
                "progress": 0,
                "current_step": "initialization",
                "completed_prospects": 0,
                "failed_prospects": 0,
                "results": {},
                "errors": [],
                "started_at": datetime.utcnow().isoformat()
            }

            total_prospects = len(prospects)
            results = {
                "execution_id": execution_id,
                "successful_contacts": 0,
                "failed_contacts": 0,
                "prospect_results": []
            }

            # Step 1: Validate and dedupe prospects
            self._update_execution_status(execution_id, "validating_prospects", 10)
            validated_prospects = await self._validate_prospects_batch(prospects)

            # Step 2: Deduplicate against Zoho CRM
            self._update_execution_status(execution_id, "deduplicating_prospects", 20)
            unique_prospects = await self._dedupe_prospects(validated_prospects)

            # Step 3: Process each prospect through the flow
            for i, prospect in enumerate(unique_prospects):
                try:
                    self._update_execution_status(
                        execution_id,
                        f"processing_prospect_{i+1}",
                        20 + (60 * (i + 1) / len(unique_prospects))
                    )

                    prospect_result = await self._process_single_prospect(
                        prospect, flow_config, user_context, execution_id
                    )

                    results["prospect_results"].append(prospect_result)

                    if prospect_result.get("success"):
                        results["successful_contacts"] += 1
                        self.execution_cache[execution_id]["completed_prospects"] += 1
                    else:
                        results["failed_contacts"] += 1
                        self.execution_cache[execution_id]["failed_prospects"] += 1

                    # Add delay between contacts if configured
                    if flow_config.delay_between_contacts > 0 and i < len(unique_prospects) - 1:
                        await asyncio.sleep(min(flow_config.delay_between_contacts, 60))

                except Exception as e:
                    logger.error(f"Error processing prospect {prospect.name}: {str(e)}")
                    results["failed_contacts"] += 1
                    self.execution_cache[execution_id]["failed_prospects"] += 1
                    self.execution_cache[execution_id]["errors"].append(
                        f"Prospect {prospect.name}: {str(e)}"
                    )

            # Step 4: Generate final report
            self._update_execution_status(execution_id, "generating_report", 90)
            await self._generate_execution_report(execution_id, results)

            # Mark as completed
            self._update_execution_status(execution_id, "completed", 100)
            self.execution_cache[execution_id]["results"] = results
            self.execution_cache[execution_id]["completed_at"] = datetime.utcnow().isoformat()

            logger.info(f"Recruiting flow {execution_id} completed: {results['successful_contacts']} successful, {results['failed_contacts']} failed")
            return results

        except Exception as e:
            logger.error(f"Error in recruiting flow execution {execution_id}: {str(e)}")
            self._update_execution_status(execution_id, "failed", None)
            self.execution_cache[execution_id]["errors"].append(str(e))
            raise

    async def _process_single_prospect(
        self,
        prospect: ProspectData,
        flow_config: FlowConfig,
        user_context: Dict[str, Any],
        execution_id: str
    ) -> Dict[str, Any]:
        """Process a single prospect through the recruiting flow"""
        try:
            # Prepare prospect data for LangFlow
            prospect_json = json.dumps({
                "name": prospect.name,
                "email": prospect.email,
                "phone": prospect.phone,
                "company": prospect.company,
                "license_number": prospect.license_number,
                "license_type": prospect.license_type,
                **prospect.additional_data
            })

            # Execute the LangFlow recruiting flow
            flow_result = await self.langflow_client.run_flow(
                flow_id="impact-realty-recruiting-flow",
                parameters={
                    "input_value": prospect_json,
                    "session_id": f"{execution_id}_{prospect.email}",
                    "sender": "Recruiter",
                    "execution_context": {
                        "execution_id": execution_id,
                        "prospect_id": prospect.email,
                        "flow_config": flow_config.dict(),
                        "user_context": user_context
                    }
                }
            )

            # Parse flow results to determine success
            success = self._evaluate_flow_success(flow_result)

            return {
                "prospect": prospect.dict(),
                "success": success,
                "flow_result": flow_result,
                "processed_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error processing prospect {prospect.name}: {str(e)}")
            return {
                "prospect": prospect.dict(),
                "success": False,
                "error": str(e),
                "processed_at": datetime.utcnow().isoformat()
            }

    def _evaluate_flow_success(self, flow_result: Dict[str, Any]) -> bool:
        """Evaluate if the flow execution was successful based on results"""
        try:
            # Look for success indicators in the flow result
            if not flow_result:
                return False

            # Check for successful outreach indicators
            result_text = str(flow_result).lower()
            success_indicators = ["sent", "delivered", "scheduled", "contacted", "success"]
            error_indicators = ["failed", "error", "rejected", "invalid"]

            has_success = any(indicator in result_text for indicator in success_indicators)
            has_error = any(indicator in result_text for indicator in error_indicators)

            return has_success and not has_error

        except Exception:
            return False

    async def _validate_prospects_batch(self, prospects: List[ProspectData]) -> List[ProspectData]:
        """Validate a batch of prospects"""
        validated = []

        for prospect in prospects:
            try:
                # Basic validation is handled by Pydantic model
                # Additional business logic validation here
                if self._is_valid_prospect(prospect):
                    validated.append(prospect)
                else:
                    logger.warning(f"Invalid prospect data: {prospect.name}")
            except Exception as e:
                logger.error(f"Error validating prospect {prospect.name}: {str(e)}")

        return validated

    def _is_valid_prospect(self, prospect: ProspectData) -> bool:
        """Validate individual prospect data"""
        # Check required fields
        if not all([prospect.name, prospect.email, prospect.phone]):
            return False

        # Validate email format
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, prospect.email):
            return False

        # Validate phone format
        phone_digits = re.sub(r'\D', '', prospect.phone)
        if len(phone_digits) < 10 or len(phone_digits) > 15:
            return False

        return True

    async def _dedupe_prospects(self, prospects: List[ProspectData]) -> List[ProspectData]:
        """Deduplicate prospects against Zoho CRM and internal duplicates"""
        try:
            # Use MCP client for Zoho deduplication
            dedupe_result = await self.mcp_client.dedupe_prospects([p.dict() for p in prospects])

            unique_prospects = []
            for prospect_data in dedupe_result.get("unique_prospects", []):
                try:
                    unique_prospects.append(ProspectData(**prospect_data))
                except Exception as e:
                    logger.error(f"Error reconstructing prospect data: {str(e)}")

            logger.info(f"Deduplication: {len(prospects)} input, {len(unique_prospects)} unique")
            return unique_prospects

        except Exception as e:
            logger.error(f"Error in deduplication: {str(e)}")
            # Fallback to basic email deduplication
            seen_emails = set()
            unique_prospects = []
            for prospect in prospects:
                if prospect.email not in seen_emails:
                    seen_emails.add(prospect.email)
                    unique_prospects.append(prospect)
            return unique_prospects

    def _update_execution_status(self, execution_id: str, step: str, progress: Optional[int]):
        """Update execution status in cache"""
        if execution_id in self.execution_cache:
            self.execution_cache[execution_id]["current_step"] = step
            if progress is not None:
                self.execution_cache[execution_id]["progress"] = int(progress)
            self.execution_cache[execution_id]["updated_at"] = datetime.utcnow().isoformat()

    async def _generate_execution_report(self, execution_id: str, results: Dict[str, Any]):
        """Generate execution report and save to database"""
        try:
            # In production, save to database
            report = {
                "execution_id": execution_id,
                "total_prospects": len(results["prospect_results"]),
                "successful_contacts": results["successful_contacts"],
                "failed_contacts": results["failed_contacts"],
                "success_rate": (results["successful_contacts"] / len(results["prospect_results"])) * 100 if results["prospect_results"] else 0,
                "generated_at": datetime.utcnow().isoformat()
            }

            logger.info(f"Generated report for execution {execution_id}: {report}")

        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")

    async def get_flow_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """Get current execution status"""
        return self.execution_cache.get(execution_id, {
            "status": "not_found",
            "error": "Execution ID not found"
        })

    async def send_sms_outreach(
        self,
        recipient: str,
        message: str,
        prospect_data: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Send SMS outreach via SalesMsg API"""
        try:
            outreach_id = str(uuid.uuid4())

            # In production, integrate with actual SalesMsg API
            sms_result = {
                "outreach_id": outreach_id,
                "status": "sent",
                "recipient": recipient,
                "message": message,
                "sent_at": datetime.utcnow().isoformat(),
                "delivery_status": "pending"
            }

            # Store outreach record
            self.outreach_cache[outreach_id] = {
                **sms_result,
                "channel": "sms",
                "prospect_data": prospect_data,
                "user_id": user_id
            }

            logger.info(f"SMS sent to {recipient}: {outreach_id}")
            return sms_result

        except Exception as e:
            logger.error(f"Error sending SMS: {str(e)}")
            raise

    async def send_email_outreach(
        self,
        recipient: str,
        subject: str,
        message: str,
        prospect_data: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Send email outreach via Gmail API"""
        try:
            outreach_id = str(uuid.uuid4())

            # In production, integrate with actual Gmail API
            email_result = {
                "outreach_id": outreach_id,
                "status": "sent",
                "recipient": recipient,
                "subject": subject,
                "message": message,
                "sent_at": datetime.utcnow().isoformat(),
                "delivery_status": "pending"
            }

            # Store outreach record
            self.outreach_cache[outreach_id] = {
                **email_result,
                "channel": "email",
                "prospect_data": prospect_data,
                "user_id": user_id
            }

            logger.info(f"Email sent to {recipient}: {outreach_id}")
            return email_result

        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            raise

    async def schedule_meeting(
        self,
        recipient: str,
        meeting_data: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Schedule meeting via Zoho Calendar"""
        try:
            outreach_id = str(uuid.uuid4())

            # In production, integrate with actual Zoho Calendar API
            meeting_result = {
                "outreach_id": outreach_id,
                "status": "scheduled",
                "recipient": recipient,
                "meeting_data": meeting_data,
                "scheduled_at": datetime.utcnow().isoformat(),
                "meeting_time": meeting_data.get("meeting_time")
            }

            # Store outreach record
            self.outreach_cache[outreach_id] = {
                **meeting_result,
                "channel": "calendar",
                "prospect_data": meeting_data,
                "user_id": user_id
            }

            logger.info(f"Meeting scheduled with {recipient}: {outreach_id}")
            return meeting_result

        except Exception as e:
            logger.error(f"Error scheduling meeting: {str(e)}")
            raise

    def validate_prospect_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate prospects from DataFrame"""
        valid_prospects = []
        invalid_prospects = []
        errors = []

        for index, row in df.iterrows():
            try:
                # Convert row to prospect data
                prospect_data = {
                    "name": row.get("name", ""),
                    "email": row.get("email", ""),
                    "phone": str(row.get("phone", "")),
                    "company": row.get("company", ""),
                    "license_number": row.get("license_number", ""),
                    "license_type": row.get("license_type", "Sales Associate")
                }

                # Validate using Pydantic model
                prospect = ProspectData(**prospect_data)
                valid_prospects.append(prospect.dict())

            except Exception as e:
                invalid_prospects.append(row.to_dict())
                errors.append(f"Row {index + 1}: {str(e)}")

        return {
            "valid_prospects": valid_prospects,
            "invalid_prospects": invalid_prospects,
            "errors": errors
        }

    def parse_text_prospects(self, text_content: str) -> List[Dict[str, Any]]:
        """Parse prospects from plain text"""
        prospects = []
        lines = text_content.strip().split('\n')

        for line in lines:
            if not line.strip():
                continue

            try:
                # Try to extract email and phone from line
                email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', line)
                phone_match = re.search(r'[\+]?[1]?[-.]?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})', line)

                if email_match:
                    email = email_match.group()
                    # Extract name (text before email)
                    name_part = line[:email_match.start()].strip().split(',')[0]
                    name = name_part if name_part else "Unknown"

                    prospect = {
                        "name": name,
                        "email": email,
                        "phone": phone_match.group() if phone_match else "",
                        "company": "",
                        "license_number": "",
                        "license_type": "Sales Associate"
                    }
                    prospects.append(prospect)

            except Exception as e:
                logger.warning(f"Could not parse line: {line} - {str(e)}")

        return prospects

    def validate_single_prospect(self, prospect_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate single prospect data"""
        try:
            prospect = ProspectData(**prospect_data)
            return {
                "is_valid": True,
                "validated_prospect": prospect.dict(),
                "errors": [],
                "suggestions": []
            }
        except Exception as e:
            return {
                "is_valid": False,
                "validated_prospect": None,
                "errors": [str(e)],
                "suggestions": self._generate_validation_suggestions(prospect_data, str(e))
            }

    def _generate_validation_suggestions(self, prospect_data: Dict[str, Any], error: str) -> List[str]:
        """Generate validation suggestions based on error"""
        suggestions = []

        if "email" in error.lower():
            suggestions.append("Please provide a valid email address (e.g., john@example.com)")

        if "phone" in error.lower():
            suggestions.append("Please provide a valid phone number (10-15 digits)")

        if "name" in error.lower():
            suggestions.append("Please provide a full name")

        return suggestions

    async def get_flow_history(self, user_id: str, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """Get flow execution history for user"""
        # In production, query from database
        # For now, return mock data
        executions = []
        for execution_id, execution_data in self.execution_cache.items():
            if execution_data.get("user_id") == user_id:
                executions.append({
                    "execution_id": execution_id,
                    **execution_data
                })

        return {
            "executions": executions[(page-1)*per_page:page*per_page],
            "total_count": len(executions)
        }

    async def retry_flow_execution(self, execution_id: str) -> Dict[str, Any]:
        """Retry failed flow execution"""
        execution_data = self.execution_cache.get(execution_id)

        if not execution_data:
            raise ValueError("Execution not found")

        if execution_data["status"] not in ["failed", "completed"]:
            raise ValueError("Can only retry failed or completed executions")

        # Create new execution for retry
        new_execution_id = f"{execution_id}_retry_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        # In production, implement actual retry logic
        self.execution_cache[new_execution_id] = {
            "status": "queued_for_retry",
            "original_execution_id": execution_id,
            "created_at": datetime.utcnow().isoformat()
        }

        return {
            "new_execution_id": new_execution_id,
            "status": "retry_queued"
        }

    async def get_prospect_outreach_status(self, prospect_id: str) -> Dict[str, Any]:
        """Get outreach status for specific prospect"""
        outreach_history = []

        for outreach_id, outreach_data in self.outreach_cache.items():
            prospect_email = outreach_data.get("prospect_data", {}).get("email")
            if prospect_email == prospect_id:
                outreach_history.append(outreach_data)

        # Sort by sent time
        outreach_history.sort(key=lambda x: x.get("sent_at", ""), reverse=True)

        last_contact = outreach_history[0] if outreach_history else None

        return {
            "outreach_history": outreach_history,
            "last_contact": last_contact.get("sent_at") if last_contact else None,
            "response_status": "pending",  # In production, track actual responses
            "next_follow_up": self._calculate_next_follow_up(last_contact)
        }

    def _calculate_next_follow_up(self, last_contact: Optional[Dict[str, Any]]) -> Optional[str]:
        """Calculate next follow-up date based on last contact"""
        if not last_contact:
            return None

        try:
            last_contact_date = datetime.fromisoformat(last_contact["sent_at"].replace("Z", "+00:00"))
            next_follow_up = last_contact_date + timedelta(days=3)  # Follow up in 3 days
            return next_follow_up.isoformat()
        except Exception:
            return None

    async def export_recruiting_data(
        self,
        user_id: str,
        format: str = "csv",
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> pd.DataFrame:
        """Export recruiting data for user"""
        # In production, query from database
        data = []

        for execution_id, execution_data in self.execution_cache.items():
            if execution_data.get("user_id") == user_id:
                results = execution_data.get("results", {})
                for prospect_result in results.get("prospect_results", []):
                    data.append({
                        "execution_id": execution_id,
                        "prospect_name": prospect_result.get("prospect", {}).get("name"),
                        "prospect_email": prospect_result.get("prospect", {}).get("email"),
                        "success": prospect_result.get("success"),
                        "processed_at": prospect_result.get("processed_at"),
                        **execution_data
                    })

        df = pd.DataFrame(data)

        # Apply date filters if provided
        if date_from or date_to:
            if "processed_at" in df.columns:
                df["processed_at"] = pd.to_datetime(df["processed_at"])
                if date_from:
                    df = df[df["processed_at"] >= pd.to_datetime(date_from)]
                if date_to:
                    df = df[df["processed_at"] <= pd.to_datetime(date_to)]

        return df

    async def get_recruiting_analytics(
        self,
        user_id: str,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get recruiting analytics for user"""
        # In production, query from database with proper aggregations
        total_prospects = 0
        successful_contacts = 0

        channel_stats = {"sms": 0, "email": 0, "calendar": 0}

        for outreach_id, outreach_data in self.outreach_cache.items():
            if outreach_data.get("user_id") == user_id:
                total_prospects += 1
                if outreach_data.get("status") == "sent":
                    successful_contacts += 1

                channel = outreach_data.get("channel", "unknown")
                channel_stats[channel] = channel_stats.get(channel, 0) + 1

        response_rate = (successful_contacts / total_prospects * 100) if total_prospects > 0 else 0

        return {
            "total_prospects": total_prospects,
            "successful_contacts": successful_contacts,
            "response_rate": response_rate,
            "conversion_rate": 0.0,  # In production, track actual conversions
            "channel_performance": [
                {
                    "channel": channel,
                    "total_sent": count,
                    "responses": 0,  # In production, track responses
                    "response_rate": 0.0,
                    "conversions": 0,
                    "conversion_rate": 0.0
                }
                for channel, count in channel_stats.items()
                if count > 0
            ],
            "daily_metrics": [],  # In production, aggregate by day
            "top_messages": []    # In production, track message performance
        }