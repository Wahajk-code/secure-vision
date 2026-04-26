from database import SessionLocal, engine
from models_db import User, Base
from auth import get_password_hash
import sys

def seed_users():
    print("🔄 Starting Seeding Process...")
    
    # 1. Ensure Tables Exist
    print("🛠️ Creating Tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Tables Created.")
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        return

    # 2. Start Session
    db = SessionLocal()
    try:
        # 3. Check for Admin
        print("🔍 Checking for existing admin...")
        admin = db.query(User).filter(User.username == "wahaj").first()
        
        if not admin:
            print("🌱 Admin not found. Creating 'wahaj'...")
            hashed_pw = get_password_hash("wahaj123")
            new_admin = User(username="wahaj", hashed_password=hashed_pw, role="admin")
            db.add(new_admin)
            db.commit()
            db.refresh(new_admin)
            print(f"✅ Admin Created: ID={new_admin.id}, Username={new_admin.username}")
        else:
            print(f"ℹ️ Admin 'wahaj' already exists (ID: {admin.id}).")
            
    except Exception as e:
        print(f"❌ Seeding Error: {e}")
        db.rollback()
    finally:
        db.close()
        print("🏁 Seeding Process Finished.")

if __name__ == "__main__":
    seed_users()
