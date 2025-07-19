from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database import Base
import random
import string

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    telegram_username = Column(String(50), unique=True, nullable=False)
    user_type = Column(String(20), nullable=False)  # 'buyer' or 'seller' or 'both'
    verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    listings = relationship("Listing", back_populates="user")
    buyer_deals = relationship("Deal", foreign_keys="Deal.buyer_id", back_populates="buyer")
    seller_deals = relationship("Deal", foreign_keys="Deal.seller_id", back_populates="seller")

class Listing(Base):
    __tablename__ = "listings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    listing_type = Column(String(10), nullable=False)  # 'buy' or 'sell'
    amount = Column(Float, nullable=False)  # USDT amount
    rate = Column(Float, nullable=False)  # ETB per USDT
    payment_method = Column(String(100), nullable=False)
    contact = Column(String(200), nullable=False)
    status = Column(String(20), default="active")  # 'active', 'inactive', 'completed'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="listings")
    deals = relationship("Deal", back_populates="listing")

class Deal(Base):
    __tablename__ = "deals"
    
    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    usdt_amount = Column(Float, nullable=False)
    etb_amount = Column(Float, nullable=False)
    trade_code = Column(String(10), unique=True, nullable=False)
    escrow_wallet = Column(String(100), nullable=False)
    status = Column(String(20), default="pending")  # 'pending', 'paid', 'released', 'cancelled'
    commission_amount = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    listing = relationship("Listing", back_populates="deals")
    buyer = relationship("User", foreign_keys=[buyer_id], back_populates="buyer_deals")
    seller = relationship("User", foreign_keys=[seller_id], back_populates="seller_deals")
    logs = relationship("Log", back_populates="deal")
    
    @staticmethod
    def generate_trade_code():
        """Generate unique trade code"""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

class Log(Base):
    __tablename__ = "logs"
    
    id = Column(Integer, primary_key=True, index=True)
    deal_id = Column(Integer, ForeignKey("deals.id"), nullable=False)
    action = Column(String(100), nullable=False)
    notes = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    deal = relationship("Deal", back_populates="logs")

