from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging

DATABASE_URL = "postgresql://TGSAdmin:Donttazemebro5212@10.0.0.6:5212/TGSDB_apr_2025"

# Validate and create engine
try:
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
except Exception as e:
    logging.exception("Database connection failed.")
    raise
