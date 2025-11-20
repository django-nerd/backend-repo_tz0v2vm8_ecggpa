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

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import date

# Example schemas (retain for reference):

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

# Job portal schemas

class Company(BaseModel):
    """
    Companies collection
    Collection name: "company"
    """
    name: str
    logo_url: Optional[HttpUrl] = None
    website: Optional[HttpUrl] = None
    tagline: Optional[str] = None
    spotlight: bool = False
    accent_color: Optional[str] = Field(None, description="Hex color for UI accents")

class Category(BaseModel):
    """
    Job categories
    Collection name: "category"
    """
    slug: str
    title: str
    emoji: Optional[str] = None
    description: Optional[str] = None

class Job(BaseModel):
    """
    Jobs collection
    Collection name: "job"
    """
    title: str
    company: str = Field(..., description="Company name")
    category: str = Field(..., description="Category slug")
    location: str = Field(..., description="City/Country or Remote")
    remote: bool = True
    type: str = Field(..., description="Full-time, Part-time, Internship, Contract")
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    currency: str = "USD"
    description: Optional[str] = None
    requirements: Optional[List[str]] = None
    apply_url: Optional[HttpUrl] = None
    featured: bool = False
    posted_on: Optional[date] = None
