from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    telegram_username: str = Field(..., pattern=r'^[a-zA-Z0-9_]{5,32}$')
    user_type: str = Field(..., pattern=r'^(buyer|seller|both)$')

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: int
    verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Listing schemas
class ListingBase(BaseModel):
    listing_type: str = Field(..., pattern=r'^(buy|sell)$')
    amount: float = Field(..., gt=0)
    rate: float = Field(..., gt=0)
    payment_method: str = Field(..., min_length=1, max_length=100)
    contact: str = Field(..., min_length=1, max_length=200)

class ListingCreate(ListingBase):
    user_id: int

class ListingResponse(ListingBase):
    id: int
    user_id: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Deal schemas
class DealBase(BaseModel):
    usdt_amount: float = Field(..., gt=0)

class DealCreate(DealBase):
    listing_id: int
    buyer_id: int

class DealResponse(DealBase):
    id: int
    listing_id: int
    buyer_id: int
    seller_id: int
    etb_amount: float
    trade_code: str
    escrow_wallet: str
    status: str
    commission_amount: float
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Payment confirmation schema
class PaymentConfirmation(BaseModel):
    trade_code: str = Field(..., min_length=1)

# Admin release schema
class AdminRelease(BaseModel):
    trade_code: str = Field(..., min_length=1)
    secret: str = Field(..., min_length=1)

# Log schema
class LogResponse(BaseModel):
    id: int
    deal_id: int
    action: str
    notes: Optional[str]
    timestamp: datetime
    
    class Config:
        from_attributes = True

