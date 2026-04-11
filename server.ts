import express from "express";
import { createServer as createViteServer } from "vite";
import { spawn } from "child_process";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function startServer() {
  const app = express();
  const PORT = 3000;

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
