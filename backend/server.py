from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
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

# Models
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
    created_at: datetime = Field(default_factory=datetime.utcnow)
    active: bool = True

class UserCreate(BaseModel):
    nome: str
    cognome: str
    sesso: Gender
    email: EmailStr
    telefono: str
    localita: str
    tessera_fisica: str
    password: str

class UserLogin(BaseModel):
    email: EmailStr
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

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

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

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = await db.users.find_one({"id": user_id})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        return User(**user)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Routes
@api_router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email già registrata")
    
    # Check if tessera fisica already exists
    existing_tessera = await db.users.find_one({"tessera_fisica": user_data.tessera_fisica})
    if existing_tessera:
        raise HTTPException(status_code=400, detail="Tessera fisica già registrata")
    
    # Create user
    user_dict = user_data.dict()
    user_dict["password_hash"] = hash_password(user_data.password)
    del user_dict["password"]
    
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
        qr_code=qr_code
    )

@api_router.post("/login", response_model=LoginResponse)
async def login(login_data: UserLogin):
    user = await db.users.find_one({"email": login_data.email})
    if not user or not verify_password(login_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Credenziali non valide")
    
    if not user["active"]:
        raise HTTPException(status_code=401, detail="Account disattivato")
    
    access_token = create_access_token(data={"sub": user["id"]})
    qr_code = generate_qr_code(user["tessera_digitale"])
    
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
        qr_code=qr_code
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )

@api_router.get("/profile", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    qr_code = generate_qr_code(current_user.tessera_digitale)
    
    return UserResponse(
        id=current_user.id,
        nome=current_user.nome,
        cognome=current_user.cognome,
        sesso=current_user.sesso,
        email=current_user.email,
        telefono=current_user.telefono,
        localita=current_user.localita,
        tessera_fisica=current_user.tessera_fisica,
        tessera_digitale=current_user.tessera_digitale,
        punti=current_user.punti,
        created_at=current_user.created_at,
        qr_code=qr_code
    )

@api_router.post("/add-points/{points}")
async def add_points(points: int, current_user: User = Depends(get_current_user)):
    await db.users.update_one(
        {"id": current_user.id},
        {"$inc": {"punti": points}}
    )
    return {"message": f"Aggiunti {points} punti", "punti_totali": current_user.punti + points}

@api_router.get("/")
async def root():
    return {"message": "ImaGross Loyalty API"}

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