"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List

# Example schemas (replace with your own):

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# Barber Shop App Schemas

class Service(BaseModel):
    name: str = Field(..., description="Service name, e.g., Haircut")
    duration_minutes: int = Field(..., ge=10, le=240, description="Duration of service in minutes")
    price: float = Field(..., ge=0, description="Service price")
    description: Optional[str] = Field(None, description="Short description")

class Barber(BaseModel):
    name: str = Field(..., description="Barber name")
    specialties: List[str] = Field(default_factory=list, description="List of specialties")
    bio: Optional[str] = Field(None, description="Short bio")

class Appointment(BaseModel):
    customer_name: str = Field(..., description="Customer full name")
    customer_phone: str = Field(..., description="Contact phone")
    customer_email: Optional[str] = Field(None, description="Contact email")
    service_id: str = Field(..., description="ID of the selected service")
    barber_id: str = Field(..., description="ID of the selected barber")
    date: str = Field(..., description="Date in YYYY-MM-DD")
    time: str = Field(..., description="Time in HH:MM 24h format")

# Note: The Flames database viewer will automatically:
# 1. Read these schemas from GET /schema endpoint
# 2. Use them for document validation when creating/editing
# 3. Handle all database operations (CRUD) directly
# 4. You don't need to create any database endpoints!
