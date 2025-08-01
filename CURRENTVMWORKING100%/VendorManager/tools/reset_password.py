from models.base import SessionLocal as Session
from models.user import User
from utils.auth import hash_password

session = Session()

username = "admin"  # Change as needed
new_password = "test123"  # Change as needed

user = session.query(User).filter_by(username=username).first()
if user:
    user.password_hash = hash_password(new_password)
    session.commit()
    print(f"Password updated for {username}")
else:
    print("User not found.")
