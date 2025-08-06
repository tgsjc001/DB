def get_vendor_status(vendor):
    if vendor.no_show:
        return "No Show"
    if vendor.amount_paid >= vendor.total_due:
        return "Paid"
    if vendor.amount_paid == 0:
        return "Unpaid"
    return "Partial"

def get_vendor_tags(vendor):
    tags = []
    if vendor.double_booked:
        print(f"[DEBUG] Vendor {vendor.id} is double booked.")
        tags.append("black")  # TOP PRIORITY
    if vendor.amount_paid > vendor.total_due:
        tags.append("light_red")  # Overpaid
    elif vendor.amount_paid < vendor.total_due:
        tags.append("dark_red")   # Unpaid
    if vendor.rta:
        tags.append("light_yellow")
    if vendor.rtn:
        tags.append("dark_yellow")
    if vendor.electricity:
        tags.append("purple")
    if vendor.saturday_setup:
        tags.append("green")  # Lowest priority
    print(f"[DEBUG] Vendor {vendor.id} tags: {tags}")
    return tags

def get_highlight_tag(vendor):
    tags = get_vendor_tags(vendor)
    result = get_vendor_priority_tag(tags)
    print(f"[DEBUG] Vendor {vendor.id} highlight tag: {result}")
    return result

def get_vendor_flag_labels(vendor):
    flags = []
    if getattr(vendor, "rta", False):
        flags.append("RTA")
    if getattr(vendor, "rtn", False):
        flags.append("RTN")
    if getattr(vendor, "no_show", False):
        flags.append("NS")
    if getattr(vendor, "early_in", False):
        flags.append("EI")
    if getattr(vendor, "saturday_setup", False):
        flags.append("SS")
    if getattr(vendor, "electricity", False):
        flags.append("E")
    if vendor.amount_paid > vendor.total_due:
        flags.append("OP")
    elif vendor.amount_paid < vendor.total_due:
        flags.append("UP")
    if getattr(vendor, "double_booked", False):
        flags.append("DB")
    return flags

def get_vendor_priority_tag(tags):
    priority_order = [
        "black",         # ✅ Double-booked (top)
        "light_red",     # ✅ Overpaid
        "dark_red",      # ✅ Unpaid
        "light_yellow",  # RTA
        "dark_yellow",   # RTN
        "purple",        # Electricity
        "green",         # SS
    ]
    for tag in priority_order:
        if tag in tags:
            return tag
    return ""
