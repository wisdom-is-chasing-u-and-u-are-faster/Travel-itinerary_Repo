"""
Pydantic Data Models and Schemas for Travel Itinerary Generator Platform.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ProblemDetails(BaseModel):
    type: str = "about:blank"
    title: str
    status: int
    detail: str
    instance: Optional[str] = None

class ActivityItem(BaseModel):
    id: Optional[str] = None
    time: str = "09:00 AM"
    title: str
    location: str
    latitude: Optional[float] = 0.0
    longitude: Optional[float] = 0.0
    cost: Optional[float] = 0.0
    category: Optional[str] = "Sightseeing"
    notes: Optional[str] = ""

class ItineraryDay(BaseModel):
    id: Optional[str] = None
    day_number: int
    date: str
    theme: Optional[str] = "Day Exploration"
    activities: List[ActivityItem] = []

class GenerateItineraryRequest(BaseModel):
    destination: str
    start_date: str
    end_date: str
    pacing: Optional[str] = "Moderate"
    interests: Optional[List[str]] = Field(default_factory=lambda: ["Culture", "Dining"])
    budget_level: Optional[str] = "Standard"

class ItineraryDetail(BaseModel):
    id: str
    title: str
    destination: str
    start_date: str
    end_date: str
    pacing: str = "Moderate"
    version: int = 1
    updated_at: Optional[str] = None
    days: List[ItineraryDay] = []

class UpdateItineraryRequest(BaseModel):
    title: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    pacing: Optional[str] = None

class CreateActivityRequest(BaseModel):
    day_id: int
    title: str
    time: Optional[str] = "09:00 AM"
    location: str
    cost: Optional[float] = 0.0
    category: Optional[str] = "Sightseeing"
    notes: Optional[str] = ""

class DeltaMutation(BaseModel):
    entity: str
    action: str
    data: Dict[str, Any]
    timestamp: str

class SyncRequest(BaseModel):
    client_timestamp: str
    mutations: List[DeltaMutation]

class CollaboratorItem(BaseModel):
    id: int
    name: str
    email: str
    role: str = "Editor"
    status: str = "Active"

class InviteCollaboratorRequest(BaseModel):
    email: str
    role: str = "Editor"

class ExpenseItem(BaseModel):
    id: int
    title: str
    amount: float
    currency: str
    paid_by: str
    category: str
    date: str

class SettlementItem(BaseModel):
    from_user: str
    to_user: str
    amount: float
    currency: str

class ExpenseLedgerResponse(BaseModel):
    trip_id: int
    base_currency: str = "USD"
    total_spent: float
    expenses: List[ExpenseItem]
    settlements: List[SettlementItem]

class CreateExpenseRequest(BaseModel):
    title: str
    amount: float
    currency: str = "USD"
    paid_by: str
    category: str = "General"
    split_between: Optional[List[str]] = None

class AffiliateRecommendation(BaseModel):
    id: int
    title: str
    destination: str
    provider: str
    price: float
    rating: float
    image_url: str
    affiliate_url: str

class CheckoutRequest(BaseModel):
    experience_id: str
    payment_token: str
    amount: float
    currency: str = "USD"

class AdminStatsResponse(BaseModel):
    total_itineraries: int
    uptime_percent: float
    p95_ttfb_seconds: float
    affiliate_ctr_percent: float
    in_app_conversion_percent: float

class UserProfile(BaseModel):
    name: str
    email: str
    offline_caching_enabled: bool = True
    preferred_currency: str = "USD"
    notifications_enabled: bool = True
