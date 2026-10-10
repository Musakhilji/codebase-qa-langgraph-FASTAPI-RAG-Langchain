import os
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError, ExpiredSignatureError
from pwdlib import PasswordHash
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, JSON
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from app.agent import run
from dotenv import load_dotenv

load_dotenv()


# ---------- Database ----------
DATABASE_URL = os.getenv("DATA_BASE")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)


class history(Base):
    __tablename__ = "history"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)      
    query = Column(String)
    git_url = Column(String)
    msg = Column(JSON)             

Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------- Schema ----------
class UserCreate(BaseModel):
    username: str
    password: str


class msgrequest(BaseModel):
    query: str
    git_url: str


# ---------- Password ----------
pwd_context = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# ---------- Token ----------
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY is not set")
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def create_token(data: dict):
    data_to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    data_to_encode.update({"exp": expire})
    return jwt.encode(data_to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token has expired")
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")


# ---------- Current user ----------
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    payload = verify_token(token)
    username = payload.get("sub")

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    return user



app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Register ----------
@app.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Username already exists")

    new_user = User(
        username=user.username,
        password=hash_password(user.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User registered successfully"}


# ---------- Login ----------
@app.post("/login")
def login(data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()

    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid username or password")

    token = create_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}


# ---------- Me (sirf user info) ----------
@app.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "username": current_user.username}



@app.post("/ask")
def ask(
    body: msgrequest,                                  
    current_user: User = Depends(get_current_user),    
    db: Session = Depends(get_db),
):
    query = body.query
    git_url = body.git_url

    
    result = run(query, git_url)

    
    answer = result["messages"][-1]["content"]

    
    chat = [
        {"role": "human", "content": query},
        {"role": "ai", "content": answer},
    ]

    
    new_history = history(
        user_id=current_user.id,
        query=query,
        git_url=git_url,
        msg=chat,
    )
    db.add(new_history)
    db.commit()

    
    return {"human": query, "ai": answer}



@app.get("/history")
def get_history(
    git_url: str,
    current_user: User = Depends(get_current_user),    
    db: Session = Depends(get_db),
):
   
    rows = db.query(history).filter(
        history.user_id == current_user.id,
        history.git_url == git_url,
    ).all()

    all_chat = []
    for row in rows:
        all_chat.extend(row.msg)

    return all_chat

@app.delete("/delete_account")
def delete_acc(user_name:str,
             current_user:User=Depends(get_current_user),
             db:Session=Depends(get_db)):
 name=user_name
 user_to_dlt=db.query(User).filter(User.username==name).first()
 if not user_to_dlt :
     raise HTTPException(
         status_code=404,
         detail="user not found"
     )
 db.delete(user_to_dlt)
 db.commit() 
 return{
     "msg":"account has been deleted "
 }