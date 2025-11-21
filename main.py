import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Service as ServiceSchema, Barber as BarberSchema, Appointment as AppointmentSchema

app = FastAPI(title="Barber Shop API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Helpers
# -----------------------------

def serialize_doc(doc: dict):
    if not doc:
        return doc
    d = doc.copy()
    if "_id" in d:
        d["id"] = str(d.pop("_id"))
    # Convert nested ObjectIds if any
    for k, v in list(d.items()):
        if isinstance(v, ObjectId):
            d[k] = str(v)
    return d

# -----------------------------
# Root and health
# -----------------------------

@app.get("/")
def read_root():
    return {"message": "Barber Shop API is running"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

# -----------------------------
# Seed data on startup
# -----------------------------

@app.on_event("startup")
async def seed_defaults():
    if db is None:
        return
    # Seed services if empty
    if db.service.count_documents({}) == 0:
        defaults = [
            {"name": "Haircut", "duration_minutes": 30, "price": 25.0, "description": "Classic cut and style"},
            {"name": "Beard Trim", "duration_minutes": 20, "price": 15.0, "description": "Shape and trim"},
            {"name": "Haircut + Beard", "duration_minutes": 50, "price": 35.0, "description": "Complete grooming"},
            {"name": "Buzz Cut", "duration_minutes": 20, "price": 18.0, "description": "Clean buzz all around"},
        ]
        for s in defaults:
            create_document("service", ServiceSchema(**s))
    # Seed barbers if empty
    if db.barber.count_documents({}) == 0:
        barbers = [
            {"name": "Alex", "specialties": ["Fade", "Beard"], "bio": "Detail-oriented with 7 years experience."},
            {"name": "Jamie", "specialties": ["Classic", "Scissor Cut"], "bio": "Loves classic looks and great chats."},
            {"name": "Riley", "specialties": ["Buzz", "Kids"], "bio": "Fast and friendly."},
        ]
        for b in barbers:
            create_document("barber", BarberSchema(**b))

# -----------------------------
# Response models
# -----------------------------

class ServiceOut(BaseModel):
    id: str
    name: str
    duration_minutes: int
    price: float
    description: Optional[str] = None

class BarberOut(BaseModel):
    id: str
    name: str
    specialties: List[str]
    bio: Optional[str] = None

class AppointmentCreate(AppointmentSchema):
    pass

class AppointmentOut(BaseModel):
    id: str
    customer_name: str
    customer_phone: str
    customer_email: Optional[str] = None
    service_id: str
    barber_id: str
    date: str
    time: str

# -----------------------------
# Routes
# -----------------------------

@app.get("/api/services", response_model=List[ServiceOut])
def list_services():
    docs = get_documents("service") if db is not None else []
    return [ServiceOut(**serialize_doc(d)) for d in docs]

@app.get("/api/barbers", response_model=List[BarberOut])
def list_barbers():
    docs = get_documents("barber") if db is not None else []
    return [BarberOut(**serialize_doc(d)) for d in docs]

@app.get("/api/appointments", response_model=List[AppointmentOut])
def list_appointments(date: Optional[str] = None, barber_id: Optional[str] = None):
    if db is None:
        return []
    query = {}
    if date:
        query["date"] = date
    if barber_id:
        # stored as string
        query["barber_id"] = barber_id
    docs = get_documents("appointment", query)
    return [AppointmentOut(**serialize_doc(d)) for d in docs]

@app.post("/api/appointments", response_model=AppointmentOut)
def create_appointment(payload: AppointmentCreate):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")

    # Validate referenced service and barber exist
    service_exists = db.service.count_documents({"_id": ObjectId(payload.service_id)}) if ObjectId.is_valid(payload.service_id) else db.service.count_documents({"_id": payload.service_id})
    barber_exists = db.barber.count_documents({"_id": ObjectId(payload.barber_id)}) if ObjectId.is_valid(payload.barber_id) else db.barber.count_documents({"_id": payload.barber_id})
    if service_exists == 0:
        raise HTTPException(status_code=400, detail="Invalid service_id")
    if barber_exists == 0:
        raise HTTPException(status_code=400, detail="Invalid barber_id")

    # Prevent double booking: same barber at same date+time
    conflict = db.appointment.count_documents({"barber_id": payload.barber_id, "date": payload.date, "time": payload.time})
    if conflict > 0:
        raise HTTPException(status_code=409, detail="Time slot already booked for this barber")

    inserted_id = create_document("appointment", payload)
    doc = db.appointment.find_one({"_id": ObjectId(inserted_id)}) if ObjectId.is_valid(inserted_id) else db.appointment.find_one({"_id": inserted_id})
    return AppointmentOut(**serialize_doc(doc))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
