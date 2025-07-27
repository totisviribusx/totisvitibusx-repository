from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, date
from enum import Enum


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Enums
class PaymentMethod(str, Enum):
    PAYPAL = "PayPal"
    VENMO = "Venmo"
    VISA = "Visa"
    MASTERCARD = "Mastercard"
    AMEX = "American Express"
    DISCOVER = "Discover"
    DEBIT_CARD = "Debit Card"
    OTHER = "Other"

class PurchaseStatus(str, Enum):
    ORDERED = "Ordered"
    SHIPPED = "Shipped"
    DELIVERED = "Delivered"
    RETURNED = "Returned"
    ARCHIVED = "Archived"


# Define Models
class Store(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    url: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class StoreCreate(BaseModel):
    name: str
    url: str

class Purchase(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    store_name: str
    store_url: Optional[str] = None
    product_name: str
    price: float
    payment_method: PaymentMethod
    order_date: date
    expected_delivery: Optional[date] = None
    delivered_date: Optional[date] = None
    status: PurchaseStatus = PurchaseStatus.ORDERED
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class PurchaseCreate(BaseModel):
    store_name: str
    store_url: Optional[str] = None
    product_name: str
    price: float
    payment_method: PaymentMethod
    order_date: date
    expected_delivery: Optional[date] = None
    delivered_date: Optional[date] = None
    status: PurchaseStatus = PurchaseStatus.ORDERED
    notes: Optional[str] = None

class PurchaseUpdate(BaseModel):
    store_name: Optional[str] = None
    store_url: Optional[str] = None
    product_name: Optional[str] = None
    price: Optional[float] = None
    payment_method: Optional[PaymentMethod] = None
    order_date: Optional[date] = None
    expected_delivery: Optional[date] = None
    delivered_date: Optional[date] = None
    status: Optional[PurchaseStatus] = None
    notes: Optional[str] = None


# Store Routes
@api_router.post("/stores", response_model=Store)
async def create_store(store: StoreCreate):
    store_dict = store.dict()
    store_obj = Store(**store_dict)
    await db.stores.insert_one(store_obj.dict())
    return store_obj

@api_router.get("/stores", response_model=List[Store])
async def get_stores():
    stores = await db.stores.find().sort("name", 1).to_list(1000)
    return [Store(**store) for store in stores]

@api_router.delete("/stores/{store_id}")
async def delete_store(store_id: str):
    result = await db.stores.delete_one({"id": store_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Store not found")
    return {"message": "Store deleted successfully"}


# Purchase Routes
@api_router.post("/purchases", response_model=Purchase)
async def create_purchase(purchase: PurchaseCreate):
    purchase_dict = purchase.dict()
    purchase_obj = Purchase(**purchase_dict)
    
    # Convert date objects to strings for MongoDB storage
    purchase_data = purchase_obj.dict()
    if purchase_data.get('order_date'):
        purchase_data['order_date'] = purchase_data['order_date'].isoformat()
    if purchase_data.get('expected_delivery'):
        purchase_data['expected_delivery'] = purchase_data['expected_delivery'].isoformat()
    if purchase_data.get('delivered_date'):
        purchase_data['delivered_date'] = purchase_data['delivered_date'].isoformat()
    
    await db.purchases.insert_one(purchase_data)
    
    # Auto-create store if it doesn't exist and has URL
    if purchase.store_url:
        existing_store = await db.stores.find_one({"name": purchase.store_name})
        if not existing_store:
            store_obj = Store(name=purchase.store_name, url=purchase.store_url)
            await db.stores.insert_one(store_obj.dict())
    
    return purchase_obj

@api_router.get("/purchases", response_model=List[Purchase])
async def get_purchases(status: Optional[str] = None, archived: bool = False):
    query = {}
    if status:
        query["status"] = status
    if not archived:
        query["status"] = {"$ne": "Archived"}
    
    purchases = await db.purchases.find(query).sort("created_at", -1).to_list(1000)
    return [Purchase(**purchase) for purchase in purchases]

@api_router.get("/purchases/{purchase_id}", response_model=Purchase)
async def get_purchase(purchase_id: str):
    purchase = await db.purchases.find_one({"id": purchase_id})
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    return Purchase(**purchase)

@api_router.put("/purchases/{purchase_id}", response_model=Purchase)
async def update_purchase(purchase_id: str, purchase_update: PurchaseUpdate):
    update_dict = {k: v for k, v in purchase_update.dict().items() if v is not None}
    update_dict["updated_at"] = datetime.utcnow()
    
    result = await db.purchases.update_one(
        {"id": purchase_id}, 
        {"$set": update_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Purchase not found")
    
    updated_purchase = await db.purchases.find_one({"id": purchase_id})
    return Purchase(**updated_purchase)

@api_router.delete("/purchases/{purchase_id}")
async def delete_purchase(purchase_id: str):
    result = await db.purchases.delete_one({"id": purchase_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Purchase not found")
    return {"message": "Purchase deleted successfully"}

@api_router.post("/purchases/{purchase_id}/archive")
async def archive_purchase(purchase_id: str):
    result = await db.purchases.update_one(
        {"id": purchase_id}, 
        {"$set": {"status": "Archived", "updated_at": datetime.utcnow()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Purchase not found")
    
    return {"message": "Purchase archived successfully"}


# Dashboard Stats
@api_router.get("/dashboard/stats")
async def get_dashboard_stats():
    total_purchases = await db.purchases.count_documents({"status": {"$ne": "Archived"}})
    total_spent = await db.purchases.aggregate([
        {"$match": {"status": {"$ne": "Archived"}}},
        {"$group": {"_id": None, "total": {"$sum": "$price"}}}
    ]).to_list(1)
    
    recent_purchases = await db.purchases.find(
        {"status": {"$ne": "Archived"}}
    ).sort("created_at", -1).limit(5).to_list(5)
    
    status_counts = await db.purchases.aggregate([
        {"$match": {"status": {"$ne": "Archived"}}},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]).to_list(10)
    
    return {
        "total_purchases": total_purchases,
        "total_spent": total_spent[0]["total"] if total_spent else 0,
        "recent_purchases": [Purchase(**p) for p in recent_purchases],
        "status_breakdown": {item["_id"]: item["count"] for item in status_counts}
    }


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()