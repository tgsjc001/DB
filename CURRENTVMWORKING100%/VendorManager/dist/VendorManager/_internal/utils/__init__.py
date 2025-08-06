from models import Session
from utils.auth import hash_password
from sqlalchemy.orm import relationship

def ensure_default_admin():
    session = Session()
    existing = session.query(User).filter_by(username="admin").first()
    if not existing:
        admin_user = User(username="admin", password_hash=hash_password("admin123"), role="admin", is_deleted=False)
        session.add(admin_user)
        session.commit()
    session.close()
