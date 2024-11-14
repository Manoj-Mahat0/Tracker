from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Connect to MongoDB (replace with your MongoDB URI)
client = MongoClient("mongodb+srv://manojmahato08779:Sonix08779Mj@cluster0.xd2uh.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client['time_tracking_db']
collection = db['user_logs']
users_collection = db['users']

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    if users_collection.find_one({"username": username}):
        return jsonify({"error": "Username already exists"}), 400

    hashed_password = generate_password_hash(password)
    users_collection.insert_one({"username": username, "password": hashed_password})

    return jsonify({"message": "User registered successfully!"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    user = users_collection.find_one({"username": username})
    if user and check_password_hash(user['password'], password):
        return jsonify({"message": "Login successful!", "user_id": str(user['_id'])}), 200
    else:
        return jsonify({"error": "Invalid username or password"}), 401

@app.route('/log-time', methods=['POST'])
def log_time():
    data = request.get_json()
    user_id = data.get('user_id')
    study_start = data.get('study_start')
    study_end = data.get('study_end')
    work_start = data.get('work_start')
    work_end = data.get('work_end')

    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    # Convert strings to datetime objects (optional, for validation)
    try:
        study_start_dt = datetime.strptime(study_start, "%Y-%m-%d %H:%M:%S")
        study_end_dt = datetime.strptime(study_end, "%Y-%m-%d %H:%M:%S")
        work_start_dt = datetime.strptime(work_start, "%Y-%m-%d %H:%M:%S")
        work_end_dt = datetime.strptime(work_end, "%Y-%m-%d %H:%M:%S")
    except ValueError as e:
        return jsonify({"error": "Invalid datetime format"}), 400

    # Insert data into MongoDB
    log_entry = {
        "user_id": user_id,
        "study_start": study_start_dt,
        "study_end": study_end_dt,
        "work_start": work_start_dt,
        "work_end": work_end_dt,
        "timestamp": datetime.now()
    }
    collection.insert_one(log_entry)

    return jsonify({"message": "Time log added successfully!"}), 200

@app.route('/get-logs', methods=['GET'])
def get_logs():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    logs = list(collection.find({"user_id": user_id}, {"_id": 0}))
    return jsonify(logs), 200

if __name__ == '__main__':
    app.run(debug=True)
