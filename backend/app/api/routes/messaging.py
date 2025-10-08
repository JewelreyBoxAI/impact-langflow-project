from fastapi import APIRouter, HTTPException
from pydantic import BaseModel  
from ...integrations.salesmsg import SalesmsgClient

router = APIRouter()

# 2. Define a Pydantic model for the request body
class SMSRequest(BaseModel):
    phone_number: str
    message: str

# 3. Update the endpoint to use the Pydantic model
@router.post("/send-sms/")
async def send_sms_endpoint(request: SMSRequest): 
    """
    API endpoint to send an SMS message via the Salesmsg service.
    """
    try:
        salesmsg_client = SalesmsgClient()
        # Use the data from the request model
        result = await salesmsg_client.send_sms(
            phone_number=request.phone_number, 
            message=request.message
        )
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))