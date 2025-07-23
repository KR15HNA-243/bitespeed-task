from pydantic import BaseModel
from typing import Optional, List



class IdentifyRequest(BaseModel):
    email: Optional[str] = None
    phoneNumber: Optional[str] = None

class ContactResponse(BaseModel):
    primaryContactId: int  
    emails: List[str]
    phoneNumbers: List[str]
    secondaryContactIds: List[int]

class FinalResponse(BaseModel):
    contact: ContactResponse

class AddContactRequest(BaseModel):
    id: Optional[int] = None
    email: Optional[str] = None
    phoneNumber: Optional[str] = None
    linkedId: Optional[int] = None
    linkPrecedence: Optional[str] = "primary"

