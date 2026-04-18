import os
import sys
import threading
from core.exfiltration_lab import ExfiltrationLab

# Ensure we are in the backend directory context
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_standalone_extraction():
    """
    Triggers the Second Lab: The Extraction Specialist.
    This lab is completely independent of the evolutionary archipelago.
    """
    BASE_URL = "http://localhost:3000/dvwa/"
    USERNAME = "admin"
    PASSWORD = "password" # DVWA Default
    SECURITY = "medium"

    print("\n[SYSTEM] INITIALIZING INDEPENDENT EXTRACTION LAB...")
    print("[SYSTEM] No connection to Main Archipelago. Specialization: Data Theft Only.")
    
    lab = ExfiltrationLab(BASE_URL, USERNAME, PASSWORD, SECURITY)
    try:
        lab.run()
    except Exception as e:
        print(f"[ERROR] Extraction Lab encountered a fatal issue: {e}")

if __name__ == "__main__":
    run_standalone_extraction()
