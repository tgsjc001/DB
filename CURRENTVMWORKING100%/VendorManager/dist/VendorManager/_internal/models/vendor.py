from sqlalchemy import Column, Integer, String, Boolean, Float, Date
from .base import Base

class Vendor(Base):
    __tablename__ = 'vendors'

    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    business_name = Column(String)
    phone = Column(String)
    email = Column(String)
    island = Column(String)
    row = Column(String)
    table_numbers = Column(String)
    address = Column(String(255))
    city = Column(String(100))
    state = Column(String(50))
    zip_code = Column(String(20))

    # Options
    early_in = Column(Boolean)
    no_show = Column(Boolean)
    electricity = Column(Boolean)
    on_rollover = Column(Boolean, default=False)
    rta = Column(Boolean, default=False)  # Rollover to April
    rtn = Column(Boolean, default=False)  # Rollover to November
    show_date = Column(String)  # Date of actual show (MM/DD/YYYY)
    ffl = Column(Boolean)
    release_signed = Column(Boolean)
    taca_member = Column(Boolean)
    taca_paid = Column(Boolean)
    taca_amount = Column(Float)
    saturday_setup = Column(Boolean)
    double_booked = Column(Boolean, default=False)

    # 6 ft tables
    table_size_six = Column(Boolean)
    six_ft_gun = Column(Integer)
    six_ft_knife = Column(Integer)
    six_ft_display = Column(Integer)
    six_ft_nonrelated = Column(Integer)
    six_ft_rollover = Column(Integer, default=0)  # Number of 6' tables that are rollover

    # 8 ft tables
    table_size_eight = Column(Boolean)
    eight_ft_gun = Column(Integer)
    eight_ft_knife = Column(Integer)
    eight_ft_display = Column(Integer)
    eight_ft_nonrelated = Column(Integer)
    eight_ft_rollover = Column(Integer, default=0)  # Number of 8' tables that are rollover

    # Payment
    cash = Column(Boolean)
    credit = Column(Boolean)
    check = Column(Boolean)
    check_number = Column(String)
    receipt_number = Column(String)
    total_due = Column(Float)
    amount_paid = Column(Float)

    reservation_date = Column(String)
    first_show = Column(String)
    last_show_attended = Column(String)
    tax_id = Column(Integer, nullable=False, unique=True)
    notes = Column(String)