"""
Zoho CRM Service
Business logic for Zoho CRM operations
"""

from typing import Dict, Any, List, Optional
import logging

from ..integrations.zoho.client import ZohoClient

logger = logging.getLogger(__name__)


class ZohoService:
    """Service class for Zoho CRM business operations"""

    def __init__(self):
        self.client = ZohoClient()

    @property
    def client_id(self) -> str:
        """Get Zoho client ID"""
        return self.client.client_id

    @property
    def client_secret(self) -> str:
        """Get Zoho client secret (masked)"""
        return bool(self.client.client_secret)

    @property
    def refresh_token(self) -> str:
        """Get refresh token status"""
        return bool(self.client.refresh_token)

    async def search_crm_records(
        self,
        module: str,
        criteria: str,
        fields: Optional[List[str]] = None,
        page: int = 1,
        per_page: int = 200
    ) -> Dict[str, Any]:
        """Search CRM records with business logic validation"""
        # Validate module name
        valid_modules = ['Leads', 'Contacts', 'Accounts', 'Deals', 'Tasks', 'Events', 'Calls']
        if module not in valid_modules:
            raise ValueError(f"Invalid module: {module}. Must be one of {valid_modules}")

        # Validate pagination
        if per_page > 200:
            per_page = 200
            logger.warning(f"per_page capped at 200 for performance")

        return await self.client.search_crm_records(module, criteria, fields, page, per_page)

    async def upsert_crm_record(
        self,
        module: str,
        record_data: Dict[str, Any],
        duplicate_check_fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Upsert CRM record with business validation"""
        # Add audit fields
        record_data['Modified_By'] = 'Impact AI Platform'

        return await self.client.upsert_crm_record(module, record_data, duplicate_check_fields)

    async def get_crm_record(
        self,
        module: str,
        record_id: str,
        fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get single CRM record"""
        return await self.client.get_crm_record(module, record_id, fields)

    async def get_crm_records(
        self,
        module: str,
        fields: Optional[List[str]] = None,
        page: int = 1,
        per_page: int = 200,
        sort_by: Optional[str] = None,
        sort_order: str = "asc"
    ) -> Dict[str, Any]:
        """Get multiple CRM records with pagination"""
        return await self.client.get_crm_records(module, fields, page, per_page, sort_by, sort_order)

    async def update_crm_record(
        self,
        module: str,
        record_id: str,
        record_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update existing CRM record"""
        # Add audit fields
        record_data['Modified_By'] = 'Impact AI Platform'

        return await self.client.update_crm_record(module, record_id, record_data)

    async def delete_crm_record(self, module: str, record_id: str) -> Dict[str, Any]:
        """Delete CRM record"""
        return await self.client.delete_crm_record(module, record_id)

    async def create_crm_note(
        self,
        module: str,
        record_id: str,
        note_title: str,
        note_content: str
    ) -> Dict[str, Any]:
        """Create CRM note with business context"""
        return await self.client.create_crm_note(module, record_id, note_title, note_content)

    async def create_crm_task(
        self,
        task_data: Dict[str, Any],
        related_module: str,
        related_record_id: str
    ) -> Dict[str, Any]:
        """Create CRM task with business validation"""
        # Add default task properties for Impact Realty
        task_data['Owner'] = task_data.get('Owner', 'Impact AI System')
        task_data['Status'] = task_data.get('Status', 'Not Started')

        return await self.client.create_crm_task(task_data, related_module, related_record_id)

    async def create_activity(
        self,
        activity_type: str,
        activity_data: Dict[str, Any],
        related_module: str,
        related_record_id: str
    ) -> Dict[str, Any]:
        """Create CRM activity (call, event, task)"""
        return await self.client.create_activity(
            activity_type, activity_data, related_module, related_record_id
        )

    async def convert_lead(self, lead_id: str, convert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert lead to contact/account/deal"""
        return await self.client.convert_lead(lead_id, convert_data)

    async def get_related_records(
        self,
        module: str,
        record_id: str,
        related_module: str,
        fields: Optional[List[str]] = None,
        page: int = 1,
        per_page: int = 200
    ) -> Dict[str, Any]:
        """Get related records for a specific record"""
        return await self.client.get_related_records(
            module, record_id, related_module, fields, page, per_page
        )

    async def bulk_read(
        self,
        module: str,
        record_ids: List[str],
        fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Bulk read multiple records by IDs"""
        return await self.client.bulk_read(module, record_ids, fields)

    async def get_field_metadata(self, module: str) -> Dict[str, Any]:
        """Get field metadata for a module"""
        return await self.client.get_field_metadata(module)

    async def get_module_metadata(self, module: str) -> Dict[str, Any]:
        """Get metadata for a specific module"""
        return await self.client.get_module_metadata(module)

    async def transition_blueprint(
        self,
        module: str,
        record_id: str,
        transition_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute blueprint transition in CRM"""
        return await self.client.transition_blueprint(module, record_id, transition_id, data)

    async def attach_file(
        self,
        module: str,
        record_id: str,
        file_path: str,
        file_name: str
    ) -> Dict[str, Any]:
        """Attach file to CRM record"""
        return await self.client.attach_file(module, record_id, file_path, file_name)

    # Real Estate specific methods
    async def search_properties(
        self,
        criteria: str,
        fields: Optional[List[str]] = None,
        page: int = 1,
        per_page: int = 200
    ) -> Dict[str, Any]:
        """Search properties - business logic wrapper"""
        return await self.search_crm_records('Properties', criteria, fields, page, per_page)

    async def search_agents(
        self,
        criteria: str,
        fields: Optional[List[str]] = None,
        page: int = 1,
        per_page: int = 200
    ) -> Dict[str, Any]:
        """Search real estate agents"""
        return await self.search_crm_records('Agents', criteria, fields, page, per_page)

    async def create_commission_record(
        self,
        agent_id: str,
        deal_id: str,
        commission_amount: float,
        commission_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create commission record for agent"""
        # Add required fields for commission tracking
        commission_data.update({
            'Agent': agent_id,
            'Deal': deal_id,
            'Commission_Amount': commission_amount,
            'Status': 'Pending',
            'Created_By': 'Impact AI Platform'
        })

        return await self.upsert_crm_record('Commissions', commission_data)

    # Webhook and email methods
    async def create_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create webhook in Zoho CRM"""
        return await self.client.create_webhook(webhook_data)

    async def send_email(
        self,
        template_id: str,
        recipient_emails: List[str],
        merge_data: Dict[str, Any],
        related_record_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send email using Zoho CRM templates"""
        return await self.client.send_email(
            template_id, recipient_emails, merge_data, related_record_id
        )