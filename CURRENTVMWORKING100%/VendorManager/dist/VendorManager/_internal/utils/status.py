
def get_vendor_status(vendor):
    if vendor.no_show:
        return "NO SHOW"
    if (vendor.rta or vendor.rtn):
        return "ROLLOVER"
    if (vendor.on_rollover):
        return "ON ROLLOVER"
    if (vendor.amount_paid or 0) < (vendor.total_due or 0):
        return "UNPAID"
    if (vendor.amount_paid or 0) > (vendor.total_due or 0):
        return "OVERPAID"
    return "PAID"
