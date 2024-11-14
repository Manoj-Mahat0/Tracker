from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
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
    username: str
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
    # Retrieve user from the database by username
    db_user = users_collection.find_one({"username": time_log.username})
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Parse datetime strings
    try:
        study_start_dt = datetime.strptime(time_log.study_start, "%Y-%m-%d %H:%M:%S")
        study_end_dt = datetime.strptime(time_log.study_end, "%Y-%m-%d %H:%M:%S")
        work_start_dt = datetime.strptime(time_log.work_start, "%Y-%m-%d %H:%M:%S")
        work_end_dt = datetime.strptime(time_log.work_end, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid datetime format")

    # Derive the date from study_start and store it for easy querying
    log_date = study_start_dt.date()

    # Create log entry
    log_entry = {
        "user_id": db_user["_id"],  # Store the user_id
        "username": time_log.username,  # Store the username
        "study_start": study_start_dt,
        "study_end": study_end_dt,
        "work_start": work_start_dt,
        "work_end": work_end_dt,
        "date": log_date,  # Store the date separately for querying
        "timestamp": datetime.now()
    }

    # Insert log entry into the database
    collection.insert_one(log_entry)

    return {"message": "Time log added successfully!"}

@app.get("/get-logs")
async def get_logs(username: str, date: str):
    # Parse the date from the request
    try:
        query_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    # Query the database for logs based on username and date
    logs_cursor = collection.find({
        "username": username,
        "date": query_date
    })

    logs_list = list(logs_cursor)  # Convert cursor to a list
    if not logs_list:
        raise HTTPException(status_code=404, detail="No logs found for the user on this date")

    # Prepare the logs in the desired format
    logs = [
        {
            "username": log["username"],
            "study_start": log["study_start"].strftime("%Y-%m-%d %H:%M:%S"),
            "study_end": log["study_end"].strftime("%Y-%m-%d %H:%M:%S"),
            "work_start": log["work_start"].strftime("%Y-%m-%d %H:%M:%S"),
            "work_end": log["work_end"].strftime("%Y-%m-%d %H:%M:%S")
        }
        for log in logs_list
    ]
    
    return {"logs": logs}

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
