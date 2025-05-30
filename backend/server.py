from fastapi import FastAPI, APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import csv
import io
import json
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
import uuid
from datetime import datetime, timedelta
import random
from decimal import Decimal

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="PayPal Mock Transaction Generator", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Transaction Models
class PayPalTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    transaction_id: str = Field(default_factory=lambda: f"TXN{random.randint(100000000, 999999999)}")
    transaction_type: Literal["payment", "refund", "subscription", "dispute", "chargeback"] = "payment"
    status: Literal["completed", "pending", "failed", "cancelled", "refunded", "disputed"] = "completed"
    amount: float
    currency: str = "USD"
    fee: float = 0.0
    net_amount: float = 0.0
    payer_email: str
    payer_name: str
    recipient_email: str
    recipient_name: str
    merchant_id: str = Field(default_factory=lambda: f"MERCHANT{random.randint(100000, 999999)}")
    description: str
    invoice_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class TransactionGenerateRequest(BaseModel):
    count: int = Field(default=10, ge=1, le=1000)
    transaction_type: Optional[Literal["payment", "refund", "subscription", "dispute", "chargeback"]] = None
    status: Optional[Literal["completed", "pending", "failed", "cancelled", "refunded", "disputed"]] = None
    min_amount: float = Field(default=1.0, ge=0.01)
    max_amount: float = Field(default=1000.0, ge=0.01)
    currency: str = "USD"
    days_back: int = Field(default=30, ge=1, le=365)

class BulkExportRequest(BaseModel):
    format: Literal["json", "csv"] = "json"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    transaction_type: Optional[str] = None
    status: Optional[str] = None

# Sample data for realistic generation
SAMPLE_NAMES = [
    "John Smith", "Sarah Johnson", "Michael Brown", "Emily Davis", "David Wilson",
    "Jessica Garcia", "Christopher Martinez", "Ashley Anderson", "Matthew Taylor",
    "Amanda Thomas", "Daniel Jackson", "Jennifer White", "James Harris", "Lisa Martin"
]

SAMPLE_EMAILS = [
    "john.smith@email.com", "sarah.j@gmail.com", "mike.brown@yahoo.com",
    "emily.davis@outlook.com", "david.w@company.com", "jessica.g@business.org",
    "chris.m@startup.io", "ashley.a@freelance.net", "matt.t@agency.com",
    "amanda.th@consultant.biz", "daniel.j@enterprise.com", "jennifer.w@shop.store"
]

SAMPLE_DESCRIPTIONS = [
    "Online Purchase - Electronics", "Digital Service Subscription", "Freelance Web Development",
    "Online Course Payment", "E-commerce Store Purchase", "Consulting Services",
    "Software License Fee", "Marketplace Commission", "Digital Download",
    "Monthly Subscription", "Product Return Refund", "Service Cancellation"
]

def generate_realistic_transaction(
    transaction_type: Optional[str] = None,
    status: Optional[str] = None,
    min_amount: float = 1.0,
    max_amount: float = 1000.0,
    currency: str = "USD",
    days_back: int = 30
) -> PayPalTransaction:
    """Generate a single realistic PayPal transaction"""
    
    # Generate random amount
    amount = round(random.uniform(min_amount, max_amount), 2)
    
    # Calculate fee (typical PayPal fee: 2.9% + $0.30)
    fee = round((amount * 0.029) + 0.30, 2)
    net_amount = round(amount - fee, 2)
    
    # Generate random timestamp within the specified range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days_back)
    random_timestamp = start_date + timedelta(
        seconds=random.randint(0, int((end_date - start_date).total_seconds()))
    )
    
    # Select random data
    payer_name = random.choice(SAMPLE_NAMES)
    payer_email = random.choice(SAMPLE_EMAILS)
    recipient_name = random.choice(SAMPLE_NAMES)
    recipient_email = random.choice(SAMPLE_EMAILS)
    description = random.choice(SAMPLE_DESCRIPTIONS)
    
    # Ensure payer and recipient are different
    while recipient_email == payer_email:
        recipient_email = random.choice(SAMPLE_EMAILS)
    while recipient_name == payer_name:
        recipient_name = random.choice(SAMPLE_NAMES)
    
    # Set transaction type and status
    if not transaction_type:
        transaction_type = random.choice(["payment", "refund", "subscription", "dispute", "chargeback"])
    
    if not status:
        # Weighted status distribution (most transactions are completed)
        status_weights = {
            "completed": 0.7,
            "pending": 0.15,
            "failed": 0.05,
            "cancelled": 0.03,
            "refunded": 0.04,
            "disputed": 0.03
        }
        status = random.choices(
            list(status_weights.keys()),
            weights=list(status_weights.values())
        )[0]
    
    # Adjust amounts for refunds
    if transaction_type == "refund":
        amount = -abs(amount)
        fee = -abs(fee)
        net_amount = amount - fee
    
    return PayPalTransaction(
        transaction_type=transaction_type,
        status=status,
        amount=amount,
        currency=currency,
        fee=fee,
        net_amount=net_amount,
        payer_email=payer_email,
        payer_name=payer_name,
        recipient_email=recipient_email,
        recipient_name=recipient_name,
        description=description,
        invoice_id=f"INV-{random.randint(1000, 9999)}" if random.random() > 0.5 else None,
        timestamp=random_timestamp,
        created_at=random_timestamp
    )

