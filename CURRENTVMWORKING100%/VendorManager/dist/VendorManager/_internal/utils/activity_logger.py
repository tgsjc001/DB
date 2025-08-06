def log_activity(user_id, username, action, description):
    from models import Session
    from models.activity_log import ActivityLog
    from datetime import datetime

    session = Session()
    log = ActivityLog(
        user_id=user_id,
        username=username,
        action=action,
        description=description,
        timestamp=datetime.utcnow()
    )
    session.add(log)
    session.commit()
    session.close()
