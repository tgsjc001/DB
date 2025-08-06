from models import Session
from models.session_log import SessionLog
from datetime import datetime

def log_session_login(user_id, ip_address=None):
    session = Session()
    log = SessionLog(
        user_id=user_id,
        login_time=datetime.utcnow(),
        ip_address=ip_address,
        visible=True
    )
    session.add(log)
    session.commit()
    session.close()

def log_session_logout(user_id):
    session = Session()
    log = session.query(SessionLog).filter_by(user_id=user_id, logout_time=None).order_by(SessionLog.login_time.desc()).first()
    if log:
        log.logout_time = datetime.utcnow()
        session.commit()
    session.close()