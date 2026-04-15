import re
from bs4 import BeautifulSoup

class DataExtractor:
    def extract(self, html_text):
        results = []
        soup = BeautifulSoup(html_text, 'html.parser')
        # DVWA specific extraction (usually in <pre> tags)
        pre_tags = soup.find_all('pre')
        for pre in pre_tags:
            text = pre.get_text()
            if 'ID:' in text or 'First name:' in text:
                results.append(text.strip())
        return results

    def format_report(self, data):
        if not data:
            return "[!] No data extracted."
        report = "\n--- Extracted Data ---\n"
        for item in data:
            report += f"{item}\n"
        report += "----------------------\n"
        return report
