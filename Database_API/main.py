# Import required modules
import dotenv
import os
import mysql.connector
from fastapi import FastAPI, HTTPException, status, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from mysql.connector import errorcode
import jwt
from pydantic import BaseModel
import uuid
from typing import Optional

# Loading the environment variables
dotenv.load_dotenv()

# Initialize the todoapi app
app = FastAPI()

# Define the allowed origins for CORS
origins = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect to the MySQL database
try:
    cnx = mysql.connector.connect(
        user=os.environ['MYSQL_USER'],
        password=os.environ['MYSQL_PASSWORD'],
        host=os.environ['MYSQL_HOST'],
        database=os.environ['MYSQL_DB'],
    )
    cursor = cnx.cursor()
except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("Something is wrong with your user name or password")
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        print("Database does not exist")
    else:
        print(err)

# Define the authentication middleware
async def authenticate(request: Request):
    try:
        api_key = request.headers.get('authorization').replace("Bearer ", "")
        cursor.execute("SELECT * FROM voters WHERE voter_id = %s", (api_key,))
        if api_key not in [row[0] for row in cursor.fetchall()]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Forbidden"
            )
    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Forbidden"
        )

# Define the POST endpoint for login
@app.get("/login")
async def login(request: Request, voter_id: str, password: str):
    await authenticate(request)
    role = await get_role(voter_id, password)

    # Assuming authentication is successful, generate a token
    token = jwt.encode({'password': password, 'voter_id': voter_id, 'role': role}, os.environ['SECRET_KEY'], algorithm='HS256')

    return {'token': token, 'role': role}

# Replace 'admin' with the actual role based on authentication
async def get_role(voter_id, password):
    try:
        cursor.execute("SELECT role FROM voters WHERE voter_id = %s AND password = %s", (voter_id, password,))
        role = cursor.fetchone()
        if role:
            return role[0]
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid voter id or password"
            )
    except mysql.connector.Error as err:
        print(err)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error"
        )

# Define the Voter registration model
class VoterRegistration(BaseModel):
    email: str
    phone: str
    address: str
    dob: str
    gender: str
    national_id: str
    password: str

# Define the POST endpoint for voter registration
@app.post("/register")
async def register(voter_data: VoterRegistration):
    try:
        # Generate a unique voter ID
        voter_id = str(uuid.uuid4())
        
        # Check if national ID already exists
        cursor.execute("SELECT * FROM voters WHERE voter_id = %s", (voter_data.national_id,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="National ID already registered"
            )
        
        # Insert the new voter into the database
        cursor.execute(
            "INSERT INTO voters (voter_id, role, password) VALUES (%s, %s, %s)",
            (voter_id, "user", voter_data.password)
        )
        cnx.commit()
        
        # Generate a token for the new user
        token = jwt.encode(
            {'password': voter_data.password, 'voter_id': voter_id, 'role': 'user'},
            os.environ['SECRET_KEY'],
            algorithm='HS256'
        )
        
        return {'token': token, 'voter_id': voter_id, 'message': 'Registration successful'}
    
    except mysql.connector.Error as err:
        print(err)
        cnx.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during registration"
        )
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during registration"
        )
