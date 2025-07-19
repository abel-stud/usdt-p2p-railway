from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import os
from datetime import datetime

# Import our modules
from src.database import get_db, init_database, test_connection
from src.models import User, Listing, Deal, Log
from src.schemas import (
    UserCreate, UserResponse, 
    ListingCreate, ListingResponse,
    DealCreate, DealResponse,
    PaymentConfirmation, AdminRelease
)

# Create FastAPI app
app = FastAPI(
    title="P2P USDT Trading API",
    description="API for P2P USDT trading platform in Ethiopia",
    version="1.0.0"
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
ESCROW_WALLET = os.getenv("ESCROW_WALLET", "TXxxxxxx")
COMMISSION_PERCENT = float(os.getenv("COMMISSION_PERCENT", "1.5"))
RELEASE_SECRET = os.getenv("RELEASE_SECRET", "p2p_secure_release_key_2024")

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    print("🚀 Starting P2P USDT Trading API...")
    print(f"📊 Database URL: {os.getenv('DATABASE_URL', 'SQLite (local)')}")
    
    # Test database connection
    if test_connection():
        print("✅ Database connection successful")
    else:
        print("❌ Database connection failed")
        
    # Initialize database
    try:
        init_database()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "P2P USDT Trading API",
        "version": "1.0.0",
        "status": "operational",
        "escrow_wallet": ESCROW_WALLET,
        "commission_percent": COMMISSION_PERCENT
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "connected" if test_connection() else "disconnected"
    }

# User endpoints
@app.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user"""
    # Check if user already exists
    existing_user = db.query(User).filter(User.telegram_username == user.telegram_username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users", response_model=List[UserResponse])
async def get_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all users"""
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get user by ID"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Listing endpoints
@app.post("/listings", response_model=ListingResponse)
async def create_listing(listing: ListingCreate, db: Session = Depends(get_db)):
    """Create a new listing"""
    # Verify user exists
    user = db.query(User).filter(User.id == listing.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_listing = Listing(**listing.dict())
    db.add(db_listing)
    db.commit()
    db.refresh(db_listing)
    return db_listing

@app.get("/listings", response_model=List[ListingResponse])
async def get_listings(skip: int = 0, limit: int = 100, listing_type: str = None, db: Session = Depends(get_db)):
    """Get all listings"""
    query = db.query(Listing).filter(Listing.status == "active")
    
    if listing_type:
        query = query.filter(Listing.listing_type == listing_type)
    
    listings = query.offset(skip).limit(limit).all()
    return listings

@app.get("/listings/{listing_id}", response_model=ListingResponse)
async def get_listing(listing_id: int, db: Session = Depends(get_db)):
    """Get listing by ID"""
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing

# Deal endpoints
@app.post("/deals", response_model=DealResponse)
async def create_deal(deal: DealCreate, db: Session = Depends(get_db)):
    """Create a new deal"""
    # Verify listing exists
    listing = db.query(Listing).filter(Listing.id == deal.listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    # Generate unique trade code
    trade_code = Deal.generate_trade_code()
    while db.query(Deal).filter(Deal.trade_code == trade_code).first():
        trade_code = Deal.generate_trade_code()
    
    # Calculate amounts
    etb_amount = deal.usdt_amount * listing.rate
    commission = deal.usdt_amount * (COMMISSION_PERCENT / 100)
    
    db_deal = Deal(
        listing_id=deal.listing_id,
        buyer_id=deal.buyer_id,
        seller_id=listing.user_id,
        usdt_amount=deal.usdt_amount,
        etb_amount=etb_amount,
        trade_code=trade_code,
        escrow_wallet=ESCROW_WALLET,
        commission_amount=commission
    )
    
    db.add(db_deal)
    db.commit()
    db.refresh(db_deal)
    
    # Log deal creation
    log = Log(
        deal_id=db_deal.id,
        action="Deal created",
        notes=f"Trade code: {trade_code}, Amount: {deal.usdt_amount} USDT"
    )
    db.add(log)
    db.commit()
    
    return db_deal

@app.get("/deals", response_model=List[DealResponse])
async def get_deals(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all deals"""
    deals = db.query(Deal).offset(skip).limit(limit).all()
    return deals

@app.get("/deals/{trade_code}", response_model=DealResponse)
async def get_deal(trade_code: str, db: Session = Depends(get_db)):
    """Get deal by trade code"""
    # Remove # if present
    if trade_code.startswith("#"):
        trade_code = trade_code[1:]
    
    deal = db.query(Deal).filter(Deal.trade_code == trade_code).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    return deal

@app.post("/confirm-payment")
async def confirm_payment(confirmation: PaymentConfirmation, db: Session = Depends(get_db)):
    """Confirm payment received"""
    # Remove # if present
    trade_code = confirmation.trade_code
    if trade_code.startswith("#"):
        trade_code = trade_code[1:]
    
    deal = db.query(Deal).filter(Deal.trade_code == trade_code).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    if deal.status != "pending":
        raise HTTPException(status_code=400, detail="Deal is not in pending status")
    
    # Update deal status
    deal.status = "paid"
    db.commit()
    
    # Log payment confirmation
    log = Log(
        deal_id=deal.id,
        action="Payment confirmed",
        notes=f"Seller confirmed ETB payment received"
    )
    db.add(log)
    db.commit()
    
    return {"message": "Payment confirmed successfully", "trade_code": deal.trade_code}

@app.post("/admin/release-funds")
async def release_funds(release: AdminRelease, db: Session = Depends(get_db)):
    """Admin release funds"""
    if release.secret != RELEASE_SECRET:
        raise HTTPException(status_code=403, detail="Invalid admin secret")
    
    # Remove # if present
    trade_code = release.trade_code
    if trade_code.startswith("#"):
        trade_code = trade_code[1:]
    
    deal = db.query(Deal).filter(Deal.trade_code == trade_code).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    if deal.status != "paid":
        raise HTTPException(status_code=400, detail="Deal payment not confirmed")
    
    # Update deal status
    deal.status = "released"
    db.commit()
    
    # Log fund release
    log = Log(
        deal_id=deal.id,
        action="Funds released",
        notes=f"Admin released {deal.usdt_amount - deal.commission_amount} USDT to buyer"
    )
    db.add(log)
    db.commit()
    
    return {
        "message": "Funds released successfully",
        "trade_code": deal.trade_code,
        "amount_released": deal.usdt_amount - deal.commission_amount,
        "commission": deal.commission_amount
    }

@app.get("/admin/pending-deals")
async def get_pending_deals(db: Session = Depends(get_db)):
    """Get all pending deals for admin"""
    deals = db.query(Deal).filter(Deal.status.in_(["pending", "paid"])).all()
    return deals

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

