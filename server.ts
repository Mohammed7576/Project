import express from "express";
import { createServer as createViteServer } from "vite";
import { spawn } from "child_process";
import path from "path";
import { fileURLToPath } from "url";
import sqlite3 from "sqlite3";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

import fs from "fs";

async function startServer() {
  const app = express();
  app.use(express.json());
  const PORT = 3000;

  // API route to receive AI hints
  app.post("/api/hint", (req, res) => {
    const { strategy, target_keyword, suggestion } = req.body;
    const db = new sqlite3.Database("memory.db");
    db.run(
      "INSERT INTO hints (strategy, target_keyword, suggestion) VALUES (?, ?, ?)",
      [strategy, target_keyword, suggestion],
      (err) => {
        if (err) {
          res.status(500).json({ error: err.message });
        } else {
          res.json({ status: "hint_received" });
        }
        db.close();
      }
    );
  });

  // API route to get all saved exploits
  app.get("/api/exploits", (req, res) => {
    const db = new sqlite3.Database("memory.db");
    db.all("SELECT payload, type, timestamp FROM exploits ORDER BY timestamp DESC", (err, rows) => {
      if (err) {
        res.status(500).json({ error: err.message });
        return;
      }
      res.json(rows);
      db.close();
    });
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
