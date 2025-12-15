from database import SessionLocal
from models_db import User
from auth import verify_password, get_password_hash

def check_users():
    db = SessionLocal()
    users = db.query(User).all()
    print(f"Total Users Found: {len(users)}")
    
    for u in users:
        print(f"User: {u.id} | {u.username} | Role: {u.role}")
        print(f"Hash: {u.hashed_password[:20]}...")
        
        # Test 'wahaj123'
        is_valid = verify_password("wahaj123", u.hashed_password)
        print(f"Password 'wahaj123' valid? {is_valid}")
        print("-" * 30)

    if not users:
        print("No users found! Seeding didn't work.")

    db.close()

if __name__ == "__main__":
    check_users()
