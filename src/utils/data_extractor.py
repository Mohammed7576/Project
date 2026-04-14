import re

class DataExtractor:
    def __init__(self):
        self.regex_patterns = {
            "user_record": r"(?:ID|User|Username|First name|Surname)\s*[:=]\s*([\w\.\-\@\s]+)",
            "md5_hash": r"([a-f0-9]{32})",
            "db_info": r"(?:Database|Version|User\(\))\s*[:=]\s*([\w\.\-\@\s/]+)",
            "email": r"[\w\.-]+@[\w\.-]+\.\w+"
        }

    def extract(self, html_content):
        if not html_content:
            return None
        
        # Simple HTML tag removal
        clean_text = re.sub(r'<[^>]+>', '\n', html_content)
        
        # Extract data using regex
        extracted_data = []
        
        # User records
        matches = re.findall(self.regex_patterns["user_record"], clean_text, re.IGNORECASE)
        for match in matches:
            val = match.strip()
            if val and len(val) > 1:
                extracted_data.append({"type": "info", "val": val})

        # MD5 Hashes
        hashes = re.findall(self.regex_patterns["md5_hash"], clean_text)
        for h in hashes:
            extracted_data.append({"type": "hash", "val": h})

        # Database info
        db_matches = re.findall(self.regex_patterns["db_info"], clean_text, re.IGNORECASE)
        for db_val in db_matches:
            extracted_data.append({"type": "system", "val": db_val.strip()})

        return extracted_data

    def format_report(self, data):
        if not data:
            return "\n[-] No readable data found. The bypass was successful, but the output format is unknown."

        report = "\n" + "═"*55 + "\n"
        report += "   القيادة والسيطرة - وحدة الهجوم HARVEST REPORT\n"
        report += "   Status: Full Exfiltration Successful\n"
        report += "═"*55 + "\n"

        seen = set()
        for item in data:
            val = item["val"]
            if val in seen: continue
            seen.add(val)

            if item["type"] == "hash":
                report += f"[!] CRITICAL: MD5 Hash Found -> {val}\n"
            elif item["type"] == "system":
                report += f"[+] SYSTEM INFO: {val}\n"
            else:
                report += f"[+] LEAKED DATA: {val}\n"
        report += "═"*55
        return report
