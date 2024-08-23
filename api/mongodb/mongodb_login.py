import hashlib
import pymongo
import jwt
import datetime
from pymongo import MongoClient
from typing import Optional, Dict, Any
from utils.config import config


class MongoDBLogin:
    def __init__(self, secret_key: str):
        self.client = MongoClient(config.MONGO_URL)
        self.db = self.client["Teledrive"]
        self.users_collection = self.db["user-data"]
        self.secret_key = secret_key

    def get_user_by_token(self, token):
        user = self.db.users.find_one({'token': token})
        return user

    def hash_password(self, password: str) -> str:
        """Hash the password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def validate_password(self, password: str, hashed: str) -> bool:
        """Validate if the provided password matches the hashed password."""
        return self.hash_password(password) == hashed

    def create_user(self, email: str, password: str, discord_id: str, role: str = "user") -> Optional[str]:
        """Create a new user with the provided email and password."""
        if self.users_collection.find_one({"email": email}):
            return None  # Email already exists

        hashed_password = self.hash_password(password)
        user_data = {
            "email": email,
            "password": hashed_password,
            "created_at": datetime.datetime.utcnow(),
            "last_login": None,
            "discord_id": discord_id,
            "role": role
        }
        self.users_collection.insert_one(user_data)
        return self.login(email, password)

    def login(self, email: str, password: str) -> Optional[str]:
        """Authenticate the user and return a JWT token."""
        user = self.users_collection.find_one({"email": email})
        if user and self.validate_password(password, user['password']):
            payload = {
                "email": email,
                "role": user["role"],
                "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)  # Token valid for 1 HOUR
            }
            token = jwt.encode(payload, self.secret_key, algorithm="HS256")
            self.users_collection.update_one(
                {"email": email},
                {"$set": {"token": token, "last_login": datetime.datetime.utcnow()}}
            )
            return token
        return None

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify the JWT token and return the decoded payload if valid."""
        try:
            decoded = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            user = self.users_collection.find_one({"email": decoded["email"], "token": token})
            if user:
                return decoded  # Return the decoded payload including role
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        return None

    def logout(self, token: str) -> bool:
        """Logout the user by invalidating the JWT token."""
        try:
            decoded = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            self.users_collection.update_one({"email": decoded["email"]}, {"$unset": {"token": ""}})
            return True
        except jwt.InvalidTokenError:
            return False

    def get_user_role(self, token: str) -> Optional[str]:
        """Retrieve the role of the user based on the JWT token."""
        decoded = self.verify_token(token)
        if decoded:
            return decoded.get("role")
        return None

    def close(self):
        """Close the MongoDB connection."""
        self.client.close()


if __name__ == "__main__":
    secret_key = config.SECRET_KEY

    auth = MongoDBLogin(secret_key)

    token = auth.create_user("prova1234@gmail.com", "ciao1234", "455043995509456907")
    if token:
        print("User registered and logged in successfully! Token:", token)

    auth.close()
