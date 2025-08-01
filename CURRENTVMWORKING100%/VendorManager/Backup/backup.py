import os
import shutil
import zipfile
from datetime import datetime, timedelta

# === CONFIGURATION ===
DB_NAME = "vendor_manager.db"
BACKUP_FOLDER = "backups"
RETENTION_DAYS = 30

# === Ensure backup directory exists ===
os.makedirs(BACKUP_FOLDER, exist_ok=True)

# === Generate zip backup filename ===
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
backup_zip_name = f"backup_{timestamp}.zip"
backup_zip_path = os.path.join(BACKUP_FOLDER, backup_zip_name)

# === Create ZIP containing the DB ===
if os.path.exists(DB_NAME):
    try:
        with zipfile.ZipFile(backup_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(DB_NAME, arcname=os.path.basename(DB_NAME))
        print(f"[OK] Backup created: {backup_zip_path}")
    except Exception as e:
        print(f"[ERROR] Failed to create zip: {e}")
else:
    print(f"[ERROR] Database not found: {DB_NAME}")
    exit(1)

# === Verify ZIP integrity ===
try:
    with zipfile.ZipFile(backup_zip_path, 'r') as zipf:
        test_result = zipf.testzip()
        if test_result is not None:
            print(f"[ERROR] Corrupted file in zip: {test_result}")
        else:
            print("[OK] Zip integrity verified.")
except Exception as e:
    print(f"[ERROR] Failed to verify zip: {e}")

# === Delete old zip backups ===
cutoff = datetime.now() - timedelta(days=RETENTION_DAYS)
deleted = 0

for fname in os.listdir(BACKUP_FOLDER):
    fpath = os.path.join(BACKUP_FOLDER, fname)
    try:
        if os.path.isfile(fpath) and fname.startswith("backup_") and fname.endswith(".zip"):
            timestamp_str = fname[7:-4]  # strip 'backup_' and '.zip'
            file_time = datetime.strptime(timestamp_str, "%Y-%m-%d_%H-%M-%S")
            if file_time < cutoff:
                os.remove(fpath)
                deleted += 1
    except Exception as e:
        print(f"[WARN] Could not process {fname}: {e}")

if deleted:
    print(f"[CLEANUP] Deleted {deleted} old backup(s).")
