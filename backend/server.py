from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime
import hashlib
import jwt
import qrcode
import io
import base64
from enum import Enum
import pandas as pd
import json

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

# JWT Secret
JWT_SECRET = "imagross_secret_key_2024"
security = HTTPBearer()

# Enums
class Gender(str, Enum):
    M = "M"
    F = "F"
    OTHER = "Other"

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

class StoreStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"

# Enhanced Models
class Store(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    code: str  # IMAGROSS 1, IMAGROSS 2, etc.
    address: str
    city: str
    province: str
    phone: str
    status: StoreStatus = StoreStatus.ACTIVE
    manager_name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    total_cashiers: int = 0

class StoreCreate(BaseModel):
    name: str
    code: str
    address: str
    city: str
    province: str
    phone: str
    manager_name: Optional[str] = None

class Cashier(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    store_id: str
    cashier_number: int
    name: str
    qr_code: str
    qr_code_image: str  # Base64 image
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    total_registrations: int = 0

class CashierCreate(BaseModel):
    store_id: str
    cashier_number: int
    name: str

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nome: str
    cognome: str
    sesso: Gender
    email: EmailStr
    telefono: str
    localita: str
    tessera_fisica: str
    tessera_digitale: str = Field(default_factory=lambda: str(uuid.uuid4()))
    punti: int = 0
    password_hash: str
    role: UserRole = UserRole.USER
    store_id: Optional[str] = None  # Store where registered
    cashier_id: Optional[str] = None  # Cashier where registered
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    active: bool = True
    migrated: bool = False  # For tessera migration tracking
    
    # Expanded fields from JSON anagrafica
    stato_tessera: str = "01"  # stato_tes
    indirizzo: Optional[str] = None
    cap: Optional[str] = None
    numero_civico: Optional[str] = None
    provincia: Optional[str] = None
    data_nascita: Optional[str] = None  # data_nas
    newsletter: bool = False
    data_creazione: Optional[str] = None  # data_creazione from JSON
    data_ultima_spesa: Optional[str] = None  # data_ult_sc
    progressivo_spesa: float = 0.0  # prog_spesa
    bollini: int = 0
    
    # Privacy settings
    consenso_dati_personali: bool = True  # dati_pers
    consenso_dati_pubblicitari: bool = True  # dati_pubb
    consenso_profilazione: Optional[bool] = None  # profilazione
    consenso_marketing: Optional[bool] = None  # marketing
    
    # Family data
    coniugato: Optional[bool] = None
    data_matrimonio: Optional[str] = None  # data_coniugato
    numero_figli: int = 0
    data_figlio_1: Optional[str] = None
    data_figlio_2: Optional[str] = None
    data_figlio_3: Optional[str] = None
    data_figlio_4: Optional[str] = None
    data_figlio_5: Optional[str] = None
    
    # Animals
    animali_cani: bool = False  # animali_1
    animali_gatti: bool = False  # animali_2
    
    # Food intolerances
    intolleranza_lattosio: bool = False  # lattosio
    intolleranza_glutine: bool = False  # glutine
    intolleranza_nichel: bool = False  # nichel
    celiachia: bool = False
    altra_intolleranza: Optional[str] = None  # altro_intolleranza
    
    # Business data
    richiede_fattura: bool = False  # fattura
    ragione_sociale: Optional[str] = None

class UserCreate(BaseModel):
    nome: str
    cognome: str
    sesso: Gender
    email: EmailStr
    telefono: str
    localita: str
    tessera_fisica: Optional[str] = None  # Optional for new registrations
    password: str
    # Optional registration context
    store_id: Optional[str] = None
    cashier_id: Optional[str] = None
    # Extended optional fields for fidelity import
    indirizzo: Optional[str] = None
    cap: Optional[str] = None
    provincia: Optional[str] = None
    data_nascita: Optional[str] = None
    newsletter: bool = False
    bollini: Optional[int] = None
    progressivo_spesa: Optional[float] = None
    consenso_dati_personali: bool = True
    consenso_dati_pubblicitari: bool = True
    consenso_profilazione: Optional[bool] = None
    consenso_marketing: Optional[bool] = None
    coniugato: Optional[bool] = None
    data_matrimonio: Optional[str] = None
    numero_figli: Optional[int] = None
    animali_cani: bool = False
    animali_gatti: bool = False
    intolleranza_lattosio: bool = False
    intolleranza_glutine: bool = False
    intolleranza_nichel: bool = False
    celiachia: bool = False
    altra_intolleranza: Optional[str] = None
    richiede_fattura: bool = False
    ragione_sociale: Optional[str] = None

class TesseraCheck(BaseModel):
    tessera_fisica: str

class Transaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    store_id: str
    cashier_id: Optional[str] = None
    scontrino_number: str
    date: datetime
    total_amount: float
    points_earned: int
    items: List[dict] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AdminUser(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: EmailStr
    password_hash: str
    role: UserRole
    full_name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    active: bool = True

class AdminUserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    role: UserRole = UserRole.ADMIN

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class AdminLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: str
    nome: str
    cognome: str
    sesso: Gender
    email: EmailStr
    telefono: str
    localita: str
    tessera_fisica: str
    tessera_digitale: str
    punti: int
    created_at: datetime
    qr_code: str
    store_name: Optional[str] = None
    cashier_name: Optional[str] = None

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str
    admin: dict

# Helper functions
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed_password: str) -> bool:
    return hashlib.sha256(password.encode()).hexdigest() == hashed_password

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    return jwt.encode(to_encode, JWT_SECRET, algorithm="HS256")

def generate_qr_code(data: str) -> str:
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode()

def calculate_points(amount: float) -> int:
    # 1 punto ogni 10 euro
    return int(amount / 10)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        user_type: str = payload.get("type", "user")
        
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        if user_type == "admin":
            admin = await db.admins.find_one({"id": user_id})
            if admin is None:
                raise HTTPException(status_code=401, detail="Admin not found")
            return {"type": "admin", "data": AdminUser(**admin)}
        else:
            user = await db.users.find_one({"id": user_id})
            if user is None:
                raise HTTPException(status_code=401, detail="User not found")
            return {"type": "user", "data": User(**user)}
            
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    current_user = await get_current_user(credentials)
    if current_user["type"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    admin = current_user["data"]
    if admin.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Admin role required")
    
    return admin

async def get_super_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    admin = await get_current_admin(credentials)
    if admin.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Super admin access required")
    return admin

# Load scontrini data
SCONTRINI_DATA = []

async def load_scontrini_data():
    """Load scontrini data from JSON file"""
    global SCONTRINI_DATA
    try:
        with open('/app/SCONTRINI_da_Gen2025.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if 'TECLI' in data:
            SCONTRINI_DATA = data['TECLI']
            print(f"Loaded {len(SCONTRINI_DATA)} scontrini records")
            
            # Statistics
            total_importo = sum(float(record.get('IMPORTO_SCONTRINO', 0)) for record in SCONTRINI_DATA)
            total_bollini = sum(float(record.get('N_BOLLINI', 0)) for record in SCONTRINI_DATA)
            unique_customers = len(set(record.get('CODICE_CLIENTE', '') for record in SCONTRINI_DATA))
            unique_stores = len(set(record.get('DITTA', '') for record in SCONTRINI_DATA))
            
            print(f"Scontrini statistics: €{total_importo:,.2f}, {total_bollini:,.0f} bollini, {unique_customers} customers, {unique_stores} stores")
        else:
            print("No TECLI data found in scontrini file")
            SCONTRINI_DATA = []
            
    except Exception as e:
        print(f"Error loading scontrini data: {e}")
        SCONTRINI_DATA = []

def get_dashboard_analytics():
    """Get comprehensive dashboard analytics"""
    from datetime import datetime, timedelta
    from collections import defaultdict
    
    # Base stats from scontrini
    total_revenue = sum(float(record.get('IMPORTO_SCONTRINO', 0)) for record in SCONTRINI_DATA)
    total_transactions = len(SCONTRINI_DATA)
    total_bollini = sum(float(record.get('N_BOLLINI', 0)) for record in SCONTRINI_DATA)
    unique_customers = len(set(record.get('CODICE_CLIENTE', '') for record in SCONTRINI_DATA))
    
    # Revenue by store
    revenue_by_store = defaultdict(float)
    transactions_by_store = defaultdict(int)
    for record in SCONTRINI_DATA:
        store_id = record.get('DITTA', '')
        revenue_by_store[store_id] += float(record.get('IMPORTO_SCONTRINO', 0))
        transactions_by_store[store_id] += 1
    
    # Daily revenue trend (last 30 days of data)
    daily_revenue = defaultdict(float)
    daily_transactions = defaultdict(int)
    for record in SCONTRINI_DATA:
        date_str = record.get('DATA_SCONTRINO', '')
        if len(date_str) == 8:  # YYYYMMDD format
            daily_revenue[date_str] += float(record.get('IMPORTO_SCONTRINO', 0))
            daily_transactions[date_str] += 1
    
    # Top customers by spending
    customer_spending = defaultdict(float)
    customer_transactions = defaultdict(int)
    for record in SCONTRINI_DATA:
        customer_id = record.get('CODICE_CLIENTE', '')
        customer_spending[customer_id] += float(record.get('IMPORTO_SCONTRINO', 0))
        customer_transactions[customer_id] += 1
    
    # Sort and get top 10
    top_customers = sorted(customer_spending.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Payment methods analysis
    payment_methods = defaultdict(int)
    for record in SCONTRINI_DATA:
        payment = record.get('TIPO_PAGAM1', '')
        if payment:
            payment_methods[payment] += 1
    
    # Hourly distribution
    hourly_distribution = defaultdict(int)
    for record in SCONTRINI_DATA:
        hour = record.get('ORA_SCONTRINO', 0)
        if isinstance(hour, int) and hour > 0:
            hour_formatted = hour // 100  # Convert from HHMM to just HH
            if 0 <= hour_formatted <= 23:
                hourly_distribution[hour_formatted] += 1
    
    return {
        "summary": {
            "total_revenue": round(total_revenue, 2),
            "total_transactions": total_transactions,
            "total_bollini": int(total_bollini),
            "unique_customers": unique_customers,
            "avg_transaction": round(total_revenue / total_transactions if total_transactions > 0 else 0, 2),
            "avg_bollini_per_transaction": round(total_bollini / total_transactions if total_transactions > 0 else 0, 2)
        },
        "revenue_by_store": [
            {"store_id": store_id, "revenue": round(revenue, 2), "transactions": transactions_by_store[store_id]}
            for store_id, revenue in sorted(revenue_by_store.items(), key=lambda x: x[1], reverse=True)
        ],
        "daily_trend": [
            {"date": date, "revenue": round(revenue, 2), "transactions": daily_transactions[date]}
            for date, revenue in sorted(daily_revenue.items())
        ][-30:],  # Last 30 days
        "top_customers": [
            {"customer_id": customer_id, "total_spent": round(spent, 2), "transactions": customer_transactions[customer_id]}
            for customer_id, spent in top_customers
        ],
        "payment_methods": [
            {"method": method, "count": count}
            for method, count in sorted(payment_methods.items(), key=lambda x: x[1], reverse=True)
        ],
        "hourly_distribution": [
            {"hour": hour, "transactions": count}
            for hour, count in sorted(hourly_distribution.items())
        ]
    }

# Load fidelity data
FIDELITY_DATA = {}

def clean_json_string(content: str) -> str:
    """Clean malformed JSON content"""
    import re
    
    # Fix common issues in the JSON
    # Replace invalid escape sequences like "\\" with empty string  
    content = re.sub(r':"\\+"', ':""', content)
    
    # Fix any other malformed escape sequences
    content = re.sub(r'\\+(?!")', '', content)
    
    return content

def parse_json_tolerant(file_path: str, encoding: str = 'latin-1') -> list:
    """Parse JSON file with tolerance for malformed records"""
    records = []
    skipped_records = 0
    
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            content = f.read()
            
        # Clean the content first
        content = clean_json_string(content)
        
        # Try to parse the complete JSON
        try:
            data = json.loads(content)
            if isinstance(data, list):
                for record in data:
                    if isinstance(record, dict) and 'card_number' in record:
                        records.append(record)
                    else:
                        skipped_records += 1
            print(f"Successfully parsed complete JSON file")
            
        except json.JSONDecodeError as e:
            # If complete parsing fails, try chunked parsing
            print(f"Complete JSON parsing failed: {e}")
            print("Attempting chunked parsing...")
            
            # Remove the outer brackets and split by records
            content = content.strip()
            if content.startswith('[') and content.endswith(']'):
                content = content[1:-1]  # Remove outer brackets
            
            # Split by record boundaries ("},{"
            record_strings = content.split('},{')
            
            for i, record_str in enumerate(record_strings):
                try:
                    # Add back the braces
                    if i == 0:
                        record_str = record_str + '}'
                    elif i == len(record_strings) - 1:
                        record_str = '{' + record_str
                    else:
                        record_str = '{' + record_str + '}'
                    
                    record = json.loads(record_str)
                    if 'card_number' in record:
                        records.append(record)
                    else:
                        skipped_records += 1
                        
                except json.JSONDecodeError:
                    skipped_records += 1
                    continue
                except Exception:
                    skipped_records += 1
                    continue
    
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
    
    print(f"Loaded {len(records)} records, skipped {skipped_records} malformed records")
    return records

async def load_fidelity_data():
    """Load fidelity data from JSON file"""
    global FIDELITY_DATA
    try:
        # Start with sample test data
        FIDELITY_DATA = {
            "2013000002194": {
                "card_number": "2013000002194",
                "stato_tes": "01",
                "nome": "GIUSEPPE",
                "cognome": "ROSSI",
                "sesso": "M", 
                "indirizzo": "VIA ROMA 123",
                "cap": "70043",
                "localita": "MONOPOLI",
                "provincia": "BA",
                "n_telefono": "0804567890",
                "email": "giuseppe.rossi@email.it",
                "data_nas": "19751225",
                "data_creazione": "20130101",
                "data_ult_sc": "20241201", 
                "prog_spesa": "2850.75",
                "bollini": "125",
                "dati_pers": "1",
                "dati_pubb": "1", 
                "profilazione": "1",
                "marketing": "1",
                "coniugato": "1",
                "data_coniugato": "20001015",
                "numero_figli": "2",
                "data_figlio_1": "20051203",
                "data_figlio_2": "20081118",
                "animali_1": "1",
                "animali_2": "0",
                "lattosio": "0",
                "glutine": "1", 
                "nichel": "0",
                "celiachia": "0",
                "altro_intolleranza": "",
                "fattura": "0",
                "ragione_sociale": "",
                "negozio": "IMAGROSS 1"
            },
            "2020000028284": {
                "card_number": "2020000028284",
                "stato_tes": "01",
                "nome": "MARIA",
                "cognome": "VERDI",
                "sesso": "F",
                "indirizzo": "CORSO ITALIA 45",
                "cap": "70042",
                "localita": "MOLA DI BARI",
                "provincia": "BA", 
                "n_telefono": "3331234567",
                "email": "maria.verdi@gmail.com",
                "data_nas": "19820314",
                "data_creazione": "20200630",
                "data_ult_sc": "20241128",
                "prog_spesa": "1450.20",
                "bollini": "78",
                "dati_pers": "1",
                "dati_pubb": "0",
                "profilazione": "",
                "marketing": "1", 
                "coniugato": "0",
                "data_coniugato": "",
                "numero_figli": "0",
                "animali_1": "0",
                "animali_2": "1",
                "lattosio": "1",
                "glutine": "0",
                "nichel": "1",
                "celiachia": "0",
                "altro_intolleranza": "NOCI",
                "fattura": "1",
                "ragione_sociale": "STUDIO VERDI SRL",
                "negozio": "IMAGROSS 2"
            },
            "2018000015632": {
                "card_number": "2018000015632", 
                "stato_tes": "01",
                "nome": "ANTONIO",
                "cognome": "BIANCHI",
                "sesso": "M",
                "indirizzo": "VIA NAPOLI 78",
                "cap": "70044",
                "localita": "POLIGNANO A MARE",
                "provincia": "BA",
                "n_telefono": "3356789012", 
                "email": "antonio.bianchi@libero.it",
                "data_nas": "19601105",
                "data_creazione": "20180315",
                "data_ult_sc": "20241025",
                "prog_spesa": "3200.80",
                "bollini": "156",
                "dati_pers": "1",
                "dati_pubb": "1",
                "profilazione": "0",
                "marketing": "0",
                "coniugato": "1", 
                "data_coniugato": "19850620",
                "numero_figli": "3",
                "data_figlio_1": "19881212",
                "data_figlio_2": "19910303",
                "data_figlio_3": "19940715",
                "animali_1": "1", 
                "animali_2": "1",
                "lattosio": "0",
                "glutine": "0",
                "nichel": "0", 
                "celiachia": "1",
                "altro_intolleranza": "",
                "fattura": "0",
                "ragione_sociale": "",
                "negozio": "IMAGROSS 1"
            }
        }
        
        # Now try to load the complete fidelity JSON with robust parsing
        try:
            print("Loading fidelity data from complete JSON file...")
            json_records = parse_json_tolerant('/app/fidelity_complete.json')
            
            # Convert records to the FIDELITY_DATA format
            for record in json_records:
                card_number = record.get('card_number', '').strip()
                if card_number:
                    FIDELITY_DATA[card_number] = record
                    
            print(f"Successfully integrated {len(json_records)} records from fidelity JSON")
            
        except Exception as big_json_error:
            print(f"Could not load big JSON: {big_json_error}")
        
        print(f"Total loaded fidelity records: {len(FIDELITY_DATA)}")
        print(f"Sample card numbers: {list(FIDELITY_DATA.keys())[:10]}")
        
    except Exception as e:
        print(f"Error loading fidelity data: {e}")
        FIDELITY_DATA = {}

def safe_float_convert(value: str, default: float = 0.0) -> float:
    """Safely convert string to float, handling European decimal format"""
    if not value or value.strip() == "":
        return default
    try:
        # Replace comma with dot for European decimal format
        value = str(value).strip().replace(',', '.')
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_int_convert(value: str, default: int = 0) -> int:
    """Safely convert string to int"""
    if not value or value.strip() == "":
        return default
    try:
        # Handle float strings first (like "0.0")
        value = str(value).strip().replace(',', '.')
        return int(float(value))
    except (ValueError, TypeError):
        return default

def get_fidelity_user_data(card_number: str) -> dict:
    """Get user data from fidelity JSON by card number"""
    if card_number in FIDELITY_DATA:
        raw_data = FIDELITY_DATA[card_number]
        
        # Map JSON fields to our User model
        return {
            "nome": raw_data.get("nome", "").strip(),
            "cognome": raw_data.get("cognome", "").strip(),
            "sesso": "F" if raw_data.get("sesso", "").upper() == "F" else "M",
            "email": raw_data.get("email", "").strip(),
            "telefono": raw_data.get("n_telefono", "").strip(),
            "localita": raw_data.get("localita", "").strip(),
            "indirizzo": raw_data.get("indirizzo", "").strip(),
            "cap": raw_data.get("cap", "").strip(),
            "provincia": raw_data.get("provincia", "").strip(),
            "data_nascita": raw_data.get("data_nas", "").strip(),
            "data_creazione": raw_data.get("data_creazione", "").strip(),
            "data_ultima_spesa": raw_data.get("data_ult_sc", "").strip(),
            "progressivo_spesa": safe_float_convert(raw_data.get("prog_spesa", "0")),
            "bollini": safe_int_convert(raw_data.get("bollini", "0")),
            "consenso_dati_personali": raw_data.get("dati_pers", "") == "1",
            "consenso_dati_pubblicitari": raw_data.get("dati_pubb", "") == "1",
            "consenso_profilazione": raw_data.get("profilazione", "") == "1" if raw_data.get("profilazione", "") != "" else None,
            "consenso_marketing": raw_data.get("marketing", "") == "1" if raw_data.get("marketing", "") != "" else None,
            "coniugato": raw_data.get("coniugato", "") == "1" if raw_data.get("coniugato", "") != "" else None,
            "data_matrimonio": raw_data.get("data_coniugato", "").strip(),
            "numero_figli": safe_int_convert(raw_data.get("numero_figli", "0")),
            "data_figlio_1": raw_data.get("data_figlio_1", "").strip(),
            "data_figlio_2": raw_data.get("data_figlio_2", "").strip(),
            "data_figlio_3": raw_data.get("data_figlio_3", "").strip(),
            "data_figlio_4": raw_data.get("data_figlio_4", "").strip(),
            "data_figlio_5": raw_data.get("data_figlio_5", "").strip(),
            "animali_cani": raw_data.get("animali_1", "") == "1",
            "animali_gatti": raw_data.get("animali_2", "") == "1",
            "intolleranza_lattosio": raw_data.get("lattosio", "") == "1",
            "intolleranza_glutine": raw_data.get("glutine", "") == "1",
            "intolleranza_nichel": raw_data.get("nichel", "") == "1",
            "celiachia": raw_data.get("celiachia", "") == "1",
            "altra_intolleranza": raw_data.get("altro_intolleranza", "").strip(),
            "richiede_fattura": raw_data.get("fattura", "") == "1",
            "ragione_sociale": raw_data.get("ragione_sociale", "").strip(),
            "stato_tessera": raw_data.get("stato_tes", "01"),
            "negozio": raw_data.get("negozio", "").strip()
        }
    return None
async def init_super_admin():
    existing_admin = await db.admins.find_one({"role": "super_admin"})
    if not existing_admin:
        super_admin = AdminUser(
            username="superadmin",
            email="superadmin@imagross.it",
            password_hash=hash_password("ImaGross2024!"),
            role=UserRole.SUPER_ADMIN,
            full_name="Super Administrator"
        )
        await db.admins.insert_one(super_admin.dict())
        print("Super admin created - Username: superadmin, Password: ImaGross2024!")

# Routes

# Public Routes
@api_router.get("/")
async def root():
    return {"message": "ImaGross Loyalty API v2.0 - Scalable System"}

@api_router.get("/debug/fidelity")
async def debug_fidelity():
    """Debug endpoint to check fidelity data"""
    return {
        "loaded_records": len(FIDELITY_DATA),
        "available_cards": list(FIDELITY_DATA.keys()),
        "sample_data": next(iter(FIDELITY_DATA.values())) if FIDELITY_DATA else None
    }

@api_router.get("/qr/{qr_code}")
async def get_qr_info(qr_code: str):
    """Get information about a QR code (store and cashier info)"""
    cashier = await db.cashiers.find_one({"qr_code": qr_code})
    if not cashier:
        raise HTTPException(status_code=404, detail="QR code not found")
    
    # Remove MongoDB _id field to avoid serialization issues
    if "_id" in cashier:
        del cashier["_id"]
    
    store = await db.stores.find_one({"id": cashier["store_id"]})
    if store and "_id" in store:
        del store["_id"]
    
    return {
        "store": store,
        "cashier": cashier,
        "registration_url": f"/register?qr={qr_code}"
    }

@api_router.post("/admin/check-tessera")
async def admin_check_tessera(tessera_data: TesseraCheck, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Admin endpoint to check tessera fisica and return user data"""
    # Verify admin token
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
        if payload.get("role") != "super_admin":
            raise HTTPException(status_code=403, detail="Accesso negato")
    except:
        raise HTTPException(status_code=401, detail="Token non valido")
    
    try:
        # Check in current users first
        user = await db.users.find_one({"tessera_fisica": tessera_data.tessera_fisica})
        
        if user:
            if user.get("migrated", False):
                return {
                    "found": True,
                    "migrated": True,
                    "message": "Tessera già migrata",
                    "user_data": {
                        "nome": user.get("nome", ""),
                        "cognome": user.get("cognome", ""),
                        "sesso": user.get("sesso", "M"),
                        "email": user.get("email", ""),
                        "telefono": user.get("telefono", ""),
                        "localita": user.get("localita", ""),
                        "indirizzo": user.get("indirizzo", ""),
                        "provincia": user.get("provincia", "")
                    }
                }
            else:
                # User exists but not migrated
                return {
                    "found": True,
                    "migrated": False,
                    "user_data": {
                        "nome": user.get("nome", ""),
                        "cognome": user.get("cognome", ""),
                        "sesso": user.get("sesso", "M"),
                        "email": user.get("email", ""),
                        "telefono": user.get("telefono", ""),
                        "localita": user.get("localita", ""),
                        "indirizzo": user.get("indirizzo", ""),
                        "provincia": user.get("provincia", "")
                    }
                }
        
        # Check in fidelity data
        fidelity_data = get_fidelity_user_data(tessera_data.tessera_fisica)
        
        if fidelity_data:
            return {
                "found": True,
                "migrated": False,
                "user_data": fidelity_data,
                "source": "fidelity_json"
            }
        
        return {
            "found": False,
            "migrated": False,
            "message": "Tessera non trovata"
        }
        
    except Exception as e:
        print(f"Error checking tessera (admin): {e}")
        return {
            "found": False,
            "migrated": False,
            "message": "Errore durante la verifica"
        }

@api_router.post("/check-tessera")
async def check_tessera(tessera_data: TesseraCheck):
    """Check if tessera fisica exists and return user data"""
    try:
        # Check in current users first
        user = await db.users.find_one({"tessera_fisica": tessera_data.tessera_fisica})
        
        if user:
            if user.get("migrated", False):
                return {
                    "found": True,
                    "migrated": True,
                    "message": "Tessera già migrata"
                }
            else:
                # User exists but not migrated
                return {
                    "found": True,
                    "migrated": False,
                    "user_data": {
                        "nome": user.get("nome", ""),
                        "cognome": user.get("cognome", ""),
                        "sesso": user.get("sesso", "M"),
                        "email": user.get("email", ""),
                        "telefono": user.get("telefono", ""),
                        "localita": user.get("localita", ""),
                        "indirizzo": user.get("indirizzo", ""),
                        "provincia": user.get("provincia", "")
                    }
                }
        
        # Check in fidelity data
        fidelity_data = get_fidelity_user_data(tessera_data.tessera_fisica)
        
        if fidelity_data:
            return {
                "found": True,
                "migrated": False,
                "user_data": fidelity_data,
                "source": "fidelity_json"
            }
        
        return {
            "found": False,
            "migrated": False,
            "message": "Tessera non trovata"
        }
        
    except Exception as e:
        print(f"Error checking tessera: {e}")
        return {
            "found": False,
            "migrated": False,
            "message": "Errore durante la verifica"
        }

# User Authentication Routes
@api_router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email già registrata")
    
    # Generate tessera fisica if not provided (new registration without existing tessera)
    tessera_fisica = user_data.tessera_fisica
    if not tessera_fisica:
        # Generate new tessera number (format: 2024 + timestamp)
        import time
        tessera_fisica = f"2024{int(time.time())}"
        
        # Ensure uniqueness
        while await db.users.find_one({"tessera_fisica": tessera_fisica}):
            tessera_fisica = f"2024{int(time.time())}{str(uuid.uuid4())[:4]}"
    else:
        # Check if tessera fisica already exists
        existing_tessera = await db.users.find_one({"tessera_fisica": tessera_fisica})
        if existing_tessera:
            raise HTTPException(status_code=400, detail="Tessera fisica già registrata")
    
    # If registering via QR code, validate cashier
    store_name = None
    cashier_name = None
    if user_data.store_id and user_data.cashier_id:
        store = await db.stores.find_one({"id": user_data.store_id})
        cashier = await db.cashiers.find_one({"id": user_data.cashier_id})
        if store:
            store_name = store["name"]
        if cashier:
            cashier_name = cashier["name"]
            # Update cashier registration count
            await db.cashiers.update_one(
                {"id": user_data.cashier_id},
                {"$inc": {"total_registrations": 1}}
            )
    
    # Create user with all provided data
    user_dict = user_data.dict()
    user_dict["tessera_fisica"] = tessera_fisica
    user_dict["password_hash"] = hash_password(user_data.password)
    user_dict["migrated"] = bool(user_data.tessera_fisica)  # Mark as migrated if tessera was provided
    del user_dict["password"]
    
    # Set default values for None fields
    for field in user_dict:
        if user_dict[field] is None and field in ["bollini", "numero_figli", "progressivo_spesa"]:
            if field == "progressivo_spesa":
                user_dict[field] = 0.0
            else:
                user_dict[field] = 0
    
    user = User(**user_dict)
    await db.users.insert_one(user.dict())
    
    # Generate QR code
    qr_code = generate_qr_code(user.tessera_digitale)
    
    return UserResponse(
        id=user.id,
        nome=user.nome,
        cognome=user.cognome,
        sesso=user.sesso,
        email=user.email,
        telefono=user.telefono,
        localita=user.localita,
        tessera_fisica=user.tessera_fisica,
        tessera_digitale=user.tessera_digitale,
        punti=user.punti,
        created_at=user.created_at,
        qr_code=qr_code,
        store_name=store_name,
        cashier_name=cashier_name
    )

@api_router.post("/login", response_model=LoginResponse)
async def login(login_data: UserLogin):
    user = await db.users.find_one({"email": login_data.email})
    if not user or not verify_password(login_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Credenziali non valide")
    
    if not user["active"]:
        raise HTTPException(status_code=401, detail="Account disattivato")
    
    access_token = create_access_token(data={"sub": user["id"], "type": "user"})
    qr_code = generate_qr_code(user["tessera_digitale"])
    
    # Get store and cashier names
    store_name = None
    cashier_name = None
    if user.get("store_id"):
        store = await db.stores.find_one({"id": user["store_id"]})
        if store:
            store_name = store["name"]
    if user.get("cashier_id"):
        cashier = await db.cashiers.find_one({"id": user["cashier_id"]})
        if cashier:
            cashier_name = cashier["name"]
    
    user_response = UserResponse(
        id=user["id"],
        nome=user["nome"],
        cognome=user["cognome"],
        sesso=user["sesso"],
        email=user["email"],
        telefono=user["telefono"],
        localita=user["localita"],
        tessera_fisica=user["tessera_fisica"],
        tessera_digitale=user["tessera_digitale"],
        punti=user["punti"],
        created_at=user["created_at"],
        qr_code=qr_code,
        store_name=store_name,
        cashier_name=cashier_name
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )

@api_router.get("/profile", response_model=UserResponse)
async def get_profile(current_user = Depends(get_current_user)):
    if current_user["type"] != "user":
        raise HTTPException(status_code=403, detail="User access required")
    
    user = current_user["data"]
    qr_code = generate_qr_code(user.tessera_digitale)
    
    # Get store and cashier names
    store_name = None
    cashier_name = None
    if user.store_id:
        store = await db.stores.find_one({"id": user.store_id})
        if store:
            store_name = store["name"]
    if user.cashier_id:
        cashier = await db.cashiers.find_one({"id": user.cashier_id})
        if cashier:
            cashier_name = cashier["name"]
    
    return UserResponse(
        id=user.id,
        nome=user.nome,
        cognome=user.cognome,
        sesso=user.sesso,
        email=user.email,
        telefono=user.telefono,
        localita=user.localita,
        tessera_fisica=user.tessera_fisica,
        tessera_digitale=user.tessera_digitale,
        punti=user.punti,
        created_at=user.created_at,
        qr_code=qr_code,
        store_name=store_name,
        cashier_name=cashier_name
    )

@api_router.post("/add-points/{points}")
async def add_points(points: int, current_user = Depends(get_current_user)):
    """Add points to user account"""
    if current_user["type"] != "user":
        raise HTTPException(status_code=403, detail="User access required")
    
    user = current_user["data"]
    
    # Update user points
    new_points = user.punti + points
    await db.users.update_one(
        {"id": user.id},
        {"$set": {"punti": new_points}}
    )
    
    return {
        "message": f"Aggiunti {points} punti",
        "punti_totali": new_points
    }

# Admin Authentication Routes
@api_router.post("/admin/login", response_model=AdminLoginResponse)
async def admin_login(login_data: AdminLogin):
    admin = await db.admins.find_one({"username": login_data.username})
    if not admin or not verify_password(login_data.password, admin["password_hash"]):
        raise HTTPException(status_code=401, detail="Credenziali non valide")
    
    if not admin["active"]:
        raise HTTPException(status_code=401, detail="Account disattivato")
    
    access_token = create_access_token(data={"sub": admin["id"], "type": "admin", "role": admin["role"]})
    
    admin_data = {
        "id": admin["id"],
        "username": admin["username"],
        "email": admin["email"],
        "role": admin["role"],
        "full_name": admin["full_name"],
        "created_at": admin["created_at"]
    }
    
    return AdminLoginResponse(
        access_token=access_token,
        token_type="bearer",
        admin=admin_data
    )

# Super Admin Routes
@api_router.post("/admin/create", response_model=dict)
async def create_admin(admin_data: AdminUserCreate, current_admin = Depends(get_super_admin)):
    # Check if admin already exists
    existing_admin = await db.admins.find_one({"$or": [
        {"username": admin_data.username},
        {"email": admin_data.email}
    ]})
    if existing_admin:
        raise HTTPException(status_code=400, detail="Admin già esistente")
    
    # Create admin
    admin_dict = admin_data.dict()
    admin_dict["password_hash"] = hash_password(admin_data.password)
    del admin_dict["password"]
    
    admin = AdminUser(**admin_dict)
    await db.admins.insert_one(admin.dict())
    
    return {"message": "Admin creato con successo", "admin_id": admin.id}

# Store Management Routes
@api_router.post("/admin/stores", response_model=Store)
async def create_store(store_data: StoreCreate, current_admin = Depends(get_current_admin)):
    # Check if store code already exists
    existing_store = await db.stores.find_one({"code": store_data.code})
    if existing_store:
        raise HTTPException(status_code=400, detail="Codice supermercato già esistente")
    
    store = Store(**store_data.dict())
    await db.stores.insert_one(store.dict())
    
    return store

@api_router.get("/admin/stores", response_model=List[Store])
async def get_stores(current_admin = Depends(get_current_admin)):
    stores = await db.stores.find().to_list(1000)
    return [Store(**store) for store in stores]

@api_router.put("/admin/stores/{store_id}", response_model=Store)
async def update_store(store_id: str, store_data: StoreCreate, current_admin = Depends(get_current_admin)):
    store = await db.stores.find_one({"id": store_id})
    if not store:
        raise HTTPException(status_code=404, detail="Supermercato non trovato")
    
    update_data = store_data.dict()
    update_data["updated_at"] = datetime.utcnow()
    
    await db.stores.update_one({"id": store_id}, {"$set": update_data})
    updated_store = await db.stores.find_one({"id": store_id})
    
    return Store(**updated_store)

# Cashier Management Routes
@api_router.post("/admin/cashiers", response_model=Cashier)
async def create_cashier(cashier_data: CashierCreate, current_admin = Depends(get_current_admin)):
    # Verify store exists
    store = await db.stores.find_one({"id": cashier_data.store_id})
    if not store:
        raise HTTPException(status_code=404, detail="Supermercato non trovato")
    
    # Check if cashier number already exists for this store
    existing_cashier = await db.cashiers.find_one({
        "store_id": cashier_data.store_id,
        "cashier_number": cashier_data.cashier_number
    })
    if existing_cashier:
        raise HTTPException(status_code=400, detail="Numero cassa già esistente per questo supermercato")
    
    # Generate QR code data and image
    qr_data = f"{store['code']}-CASSA{cashier_data.cashier_number}"
    # Generate full URL for QR code
    base_url = "https://6a0a1851-a8c5-4e5a-a696-0e8a2481171c.preview.emergentagent.com"
    qr_url = f"{base_url}/register?qr={qr_data}"
    qr_image = generate_qr_code(qr_url)
    
    cashier = Cashier(
        store_id=cashier_data.store_id,
        cashier_number=cashier_data.cashier_number,
        name=cashier_data.name,
        qr_code=qr_data,
        qr_code_image=qr_image
    )
    
    await db.cashiers.insert_one(cashier.dict())
    
    # Update store total cashiers count
    await db.stores.update_one(
        {"id": cashier_data.store_id},
        {"$inc": {"total_cashiers": 1}}
    )
    
    return cashier

@api_router.get("/admin/stores/{store_id}/cashiers", response_model=List[Cashier])
async def get_store_cashiers(store_id: str, current_admin = Depends(get_current_admin)):
    cashiers = await db.cashiers.find({"store_id": store_id}).to_list(1000)
    return [Cashier(**cashier) for cashier in cashiers]

@api_router.get("/admin/cashiers", response_model=List[dict])
async def get_all_cashiers(current_admin = Depends(get_current_admin)):
    cashiers = await db.cashiers.find().to_list(1000)
    result = []
    
    for cashier in cashiers:
        # Remove MongoDB _id field to avoid serialization issues
        if "_id" in cashier:
            del cashier["_id"]
        
        store = await db.stores.find_one({"id": cashier["store_id"]})
        result.append({
            **cashier,
            "store_name": store["name"] if store else "Unknown"
        })
    
    return result

# User Management Routes
@api_router.get("/admin/fidelity-users")
async def get_fidelity_users(
    page: int = 1,
    limit: int = 50,
    search: str = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get paginated fidelity users data"""
    # Verify admin token
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
        if payload.get("role") != "super_admin":
            raise HTTPException(status_code=403, detail="Accesso negato")
    except:
        raise HTTPException(status_code=401, detail="Token non valido")
    
    try:
        # Convert FIDELITY_DATA to list of users
        all_users = []
        for card_number, user_data in FIDELITY_DATA.items():
            user_record = {
                "tessera_fisica": card_number,
                "nome": user_data.get("nome", "").strip(),
                "cognome": user_data.get("cognome", "").strip(),
                "email": user_data.get("email", "").strip(),
                "telefono": user_data.get("n_telefono", "").strip(),
                "localita": user_data.get("localita", "").strip(),
                "indirizzo": user_data.get("indirizzo", "").strip(),
                "provincia": user_data.get("provincia", "").strip(),
                "sesso": user_data.get("sesso", "M"),
                "data_nascita": user_data.get("data_nas", "").strip(),
                "data_creazione": user_data.get("data_creazione", "").strip(),
                "progressivo_spesa": safe_float_convert(user_data.get("prog_spesa", "0")),
                "bollini": safe_int_convert(user_data.get("bollini", "0")),
                "negozio": user_data.get("negozio", "").strip(),
                "stato_tessera": user_data.get("stato_tes", "").strip(),
                "source": "fidelity_json"
            }
            all_users.append(user_record)
        
        # Apply search filter if provided
        if search:
            search_lower = search.lower()
            all_users = [
                user for user in all_users 
                if (search_lower in user["tessera_fisica"].lower() or
                    search_lower in user["nome"].lower() or
                    search_lower in user["cognome"].lower() or
                    search_lower in user["email"].lower() or
                    search_lower in user["telefono"].lower())
            ]
        
        # Sort by progressivo_spesa descending
        all_users.sort(key=lambda x: x["progressivo_spesa"], reverse=True)
        
        # Pagination
        total = len(all_users)
        start = (page - 1) * limit
        end = start + limit
        paginated_users = all_users[start:end]
        
        return {
            "users": paginated_users,
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit,
            "has_next": end < total,
            "has_prev": page > 1
        }
        
    except Exception as e:
        print(f"Error getting fidelity users: {e}")
        raise HTTPException(status_code=500, detail="Errore nel recupero degli utenti fidelity")

@api_router.get("/admin/users", response_model=List[dict])
async def get_all_users(current_admin = Depends(get_current_admin)):
    users = await db.users.find().to_list(1000)
    result = []
    
    for user in users:
        if "_id" in user:
            del user["_id"]
        
        # Get store name if available
        store_name = None
        if user.get("store_id"):
            store = await db.stores.find_one({"id": user["store_id"]})
            if store:
                store_name = store["name"]
        
        result.append({
            **user,
            "store_name": store_name
        })
    
    return result

# Statistics and Analytics Routes
@api_router.get("/admin/stats/dashboard")
async def get_dashboard_stats(current_admin = Depends(get_current_admin)):
    total_users = await db.users.count_documents({})
    total_stores = await db.stores.count_documents({})
    total_cashiers = await db.cashiers.count_documents({})
    total_transactions = await db.transactions.count_documents({})
    
    # Recent registrations (last 7 days)
    from datetime import timedelta
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_registrations = await db.users.count_documents({
        "created_at": {"$gte": week_ago}
    })
    
    # Total points distributed
    pipeline = [
        {"$group": {"_id": None, "total_points": {"$sum": "$punti"}}}
    ]
    points_result = await db.users.aggregate(pipeline).to_list(1)
    total_points = points_result[0]["total_points"] if points_result else 0
    
    return {
        "total_users": total_users,
        "total_stores": total_stores,
        "total_cashiers": total_cashiers,
        "total_transactions": total_transactions,
        "recent_registrations": recent_registrations,
        "total_points_distributed": total_points
    }

@api_router.get("/admin/analytics")
async def get_admin_analytics(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get comprehensive analytics for admin dashboard"""
    # Verify admin token
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
        if payload.get("role") != "super_admin":
            raise HTTPException(status_code=403, detail="Accesso negato")
    except:
        raise HTTPException(status_code=401, detail="Token non valido")
    
    try:
        analytics = get_dashboard_analytics()
        return analytics
    except Exception as e:
        print(f"Error getting analytics: {e}")
        raise HTTPException(status_code=500, detail="Errore nel recupero delle analytics")

@api_router.get("/admin/scontrini")
async def get_scontrini_data(
    page: int = 1,
    limit: int = 50,
    store_id: str = None,
    customer_id: str = None,
    date_from: str = None,
    date_to: str = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get paginated scontrini data with filters"""
    # Verify admin token
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
        if payload.get("role") != "super_admin":
            raise HTTPException(status_code=403, detail="Accesso negato")
    except:
        raise HTTPException(status_code=401, detail="Token non valido")
    
    try:
        # Apply filters
        filtered_data = SCONTRINI_DATA.copy()
        
        if store_id:
            filtered_data = [s for s in filtered_data if s.get('DITTA') == store_id]
        
        if customer_id:
            filtered_data = [s for s in filtered_data if s.get('CODICE_CLIENTE') == customer_id]
        
        if date_from:
            filtered_data = [s for s in filtered_data if s.get('DATA_SCONTRINO', '') >= date_from]
        
        if date_to:
            filtered_data = [s for s in filtered_data if s.get('DATA_SCONTRINO', '') <= date_to]
        
        # Pagination
        total = len(filtered_data)
        start = (page - 1) * limit
        end = start + limit
        paginated_data = filtered_data[start:end]
        
        return {
            "scontrini": paginated_data,
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit,
            "has_next": end < total,
            "has_prev": page > 1
        }
        
    except Exception as e:
        print(f"Error getting scontrini: {e}")
        raise HTTPException(status_code=500, detail="Errore nel recupero degli scontrini")

@api_router.get("/admin/stats/stores")
async def get_stores_stats(current_admin = Depends(get_current_admin)):
    stores = await db.stores.find().to_list(1000)
    result = []
    
    for store in stores:
        # Remove MongoDB _id field to avoid serialization issues
        if "_id" in store:
            del store["_id"]
            
        users_count = await db.users.count_documents({"store_id": store["id"]})
        cashiers_count = await db.cashiers.count_documents({"store_id": store["id"]})
        
        result.append({
            **store,
            "users_registered": users_count,
            "active_cashiers": cashiers_count
        })
    
    return result

# Data Import Routes
# Data Import Routes
@api_router.post("/admin/regenerate-qr-codes")
async def regenerate_all_qr_codes(current_admin = Depends(get_current_admin)):
    """Regenerate all QR codes with full URLs"""
    try:
        base_url = "https://6a0a1851-a8c5-4e5a-a696-0e8a2481171c.preview.emergentagent.com"
        
        cashiers = await db.cashiers.find().to_list(1000)
        updated_count = 0
        
        for cashier in cashiers:
            # Get store info
            store = await db.stores.find_one({"id": cashier["store_id"]})
            if store:
                # Generate new QR with full URL
                qr_data = f"{store['code']}-CASSA{cashier['cashier_number']}"
                qr_url = f"{base_url}/register?qr={qr_data}"
                qr_image = generate_qr_code(qr_url)
                
                # Update cashier record
                await db.cashiers.update_one(
                    {"id": cashier["id"]},
                    {"$set": {"qr_code_image": qr_image}}
                )
                updated_count += 1
        
        return {
            "message": f"Rigenerati {updated_count} QR codes con URL completo",
            "total_cashiers": len(cashiers),
            "updated": updated_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Errore rigenerazione QR: {str(e)}")

@api_router.post("/admin/regenerate-qr/{cashier_id}")
async def regenerate_single_qr_code(cashier_id: str, current_admin = Depends(get_current_admin)):
    """Regenerate single QR code with full URL"""
    try:
        base_url = "https://6a0a1851-a8c5-4e5a-a696-0e8a2481171c.preview.emergentagent.com"
        
        # Get cashier
        cashier = await db.cashiers.find_one({"id": cashier_id})
        if not cashier:
            raise HTTPException(status_code=404, detail="Cassa non trovata")
        
        # Get store info
        store = await db.stores.find_one({"id": cashier["store_id"]})
        if not store:
            raise HTTPException(status_code=404, detail="Supermercato non trovato")
        
        # Generate new QR with full URL
        qr_data = f"{store['code']}-CASSA{cashier['cashier_number']}"
        qr_url = f"{base_url}/register?qr={qr_data}"
        qr_image = generate_qr_code(qr_url)
        
        # Update cashier record
        await db.cashiers.update_one(
            {"id": cashier_id},
            {"$set": {"qr_code_image": qr_image}}
        )
        
        return {
            "message": "QR code rigenerato con successo",
            "cashier_id": cashier_id,
            "qr_data": qr_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Errore rigenerazione QR: {str(e)}")

@api_router.put("/admin/users/{user_id}")
async def update_user(user_id: str, user_data: dict, current_admin = Depends(get_current_admin)):
    """Update user information"""
    try:
        # Get existing user
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="Utente non trovato")
        
        # Prepare update data - expanded fields
        update_data = {}
        allowed_fields = [
            "nome", "cognome", "email", "telefono", "localita", "punti", "active",
            "indirizzo", "cap", "provincia", "data_nascita", "newsletter",
            "bollini", "progressivo_spesa", "consenso_dati_personali", 
            "consenso_dati_pubblicitari", "consenso_profilazione", "consenso_marketing",
            "coniugato", "numero_figli", "data_matrimonio", "data_figlio_1", "data_figlio_2",
            "data_figlio_3", "data_figlio_4", "data_figlio_5", "animali_cani", "animali_gatti",
            "intolleranza_lattosio", "intolleranza_glutine", "intolleranza_nichel", 
            "celiachia", "altra_intolleranza", "richiede_fattura", "ragione_sociale"
        ]
        
        for field in allowed_fields:
            if field in user_data:
                update_data[field] = user_data[field]
        
        # Add update timestamp
        update_data["updated_at"] = datetime.utcnow()
        
        # Update user
        await db.users.update_one(
            {"id": user_id},
            {"$set": update_data}
        )
        
        # Get updated user
        updated_user = await db.users.find_one({"id": user_id})
        if "_id" in updated_user:
            del updated_user["_id"]
        
        return {
            "message": "Utente aggiornato con successo",
            "user": updated_user
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Errore aggiornamento utente: {str(e)}")

@api_router.post("/admin/import/excel")
async def import_excel_data(
    file: UploadFile = File(...),
    data_type: str = "users",  # "users" or "transactions"
    current_admin = Depends(get_super_admin)
):
    try:
        contents = await file.read()
        
        # Save temporarily
        temp_path = f"/tmp/{file.filename}"
        with open(temp_path, "wb") as f:
            f.write(contents)
        
        # Read Excel
        df = pd.read_excel(temp_path)
        
        imported_count = 0
        
        if data_type == "users":
            for _, row in df.iterrows():
                # Map Excel columns to our user model
                user_data = {
                    "nome": str(row.get("nome", "")),
                    "cognome": str(row.get("cognome", "")),
                    "sesso": "M" if row.get("sesso") == "Maschio" else "F",
                    "email": str(row.get("email", f"import_{uuid.uuid4()}@imagross.it")),
                    "telefono": str(row.get("tel_cell", "")),
                    "localita": str(row.get("citta", "")),
                    "tessera_fisica": str(row.get("card_number", "")),
                    "password_hash": hash_password("imported123"),
                    "tessera_digitale": str(uuid.uuid4()),
                    "punti": 0,
                    "role": "user",
                    "active": True,
                    "indirizzo": str(row.get("indirizzo", "")),
                    "provincia": str(row.get("punto_provincia", "")),
                    "newsletter": bool(row.get("newsletter", 0)),
                    "numero_figli": int(row.get("numero_figli", 0)),
                    "created_at": datetime.utcnow()
                }
                
                # Check if user already exists
                existing = await db.users.find_one({
                    "$or": [
                        {"email": user_data["email"]},
                        {"tessera_fisica": user_data["tessera_fisica"]}
                    ]
                })
                
                if not existing and user_data["tessera_fisica"]:
                    user = User(**user_data)
                    await db.users.insert_one(user.dict())
                    imported_count += 1
        
        # Clean up
        os.remove(temp_path)
        
        return {
            "message": f"Importati {imported_count} record",
            "total_rows": len(df),
            "imported": imported_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Errore import: {str(e)}")

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

@app.on_event("startup")
async def startup_event():
    await init_super_admin()
    await load_fidelity_data()
    await load_scontrini_data()

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()