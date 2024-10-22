from utils.config import config
from pymongo import MongoClient
import hashlib
import datetime


class MongoDBLogin:
    def __init__(self, secret_key: str):
        self.client = MongoClient(config.MONGO_URL)
        self.db = self.client[config.NAME_CLUSTER]
        self.users_collection = self.db["user-data"]
        self.secret_key = secret_key

    def hash_password(self, password: str) -> str:
        """Hash the password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def create_user(self, email: str, password: str, discord_id: str, url_avatar: str, role: str = "user"):
        """Create a new user, return True if successful or False if the email already exists."""
        if self.users_collection.find_one({"email": email}):
            print(f"❌ User with email {email} already exists.")
            return False

        hashed_password = self.hash_password(password)
        user_data = {
            "email": str(email),
            "password": str(hashed_password),
            "created_at": datetime.datetime.utcnow(),
            "last_login": None,
            "discord_id": str(discord_id),
            "url_avatar": str(url_avatar),
            "role": str(role)
        }
        self.users_collection.insert_one(user_data)
        print("✅ User registered successfully!")
        return True

    def list_users(self):
        """List all registered users."""
        users = self.users_collection.find({}, {"email": 1, "role": 1, "created_at": 1, "_id": 0})
        print("\n📋 Registered Users:")
        for user in users:
            print(f"  - Email: {user['email']}, Role: {user['role']}, Created at: {user['created_at']}")
        print("")

    def find_user(self, email: str):
        """Find a user by email."""
        user = self.users_collection.find_one({"email": email}, {"password": 0, "_id": 0})
        if user:
            print(f"\n👤 User Found: {user}\n")
        else:
            print(f"\n❌ No user found with email: {email}\n")

    def logout(self, email: str):
        """Logout the user by invalidating their token."""
        result = self.users_collection.update_one({"email": email}, {"$unset": {"token": ""}})
        if result.modified_count > 0:
            print(f"\n🚪 User with email {email} has been logged out successfully.\n")
        else:
            print(f"\n❌ No active session found for user with email {email}.\n")

    def delete_user(self, email: str):
        """Delete a user by email."""
        result = self.users_collection.delete_one({"email": email})
        if result.deleted_count > 0:
            print(f"\n🗑️ User with email {email} has been deleted.\n")
        else:
            print(f"\n❌ No user found with email: {email}.\n")

    def update_user(self, email: str, updates: dict):
        """Update user details (role, password, avatar)."""
        result = self.users_collection.update_one({"email": email}, {"$set": updates})
        if result.modified_count > 0:
            print(f"\n✏️ User with email {email} has been updated.\n")
        else:
            print(f"\n❌ No user found with email: {email} or nothing to update.\n")

    def reset_password(self, email: str, new_password: str):
        """Reset the password of a user."""
        hashed_password = self.hash_password(new_password)
        result = self.users_collection.update_one({"email": email}, {"$set": {"password": hashed_password}})
        if result.modified_count > 0:
            print(f"\n🔑 Password for user {email} has been reset.\n")
        else:
            print(f"\n❌ No user found with email: {email}.\n")

    def close(self):
        """Close the MongoDB connection."""
        self.client.close()


def get_input(prompt: str, required: bool = True) -> str:
    """Helper function to get user input with optional validation."""
    while True:
        user_input = input(prompt).strip()
        if user_input or not required:
            return user_input
        print("⚠️ This field is required.")


def register_user():
    secret_key = config.SECRET_KEY
    auth = MongoDBLogin(secret_key)

    print("👋 Welcome to the user registration system.\n")

    # Collect user information interactively
    email = get_input("📧 Enter your email: ")
    password = get_input("🔑 Enter your password: ")
    discord_id = get_input("💬 Enter your Discord ID: ")
    url_avatar = get_input("🌐 Enter the URL of your avatar (optional): ", required=False)
    role = get_input("👤 Enter the role (default is 'user'): ", required=False) or "user"

    # Try to create the user
    success = auth.create_user(email, password, discord_id, url_avatar, role)
    if not success:
        print("⚠️ Registration failed. Please try again with a different email.")

    auth.close()


def main_menu():
    secret_key = config.SECRET_KEY
    auth = MongoDBLogin(secret_key)

    while True:
        print("📂 User Management Menu:")
        print("1️⃣ - List all users")
        print("2️⃣ - Find a user by email")
        print("3️⃣ - Logout a user by email")
        print("4️⃣ - Delete a user by email")
        print("5️⃣ - Update user details")
        print("6️⃣ - Reset user password")
        print("7️⃣ - Register a new user")
        print("8️⃣ - Exit")
        choice = input("\nChoose an option: ").strip()

        if choice == "1":
            auth.list_users()

        elif choice == "2":
            email = get_input("📧 Enter user email to search: ")
            auth.find_user(email)

        elif choice == "3":
            email = get_input("📧 Enter user email to log out: ")
            auth.logout(email)

        elif choice == "4":
            email = get_input("📧 Enter user email to delete: ")
            confirmation = get_input("⚠️ Are you sure you want to delete this user? (yes/no): ").lower()
            if confirmation == "yes":
                auth.delete_user(email)
            else:
                print("\n❌ User deletion cancelled.\n")

        elif choice == "5":
            email = get_input("📧 Enter user email to update: ")
            updates = {}
            role = get_input("👤 Enter new role (leave blank to skip): ", required=False)
            if role:
                updates["role"] = role
            avatar = get_input("🌐 Enter new avatar URL (leave blank to skip): ", required=False)
            if avatar:
                updates["url_avatar"] = avatar
            password = get_input("🔑 Enter new password (leave blank to skip): ", required=False)
            if password:
                updates["password"] = auth.hash_password(password)
            if updates:
                auth.update_user(email, updates)
            else:
                print("\n❌ No updates provided.\n")

        elif choice == "6":
            email = get_input("📧 Enter user email to reset password: ")
            new_password = get_input("🔑 Enter new password: ")
            auth.reset_password(email, new_password)

        elif choice == "7":
            register_user()

        elif choice == "8":
            print("👋 Exiting User Management.")
            auth.close()
            break

        else:
            print("⚠️ Invalid option. Please try again.\n")


if __name__ == "__main__":
    main_menu()
