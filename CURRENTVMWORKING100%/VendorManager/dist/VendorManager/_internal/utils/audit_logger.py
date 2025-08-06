from models import Session
from models.audit_log import AuditLog
from datetime import datetime

def log_audit(user, action, description):
    session = Session()
    log = AuditLog(
        username=user,
        action=action,
        description=description,
        timestamp=datetime.now()
    )
    session.add(log)
    session.commit()
    session.close()