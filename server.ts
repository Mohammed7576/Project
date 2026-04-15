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
let db: any;
try {
  db = new Database("memory.db");
  console.log("[DB] Database initialized successfully.");
} catch (err) {
  console.error("[DB] Failed to initialize database, using in-memory fallback:", err);
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
        island_id INTEGER DEFAULT 0,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS exploits (
        payload TEXT PRIMARY KEY,
        type TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
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
  `);
} catch (err) {
  console.error("[DB] Schema creation failed:", err);
}

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

  // API route for Sandbox
  app.post("/api/sandbox", async (req, res) => {
    const { url, method, payload, headers } = req.body;
    const startTime = Date.now();
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
      // Try to select island_id, fallback to 1 if column doesn't exist yet
      let rows: any[] = [];
      try {
        const stmt = db.prepare("SELECT payload, score, island_id FROM experience ORDER BY timestamp DESC LIMIT 100");
        rows = stmt.all();
      } catch (e) {
        const stmt = db.prepare("SELECT payload, score, 1 as island_id FROM experience ORDER BY timestamp DESC LIMIT 100");
        rows = stmt.all();
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
          island: row.island_id || 1, // Default to 1 if 0
        };
      });
      
      res.json(radarData);
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
      const stmt = db.prepare("SELECT payload, type, timestamp FROM exploits ORDER BY timestamp DESC");
      const rows = stmt.all();
      res.json(rows);
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  // Catch-all for /api/* to ensure JSON response
  // API route to run Prometheus (Python script)
  app.get("/api/run-prometheus", async (req, res) => {
    try {
      res.setHeader('Content-Type', 'text/plain; charset=utf-8');
      res.setHeader('Transfer-Encoding', 'chunked');

      const { url, username, password, security, population, generations } = req.query;
      
      // Pass configuration as environment variables to the Python script
      const pythonProcess = spawn("python3", ["main.py"], {
        env: {
          ...process.env,
          TARGET_URL: url as string,
          TARGET_USER: username as string,
          TARGET_PASS: password as string,
          TARGET_SECURITY: security as string,
          POPULATION_SIZE: population as string,
          MAX_GENERATIONS: generations as string
        }
      });

      pythonProcess.on("error", (err) => {
        console.error("Failed to start python process:", err);
        if (!res.writableEnded) {
          res.write(`[ERROR] Failed to start engine: ${err.message}\n`);
          res.end();
        }
      });

      pythonProcess.stdout.on("data", (data) => {
        if (!res.writableEnded) res.write(data);
      });

      pythonProcess.stderr.on("data", (data) => {
        if (!res.writableEnded) res.write(`[ERROR] ${data}`);
      });

      pythonProcess.on("close", (code) => {
        if (!res.writableEnded) {
          res.write(`\n[PROCESS COMPLETED WITH CODE ${code}]\n`);
          res.end();
        }
      });
    } catch (err: any) {
      console.error("Error in run-prometheus route:", err);
      if (!res.writableEnded) {
        res.status(500).write(`[CRITICAL ERROR] ${err.message}\n`);
        res.end();
      }
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

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Server running on http://localhost:${PORT}`);
  });
}

startServer().catch(err => {
  console.error("[CRITICAL] Server failed to start:", err);
});
