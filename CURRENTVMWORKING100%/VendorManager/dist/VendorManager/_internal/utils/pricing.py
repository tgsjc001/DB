def calculate_total_due(vendor):
    def safe_int(value):
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0

    total = 0

    # --- 6' Tables ---
    total += safe_int(getattr(vendor, "six_ft_gun", 0)) * 175
    total += safe_int(getattr(vendor, "six_ft_knife", 0)) * 175
    total += safe_int(getattr(vendor, "six_ft_display", 0)) * 100
    total += safe_int(getattr(vendor, "six_ft_nonrelated", 0)) * 220

    # --- 8' Tables ---
    total += safe_int(getattr(vendor, "eight_ft_gun", 0)) * 200
    total += safe_int(getattr(vendor, "eight_ft_knife", 0)) * 200
    total += safe_int(getattr(vendor, "eight_ft_display", 0)) * 100
    total += safe_int(getattr(vendor, "eight_ft_nonrelated", 0)) * 220

    # --- Electricity ---
    if getattr(vendor, "electricity", False):
        total += 100

    # --- Credit Card Surcharge ---
    if getattr(vendor, "credit", False):
        total += 8

    return total
