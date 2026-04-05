export class SuccessValidator {
  private basicSignatures = [
    "First name:", 
    "Surname:", 
    "ID:", 
    "admin", 
    "gordonb", 
    "1337"
  ];
  
  private hashPattern = /[a-f0-9]{32}/i;
  
  private schemaSignatures = [
    "table_name", 
    "column_name", 
    "information_schema", 
    "users", 
    "guest"
  ];

  public validate(responseBody: string, statusCode: number): { score: number, status: string } {
    if (!responseBody) {
      return { score: 0.0, status: "CONNECTION_ERROR" };
    }

    const lowBody = responseBody.toLowerCase();

    // 1. Goal: MD5 Hashes (Final Success)
    if (this.hashPattern.test(responseBody)) {
      return { score: 1.0, status: "CRITICAL_DATA_LEAKED" };
    }

    // 2. Schema Discovery (UNION)
    if (this.schemaSignatures.some(sig => lowBody.includes(sig)) && responseBody.toUpperCase().includes("UNION")) {
      return { score: 0.95, status: "SCHEMA_EXFILTRATED" };
    }

    // 3. WAF Bypass Partial (User data visible)
    if (this.basicSignatures.some(sig => responseBody.includes(sig))) {
      return { score: 0.9, status: "WAF_BYPASSED_PARTIAL" };
    }

    // 4. Potential Bypass (Status 200 and large body)
    if (statusCode === 200 && responseBody.length > 1000) {
      return { score: 0.5, status: "POTENTIAL_BYPASS" };
    }

    // 5. Failure
    return { score: 0.1, status: "WAF_BLOCKED" };
  }
}
