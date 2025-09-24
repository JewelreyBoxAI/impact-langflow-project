"""
CRM API Routes
Zoho CRM integration endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from typing import Optional
import logging

from ...services.zoho_service import ZohoService
from ...schemas.crm_schemas import (
    CRMSearchRequest, CRMSearchResponse, CRMUpsertRequest, CRMUpsertResponse,
    CRMRecordUpdateRequest, LeadConvertRequest, ActivityCreateRequest, BulkReadRequest,
    NotesCreateRequest, NotesCreateResponse, TasksCreateRequest, TasksCreateResponse,
    BlueprintTransitionRequest, BlueprintTransitionResponse,
    FilesAttachRequest, FilesAttachResponse,
    StandardResponse, RecordResponse, MetadataResponse
)
from ...api.dependencies import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


def get_zoho_service():
    """Dependency to get Zoho service instance"""
    return ZohoService()


@router.post("/search", response_model=CRMSearchResponse)
async def search_crm_records(
    request: CRMSearchRequest,
    current_user: dict = Depends(get_current_user),
    zoho_service: ZohoService = Depends(get_zoho_service)
):
    """Search CRM records by criteria"""
    try:
        logger.info(f"Searching CRM module {request.module} with criteria: {request.criteria}")

        records = await zoho_service.search_crm_records(
            module=request.module,
            criteria=request.criteria,
            fields=request.fields,
            page=request.page,
            per_page=request.per_page
        )

        return CRMSearchResponse(
            module=request.module,
            records=records.get("data", []),
            total_count=records.get("info", {}).get("count", 0),
            page=request.page,
            per_page=request.per_page
        )

    except Exception as e:
        logger.error(f"Error searching CRM {request.module}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upsert", response_model=CRMUpsertResponse)
async def upsert_crm_record(
    request: CRMUpsertRequest,
    current_user: dict = Depends(get_current_user),
    zoho_service: ZohoService = Depends(get_zoho_service)
):
    """Create or update CRM record"""
    try:
        logger.info(f"Upserting CRM record in module {request.module}")

        result = await zoho_service.upsert_crm_record(
            module=request.module,
            record_data=request.record_data,
            duplicate_check_fields=request.duplicate_check_fields
        )

        return CRMUpsertResponse(
            module=request.module,
            record_id=result.get("data", [{}])[0].get("details", {}).get("id"),
            operation=result.get("data", [{}])[0].get("code", "unknown"),
            details=result
        )

    except Exception as e:
        logger.error(f"Error upserting CRM record: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{module}/{record_id}", response_model=StandardResponse)
async def get_crm_record(
    module: str,
    record_id: str,
    fields: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    zoho_service: ZohoService = Depends(get_zoho_service)
):
    """Get specific CRM record by ID"""
    try:
        field_list = fields.split(",") if fields else None
        record = await zoho_service.get_crm_record(module, record_id, field_list)

        return StandardResponse(
            success=True,
            data=record,
            message=f"Retrieved {module} record {record_id}"
        )
    except Exception as e:
        logger.error(f"Error getting {module} record {record_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{module}", response_model=StandardResponse)
async def list_crm_records(
    module: str,
    fields: Optional[str] = None,
    page: int = 1,
    per_page: int = 200,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
    current_user: dict = Depends(get_current_user),
    zoho_service: ZohoService = Depends(get_zoho_service)
):
    """List CRM records with pagination"""
    try:
        field_list = fields.split(",") if fields else None
        records = await zoho_service.get_crm_records(
            module, field_list, page, per_page, sort_by, sort_order
        )

        return StandardResponse(
            success=True,
            data=records,
            message=f"Retrieved {module} records"
        )
    except Exception as e:
        logger.error(f"Error listing {module} records: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{module}/{record_id}", response_model=RecordResponse)
async def update_crm_record(
    module: str,
    record_id: str,
    request: CRMRecordUpdateRequest,
    current_user: dict = Depends(get_current_user),
    zoho_service: ZohoService = Depends(get_zoho_service)
):
    """Update existing CRM record"""
    try:
        result = await zoho_service.update_crm_record(module, record_id, request.record_data)

        return RecordResponse(
            record_id=record_id,
            module=module,
            operation="update",
            details=result
        )
    except Exception as e:
        logger.error(f"Error updating {module} record {record_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{module}/{record_id}", response_model=StandardResponse)
async def delete_crm_record(
    module: str,
    record_id: str,
    current_user: dict = Depends(get_current_user),
    zoho_service: ZohoService = Depends(get_zoho_service)
):
    """Delete CRM record"""
    try:
        result = await zoho_service.delete_crm_record(module, record_id)

        return StandardResponse(
            success=True,
            data=result,
            message=f"Deleted {module} record {record_id}"
        )
    except Exception as e:
        logger.error(f"Error deleting {module} record {record_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notes/create", response_model=NotesCreateResponse)
async def create_crm_note(
    request: NotesCreateRequest,
    current_user: dict = Depends(get_current_user),
    zoho_service: ZohoService = Depends(get_zoho_service)
):
    """Create a note in CRM"""
    try:
        logger.info(f"Creating note for record {request.record_id} in module {request.module}")

        result = await zoho_service.create_crm_note(
            module=request.module,
            record_id=request.record_id,
            note_title=request.note_title,
            note_content=request.note_content
        )

        return NotesCreateResponse(
            note_id=result.get("data", [{}])[0].get("details", {}).get("id"),
            record_id=request.record_id,
            module=request.module
        )

    except Exception as e:
        logger.error(f"Error creating CRM note: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/create", response_model=TasksCreateResponse)
async def create_crm_task(
    request: TasksCreateRequest,
    current_user: dict = Depends(get_current_user),
    zoho_service: ZohoService = Depends(get_zoho_service)
):
    """Create a task in CRM"""
    try:
        logger.info(f"Creating task for record {request.related_record_id}")

        result = await zoho_service.create_crm_task(
            task_data=request.task_data,
            related_module=request.related_module,
            related_record_id=request.related_record_id
        )

        return TasksCreateResponse(
            task_id=result.get("data", [{}])[0].get("details", {}).get("id"),
            related_record_id=request.related_record_id,
            related_module=request.related_module
        )

    except Exception as e:
        logger.error(f"Error creating CRM task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/activities/create", response_model=RecordResponse)
async def create_activity(
    request: ActivityCreateRequest,
    current_user: dict = Depends(get_current_user),
    zoho_service: ZohoService = Depends(get_zoho_service)
):
    """Create activity (call, event, task) in CRM"""
    try:
        result = await zoho_service.create_activity(
            request.activity_type,
            request.activity_data,
            request.related_module,
            request.related_record_id
        )

        return RecordResponse(
            record_id=result.get("data", [{}])[0].get("details", {}).get("id"),
            module=request.activity_type,
            operation="create",
            details=result
        )
    except Exception as e:
        logger.error(f"Error creating activity: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/leads/{lead_id}/convert", response_model=StandardResponse)
async def convert_lead(
    lead_id: str,
    request: LeadConvertRequest,
    current_user: dict = Depends(get_current_user),
    zoho_service: ZohoService = Depends(get_zoho_service)
):
    """Convert lead to contact/account/deal"""
    try:
        result = await zoho_service.convert_lead(lead_id, request.convert_data)

        return StandardResponse(
            success=True,
            data=result,
            message=f"Converted lead {lead_id}"
        )
    except Exception as e:
        logger.error(f"Error converting lead {lead_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{module}/{record_id}/{related_module}", response_model=StandardResponse)
async def get_related_records(
    module: str,
    record_id: str,
    related_module: str,
    fields: Optional[str] = None,
    page: int = 1,
    per_page: int = 200,
    current_user: dict = Depends(get_current_user),
    zoho_service: ZohoService = Depends(get_zoho_service)
):
    """Get related records for a specific record"""
    try:
        field_list = fields.split(",") if fields else None
        records = await zoho_service.get_related_records(
            module, record_id, related_module, field_list, page, per_page
        )

        return StandardResponse(
            success=True,
            data=records,
            message=f"Retrieved {related_module} related to {module} {record_id}"
        )
    except Exception as e:
        logger.error(f"Error getting related records: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{module}/bulk_read", response_model=StandardResponse)
async def bulk_read_records(
    module: str,
    request: BulkReadRequest,
    current_user: dict = Depends(get_current_user),
    zoho_service: ZohoService = Depends(get_zoho_service)
):
    """Bulk read multiple records by IDs"""
    try:
        result = await zoho_service.bulk_read(module, request.record_ids, request.fields)

        return StandardResponse(
            success=True,
            data=result,
            message=f"Bulk read {len(request.record_ids)} {module} records"
        )
    except Exception as e:
        logger.error(f"Error bulk reading {module} records: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metadata/fields/{module}", response_model=MetadataResponse)
async def get_field_metadata(
    module: str,
    current_user: dict = Depends(get_current_user),
    zoho_service: ZohoService = Depends(get_zoho_service)
):
    """Get field metadata for a module"""
    try:
        metadata = await zoho_service.get_field_metadata(module)

        return MetadataResponse(
            module=module,
            metadata=metadata
        )
    except Exception as e:
        logger.error(f"Error getting field metadata for {module}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metadata/modules/{module}", response_model=MetadataResponse)
async def get_module_metadata(
    module: str,
    current_user: dict = Depends(get_current_user),
    zoho_service: ZohoService = Depends(get_zoho_service)
):
    """Get metadata for a specific module"""
    try:
        metadata = await zoho_service.get_module_metadata(module)

        return MetadataResponse(
            module=module,
            metadata=metadata
        )
    except Exception as e:
        logger.error(f"Error getting module metadata for {module}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/blueprint/transition", response_model=BlueprintTransitionResponse)
async def transition_blueprint(
    request: BlueprintTransitionRequest,
    current_user: dict = Depends(get_current_user),
    zoho_service: ZohoService = Depends(get_zoho_service)
):
    """Execute blueprint transition in CRM"""
    try:
        logger.info(f"Transitioning blueprint for record {request.record_id}")

        result = await zoho_service.transition_blueprint(
            module=request.module,
            record_id=request.record_id,
            transition_id=request.transition_id,
            data=request.data
        )

        return BlueprintTransitionResponse(
            record_id=request.record_id,
            transition_id=request.transition_id,
            status="completed",
            result=result
        )

    except Exception as e:
        logger.error(f"Error transitioning blueprint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/files/attach", response_model=FilesAttachResponse)
async def attach_file(
    request: FilesAttachRequest,
    current_user: dict = Depends(get_current_user),
    zoho_service: ZohoService = Depends(get_zoho_service)
):
    """Attach file to CRM record"""
    try:
        logger.info(f"Attaching file to record {request.record_id}")

        result = await zoho_service.attach_file(
            module=request.module,
            record_id=request.record_id,
            file_path=request.file_path,
            file_name=request.file_name
        )

        return FilesAttachResponse(
            file_id=result.get("data", [{}])[0].get("details", {}).get("id"),
            record_id=request.record_id,
            file_name=request.file_name
        )

    except Exception as e:
        logger.error(f"Error attaching file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))