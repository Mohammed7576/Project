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

// Initialize database
const db = new Database("memory.db");

// Create tables if they don't exist
db.exec(`
  CREATE TABLE IF NOT EXISTS experience (
      payload TEXT PRIMARY KEY,
      score REAL,
      status TEXT,
      parent_payload TEXT,
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
`);

async function startServer() {
  const app = express();
  app.use(express.json());
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

  // API route to receive AI hints
  app.post("/api/hint", (req, res) => {
    const { strategy, target_keyword, suggestion } = req.body;
    try {
      const stmt = db.prepare("INSERT INTO hints (strategy, target_keyword, suggestion) VALUES (?, ?, ?)");
      stmt.run(strategy, target_keyword, suggestion);
      res.json({ status: "hint_received" });
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

  // API route to run Prometheus (Python script)
  app.get("/api/run-prometheus", (req, res) => {
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

    pythonProcess.stdout.on("data", (data) => {
      res.write(data);
    });

    pythonProcess.stderr.on("data", (data) => {
      res.write(`[ERROR] ${data}`);
    });

    pythonProcess.on("close", (code) => {
      res.write(`\n[PROCESS COMPLETED WITH CODE ${code}]\n`);
      res.end();
    });
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

startServer();
