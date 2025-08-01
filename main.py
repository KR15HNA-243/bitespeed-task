from fastapi import FastAPI, HTTPException
from datetime import datetime
from db_setup import init_db, get_db_connection
from db_models import IdentifyRequest, FinalResponse, ContactResponse, AddContactRequest

init_db()

app = FastAPI(
    title="Bitespeed Contact Reconciliation API", 
    version="1.0.0"
)



def find_contacts(email: str = None, phone: str = None):
    query = """
        SELECT * FROM Contact 
        WHERE deletedAt IS NULL 
        AND (email = ? OR phoneNumber = ?)
        ORDER BY createdAt ASC
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, (email, phone))
    contacts = cursor.fetchall()

    conn.close()

    return [dict(contact) for contact in contacts]

def get_all_linked_contacts(primary_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM Contact WHERE id = ? AND deletedAt IS NULL", (primary_id,))
    primary = cursor.fetchone()
    
    if not primary:
        conn.close()
        return []
    
    cursor.execute("""
        SELECT * FROM Contact 
        WHERE linkedId = ? AND deletedAt IS NULL 
        ORDER BY createdAt ASC
    """, (primary_id,))
    
    secondaries = cursor.fetchall()
    conn.close()
    
    contacts = [dict(primary)] + [dict(contact) for contact in secondaries]
    return contacts

def create_contact(email: str = None, phone: str = None, linked_id: int = None, precedence: str = "primary", contact_id: int = None):
    """Create a new contact"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    if contact_id:
        cursor.execute("""
            INSERT INTO Contact (id, phoneNumber, email, linkedId, linkPrecedence, createdAt, updatedAt)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (contact_id, phone, email, linked_id, precedence, now, now))
        result_id = contact_id
    else:
        cursor.execute("""
            INSERT INTO Contact (phoneNumber, email, linkedId, linkPrecedence, createdAt, updatedAt)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (phone, email, linked_id, precedence, now, now))
        result_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    
    return result_id

def update_to_secondary(contact_id: int, primary_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    cursor.execute("""
        UPDATE Contact 
        SET linkedId = ?, linkPrecedence = 'secondary', updatedAt = ?
        WHERE id = ?
    """, (primary_id, now, contact_id))
    
    conn.commit()
    conn.close()


@app.get("/")
async def root():
    return {"message": "Bitespeed API is up"}



@app.post("/identify", response_model=FinalResponse)
async def identify(request: IdentifyRequest):

    email = request.email
    phone = request.phoneNumber
    
    if not email and not phone:
        raise HTTPException(status_code=400, detail="Either email or phoneNumber must be provided")
    
    existing_contacts = find_contacts(email, phone)
    
    if not existing_contacts:
        
        contact_id = create_contact(email, phone, None, "primary")
        
        return FinalResponse(
            contact=ContactResponse(
                primaryContactId=contact_id,
                emails=[email] if email else [],
                phoneNumbers=[phone] if phone else [],
                secondaryContactIds=[]
            )
        )
    
    
    primary_contacts = []
    secondary_contacts = []
    
    for contact in existing_contacts:
        if contact['linkPrecedence'] == 'primary':
            primary_contacts.append(contact)
        else:
            secondary_contacts.append(contact)
    
    
    if primary_contacts:
        primary_contacts.sort(key=lambda x: x['createdAt'])
        primary_contact = primary_contacts[0]
        primary_id = primary_contact['id']

        for contact in primary_contacts[1:]:
            update_to_secondary(contact['id'], primary_id)
            
            
        for contact in primary_contacts[1:]:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE Contact SET linkedId = ? WHERE linkedId = ?", (primary_id, contact['id']))
            conn.commit()
            conn.close()

        
    else:
        primary_id = secondary_contacts[0]['linkedId']
        primary_contact_query = get_all_linked_contacts(primary_id)
        primary_contact = next(c for c in primary_contact_query if c['linkPrecedence'] == 'primary')

    needs_new_contact = False
    
    if email and phone:
        exact_match = any(c['email'] == email and c['phoneNumber'] == phone for c in existing_contacts)

        email_exists = any(c['email'] == email for c in existing_contacts)
        phone_exists = any(c['phoneNumber'] == phone for c in existing_contacts)
        
        if not exact_match and not (email_exists and phone_exists):
            needs_new_contact = True
    elif email:
        email_match = any(c['email'] == email for c in existing_contacts)
        if not email_match:
            needs_new_contact = True
    elif phone:
        phone_match = any(c['phoneNumber'] == phone for c in existing_contacts)
        if not phone_match:
            needs_new_contact = True
    
    if needs_new_contact:
        create_contact(email, phone, primary_id, "secondary")
    
    all_contacts = get_all_linked_contacts(primary_id)
    
    emails = []
    phone_numbers = []
    secondary_ids = []
    
    all_contacts.sort(key=lambda x: x['createdAt'])
    
    for contact in all_contacts:
        if contact['email'] and contact['email'] not in emails:
            emails.append(contact['email'])
        if contact['phoneNumber'] and contact['phoneNumber'] not in phone_numbers:
            phone_numbers.append(contact['phoneNumber'])
        if contact['linkPrecedence'] == 'secondary':
            secondary_ids.append(contact['id'])
    
    return FinalResponse(
        contact=ContactResponse(
            primaryContactId=primary_id,
            emails=emails,
            phoneNumbers=phone_numbers,
            secondaryContactIds=secondary_ids
        )
    )

@app.post("/add-contact")
async def add_contact(request: AddContactRequest):
    """Add a new contact to the database with all fields"""
    contact_id = create_contact(
        email=request.email,
        phone=request.phoneNumber,
        linked_id=request.linkedId,
        precedence=request.linkPrecedence,
        contact_id=request.id
    )
    return {"message": "Contact added successfully", "contact_id": contact_id}


@app.delete("/contact/{contact_id}")
async def delete_contact(contact_id: int):
    """Delete a contact by setting deletedAt timestamp"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM Contact WHERE id = ? AND deletedAt IS NULL", (contact_id,))
    contact = cursor.fetchone()
    
    if not contact:
        conn.close()
        raise HTTPException(status_code=404, detail="Contact not found")
    
    now = datetime.now().isoformat()
    cursor.execute("UPDATE Contact SET deletedAt = ? WHERE id = ?", (now, contact_id))
    
    conn.commit()
    conn.close()
    
    return {"message": f"Contact {contact_id} deleted successfully"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)