# API Routes
@api_router.get("/")
async def root():
    return {
        "message": "PayPal Mock Transaction Generator API",
        "version": "1.0.0",
        "endpoints": [
            "/api/transactions/generate",
            "/api/transactions",
            "/api/transactions/export",
            "/api/transactions/stats"
        ]
    }

@api_router.post("/transactions/generate", response_model=List[PayPalTransaction])
async def generate_transactions(request: TransactionGenerateRequest):
    """Generate mock PayPal transactions"""
    transactions = []
    
    for _ in range(request.count):
        transaction = generate_realistic_transaction(
            transaction_type=request.transaction_type,
            status=request.status,
            min_amount=request.min_amount,
            max_amount=request.max_amount,
            currency=request.currency,
            days_back=request.days_back
        )
        transactions.append(transaction)
        
        # Save to database
        await db.transactions.insert_one(transaction.dict())
    
    return transactions

@api_router.get("/transactions", response_model=List[PayPalTransaction])
async def get_transactions(
    limit: int = Query(50, ge=1, le=1000),
    skip: int = Query(0, ge=0),
    transaction_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    """Get stored transactions with filtering"""
    filter_query = {}
    
    if transaction_type:
        filter_query["transaction_type"] = transaction_type
    if status:
        filter_query["status"] = status
    
    transactions = await db.transactions.find(filter_query).skip(skip).limit(limit).sort("timestamp", -1).to_list(limit)
    return [PayPalTransaction(**transaction) for transaction in transactions]

@api_router.get("/transactions/stats")
async def get_transaction_stats():
    """Get transaction statistics"""
    total_count = await db.transactions.count_documents({})
    
    # Get stats by type
    type_pipeline = [
        {"$group": {"_id": "$transaction_type", "count": {"$sum": 1}, "total_amount": {"$sum": "$amount"}}}
    ]
    type_stats = await db.transactions.aggregate(type_pipeline).to_list(100)
    
    # Get stats by status
    status_pipeline = [
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    status_stats = await db.transactions.aggregate(status_pipeline).to_list(100)
    
    # Get recent activity (last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_count = await db.transactions.count_documents({"timestamp": {"$gte": seven_days_ago}})
    
    return {
        "total_transactions": total_count,
        "recent_transactions": recent_count,
        "by_type": {stat["_id"]: {"count": stat["count"], "total_amount": stat.get("total_amount", 0)} for stat in type_stats},
        "by_status": {stat["_id"]: stat["count"] for stat in status_stats}
    }

@api_router.post("/transactions/export")
async def export_transactions(request: BulkExportRequest):
    """Export transactions in JSON or CSV format"""
    filter_query = {}
    
    if request.start_date:
        filter_query["timestamp"] = {"$gte": request.start_date}
    if request.end_date:
        if "timestamp" in filter_query:
            filter_query["timestamp"]["$lte"] = request.end_date
        else:
            filter_query["timestamp"] = {"$lte": request.end_date}
    if request.transaction_type:
        filter_query["transaction_type"] = request.transaction_type
    if request.status:
        filter_query["status"] = request.status
    
    transactions = await db.transactions.find(filter_query).sort("timestamp", -1).to_list(10000)
    
    if request.format == "json":
        # Return JSON format
        json_data = json.dumps([PayPalTransaction(**t).dict() for t in transactions], default=str, indent=2)
        return StreamingResponse(
            io.StringIO(json_data),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=transactions.json"}
        )
    
    elif request.format == "csv":
        # Return CSV format
        output = io.StringIO()
        if transactions:
            fieldnames = PayPalTransaction(**transactions[0]).dict().keys()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            for transaction in transactions:
                writer.writerow(PayPalTransaction(**transaction).dict())
        
        return StreamingResponse(
            io.StringIO(output.getvalue()),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=transactions.csv"}
        )

@api_router.delete("/transactions")
async def clear_all_transactions():
    """Clear all generated transactions"""
    result = await db.transactions.delete_many({})
    return {"message": f"Cleared {result.deleted_count} transactions"}

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
