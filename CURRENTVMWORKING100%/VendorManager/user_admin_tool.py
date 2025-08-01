# user_admin_tool.py

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models.user import User
from utils.auth import hash_password

# Set up the engine to your DB (update this with your actual connection string)
DATABASE_URL = "postgresql+psycopg2://TGSAdmin:Donttazemebro5212@10.0.0.5:5432/TGSDB"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def list_users():
    session = Session()
    users = session.query(User).all()
    print("\n--- User List ---")
    for u in users:
        print(f"ID: {u.id}, Username: {u.username}, Role: {u.role}")
    session.close()

def reset_password():
    session = Session()
    username = input("\nEnter the username to reset password: ").strip()
    user = session.query(User).filter_by(username=username).first()

    if not user:
        print("❌ User not found.")
        session.close()
        return

    new_pw = input("Enter new password: ").strip()
    confirm_pw = input("Confirm password: ").strip()

    if new_pw != confirm_pw:
        print("❌ Passwords do not match.")
        session.close()
        return

    user.password_hash = hash_password(new_pw)
    session.commit()
    print("✅ Password updated successfully.")
    session.close()

if __name__ == "__main__":
    while True:
        print("\n--- User Admin Tool ---")
        print("1. List Users")
        print("2. Reset Password")
        print("3. Exit")

        choice = input("Choose an option: ").strip()
        if choice == "1":
            list_users()
        elif choice == "2":
            reset_password()
        elif choice == "3":
            break
        else:
            print("Invalid choice. Try again.")
