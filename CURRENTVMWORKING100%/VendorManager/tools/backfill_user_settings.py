from models.base import SessionLocal as Session
from models.user import User
from models.user_settings import UserSettings

session = Session()
users = session.query(User).all()

for user in users:
    if not user.settings:
        user.settings = UserSettings()
        print(f"Added settings for user: {user.username}")

session.commit()
print("All user settings backfilled.")
