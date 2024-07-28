import hashlib
import pymongo
import jwt
import datetime
from pymongo import MongoClient
from typing import Optional
from utils.config import config


class MongoDBLogin:
    def __init__(self, secret_key: str):
        self.client = MongoClient(config.MONGO_URL)
        self.db = self.client["user-data"]
        self.users_collection = self.db["user-data"]
        self.secret_key = secret_key

    def hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def validate_password(self, password: str, hashed: str) -> bool:
        return self.hash_password(password) == hashed

    def login(self, email: str, password: str) -> Optional[str]:
        user = self.users_collection.find_one({"email": email})
        if user and self.validate_password(password, user['password']):
            payload = {
                "email": email,
                "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)  # Token valid for 1 HOUR
            }
            token = jwt.encode(payload, self.secret_key, algorithm="HS256")
            self.users_collection.update_one({"email": email}, {"$set": {"token": token}})
            return token
        return None

    def verify_token(self, token: str) -> bool:
        try:
            decoded = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            user = self.users_collection.find_one({"email": decoded["email"], "token": token})
            if user:
                return True
        except jwt.ExpiredSignatureError:
            return False
        except jwt.InvalidTokenError:
            return False
        return False

    def logout(self, token: str) -> bool:
        try:
            decoded = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            self.users_collection.update_one({"email": decoded["email"]}, {"$unset": {"token": ""}})
            return True
        except jwt.InvalidTokenError:
            return False

    def close(self):
        self.client.close()


if __name__ == "__main__":
    secret_key = "YOUR_SECRET_KEY"

    auth = MongoDBLogin(secret_key)

    email = "user@example.com"
    password = "securepassword"

    token = auth.login(email, password)
    if token:
        print("Login eseguito con successo! Token:", token)
        if auth.verify_token(token):
            print("Token verificato!")
        else:
            print("Token non valido!")

        if auth.logout(token):
            print("Logout eseguito con successo!")
        else:
            print("Errore durante il logout!")
    else:
        print("Email o password errati!")

    auth.close()
