export class DataExtractor {
  private regexPatterns = {
    "user_record": /(?:ID|User|Username|First name|Surname)\s*[:=]\s*([\w\.\-\@\s]+)/gi,
    "md5_hash": /([a-f0-9]{32})/gi,
    "db_info": /(?:Database|Version|User\(\))\s*[:=]\s*([\w\.\-\@\s/]+)/gi,
    "email": /[\w\.-]+@[\w\.-]+\.\w+/gi
  };

  public extract(htmlContent: string): { type: string, val: string }[] {
    if (!htmlContent) return [];

    // Simple text cleaning (simulating BeautifulSoup text extraction)
    const cleanText = htmlContent.replace(/<[^>]*>?/gm, '\n');
    const extractedData: { type: string, val: string }[] = [];

    // 1. User records
    let match;
    while ((match = this.regexPatterns.user_record.exec(cleanText)) !== null) {
      const val = match[1].trim();
      if (val && val.length > 1) {
        extractedData.push({ type: "info", val });
      }
    }

    // 2. MD5 Hashes
    while ((match = this.regexPatterns.md5_hash.exec(cleanText)) !== null) {
      extractedData.push({ type: "hash", val: match[1] });
    }

    // 3. System info
    while ((match = this.regexPatterns.db_info.exec(cleanText)) !== null) {
      extractedData.push({ type: "system", val: match[1].trim() });
    }

    return extractedData;
  }

  public formatReport(data: { type: string, val: string }[]): string {
    if (!data || data.length === 0) {
      return "\n[-] No readable data found. The bypass was successful, but the output format is unknown.";
    }

    let report = "\n" + "═".repeat(55) + "\n";
    report += "   PROMETHEUS PROJECT - UNIT 804 HARVEST REPORT\n";
    report += "   Status: Full Exfiltration Successful\n";
    report += "═".repeat(55) + "\n";

    const seen = new Set<string>();
    for (const item of data) {
      const val = item.val;
      if (seen.has(val)) continue;
      seen.add(val);

      if (item.type === "hash") {
        report += `[!] CRITICAL: MD5 Hash Found -> ${val}\n`;
      } else if (item.type === "system") {
        report += `[+] SYSTEM INFO: ${val}\n`;
      } else {
        report += `[+] LEAKED DATA: ${val}\n`;
      }
    }

    report += "═".repeat(55);
    return report;
  }
}
