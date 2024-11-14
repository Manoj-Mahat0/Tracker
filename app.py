from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uvicorn

# Create FastAPI instance
app = FastAPI()

# MongoDB connection (replace with your MongoDB URI)
client = MongoClient("mongodb+srv://manojmahato08779:Sonix08779Mj@cluster0.xd2uh.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client['time_tracking_db']
users_collection = db['users']
collection = db['user_logs']

# Models
class UserCreate(BaseModel):
    username: str
    password: str
    name: str
    phone_number: str

class UserLogin(BaseModel):
    username: str
    password: str

class TimeLog(BaseModel):
    user_id: str
    study_start: str
    study_end: str
    work_start: str
    work_end: str

# Routes
@app.post("/signup")
async def signup(user: UserCreate):
    # Check if user already exists
    if users_collection.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="Username already exists")

    # Hash the password and store the user details
    hashed_password = generate_password_hash(user.password)
    users_collection.insert_one({
        "username": user.username,
        "password": hashed_password,
        "name": user.name,
        "phone_number": user.phone_number
    })

    return {"message": "User registered successfully!"}

@app.post("/login")
async def login(user: UserLogin):
    # Retrieve the user from the database
    db_user = users_collection.find_one({"username": user.username})
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if password matches
    if not check_password_hash(db_user['password'], user.password):
        raise HTTPException(status_code=401, detail="Invalid password")
    
    return {"message": "Login successful!"}

@app.post("/log-time")
async def log_time(time_log: TimeLog):
    try:
        # Parse datetime strings
        study_start_dt = datetime.strptime(time_log.study_start, "%Y-%m-%d %H:%M:%S")
        study_end_dt = datetime.strptime(time_log.study_end, "%Y-%m-%d %H:%M:%S")
        work_start_dt = datetime.strptime(time_log.work_start, "%Y-%m-%d %H:%M:%S")
        work_end_dt = datetime.strptime(time_log.work_end, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid datetime format")

    # Store the time log in the database
    log_entry = {
        "user_id": time_log.user_id,
        "study_start": study_start_dt,
        "study_end": study_end_dt,
        "work_start": work_start_dt,
        "work_end": work_end_dt,
        "timestamp": datetime.now()
    }
    collection.insert_one(log_entry)

    return {"message": "Time log added successfully!"}

@app.get("/get-logs")
async def get_logs(user_id: str):
    # Retrieve logs for the user
    logs = list(collection.find({"user_id": user_id}, {"_id": 0}))
    if not logs:
        raise HTTPException(status_code=404, detail="No logs found for the user")
    return logs

@app.get("/get-user-details/{username}")
async def get_user_details(username: str):
    # Retrieve the user details from the database
    db_user = users_collection.find_one({"username": username})
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Return user details (excluding the password)
    user_details = {
        "username": db_user["username"],
        "name": db_user["name"],
        "phone_number": db_user["phone_number"]
    }
    return user_details

# Main entry point
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
