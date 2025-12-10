
import os
import sys

# Replicate config.py logic
UPLOADS_DIR = os.path.join(os.getcwd(), "data", "uploads")
print(f"Checking UPLOADS_DIR: {UPLOADS_DIR}")

try:
    if os.path.exists(UPLOADS_DIR):
        print("Directory exists.")
        files = os.listdir(UPLOADS_DIR)
        print(f"Files found: {len(files)}")
        for f in files:
            print(f" - {f}")
    else:
        print("Directory does NOT exist.")
        try:
            os.makedirs(UPLOADS_DIR)
            print("Created directory.")
        except Exception as e:
            print(f"Failed to create directory: {e}")

except Exception as e:
    print(f"CRITICAL ERROR: {e}")
