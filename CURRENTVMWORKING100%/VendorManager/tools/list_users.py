from models.base import SessionLocal as Session
from models.user import User

session = Session()
users = session.query(User).all()

print("Users in database:")
for user in users:
    print(user.username)
