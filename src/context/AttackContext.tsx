import React, { createContext, useContext, useState, useCallback, useRef, useEffect } from 'react';

interface AttackContextType {
  url: string;
  setUrl: (url: string) => void;
  username: string;
  setUsername: (username: string) => void;
  password: string;
  setPassword: (password: string) => void;
  security: string;
  setSecurity: (security: string) => void;
  population: number;
  setPopulation: (population: number) => void;
  generations: number;
  setGenerations: (generations: number) => void;
  targetName: string;
  setTargetName: (name: string) => void;
  isAttacking: boolean;
  logs: string[];
  learningLogs: string[];
  successLogs: string[];
  systemLogs: string[];
  currentGeneration: number;
  elapsedTime: number;
  attemptHistory: any[];
  telemetryHistory: any[];
  startAttack: (mode?: 'training' | 'attack') => Promise<void>;
  stopAttack: () => void;
}

const AttackContext = createContext<AttackContextType | undefined>(undefined);

export function AttackProvider({ children }: { children: React.ReactNode }) {
  const [url, setUrl] = useState('http://localhost/');
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('password');
  const [security, setSecurity] = useState('medium');
  const [population, setPopulation] = useState(300);
  const [generations, setGenerations] = useState(30);
  const [targetName, setTargetName] = useState('dvwa_lab');
  const [isAttacking, setIsAttacking] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [learningLogs, setLearningLogs] = useState<string[]>([]);
  const [successLogs, setSuccessLogs] = useState<string[]>([]);
  const [systemLogs, setSystemLogs] = useState<string[]>([]);
  const [currentGeneration, setCurrentGeneration] = useState(0);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [attemptHistory, setAttemptHistory] = useState<any[]>([]);
  const [telemetryHistory, setTelemetryHistory] = useState<any[]>([]);
  
  const abortControllerRef = useRef<AbortController | null>(null);
  const attackStartTimeRef = useRef<number | null>(null);
  const timerIntervalRef = useRef<any>(null);
  const socketRef = useRef<WebSocket | null>(null);

  // Initialize WebSocket for real-time logs
  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const socketUrl = `${protocol}//${window.location.host}/ws/logs`;
    
    const connect = () => {
      console.log("[WS] Connecting to", socketUrl);
      const ws = new WebSocket(socketUrl);
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleStructuredLog(data);
        } catch (e) {
          // Fallback for non-JSON lines
          handleRawLog(event.data);
        }
      };

      ws.onclose = () => {
        console.log("[WS] Disconnected. Reconnecting in 5s...");
        setTimeout(connect, 5000);
      };

      ws.onerror = (err) => {
        console.error("[WS] Socket error", err);
      };

      socketRef.current = ws;
    };

    connect();
    return () => socketRef.current?.close();
  }, []);

  const handleStructuredLog = (data: any) => {
    const { type, message, payload, score, status, gen, island, latency } = data;

    if (type === 'attempt') {
      const logLine = `[ISLAND ${island}] Gen ${gen}: Score ${Math.round(score * 100)} | ${status} | Payload: ${payload}`;
      setLearningLogs(prev => [...prev.slice(-199), logLine]);
      setAttemptHistory(prev => [...prev.slice(-499), { island, score, status, gen, latency, timestamp: Date.now() }]);
      if (score >= 0.7) {
        setSuccessLogs(prev => [...prev.slice(-99), `[SUCCESS] ${payload}`]);
      }
    } else if (type === 'telemetry') {
      setTelemetryHistory(prev => [...prev.slice(-299), { ...data, timestamp: Date.now() }]);
    } else if (type === 'gen_start') {
      setCurrentGeneration(data.val || 0);
      setSystemLogs(prev => [...prev.slice(-199), message || `[GENERATION START]`]);
    } else if (type === 'success') {
       setSuccessLogs(prev => [...prev.slice(-99), message]);
    } else if (type === 'error') {
       setSystemLogs(prev => [...prev.slice(-199), `[ERROR] ${message}`]);
    } else if (type === 'system') {
       setSystemLogs(prev => [...prev.slice(-199), message]);
    } else if (type === 'best') {
       setSystemLogs(prev => [...prev.slice(-199), `[BEST] ${message}`]);
    } else if (message) {
       handleRawLog(message);
    }
  };

  const handleRawLog = (line: string) => {
    if (line.includes(': keep-alive')) return;
    
    if (line.includes('[*] AST Blocker') || line.includes('[?] Probing') || line.includes('Discovery Complete')) {
      setLearningLogs(prev => [...prev.slice(-199), line]);
    } else if (line.includes('SQL_EXECUTION_VERIFIED') || line.includes('SUCCESS') || line.includes('EXFILTRATION')) {
      setSuccessLogs(prev => [...prev.slice(-199), line]);
    } else if (line.includes('[+] Generation')) {
      const genMatch = line.match(/Generation (\d+)/);
      if (genMatch) setCurrentGeneration(parseInt(genMatch[1]));
      setSystemLogs(prev => [...prev.slice(-199), line]);
    } else {
      setSystemLogs(prev => [...prev.slice(-199), line]);
    }
    
    setLogs(prev => [...prev.slice(-499), line]);
  };

  useEffect(() => {
    // Restore state from APIs
    fetch('/api/last-session')
      .then(res => res.json())
      .then(data => { if (data.target_url) setUrl(data.target_url); })
      .catch(() => {});

    fetch('/api/exploits')
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) {
           setSuccessLogs(data.map((exp: any) => `[RESTORED] ... ${exp.payload}`).slice(-50));
        }
      })
      .catch(() => {});
  }, []);

  const stopAttack = useCallback(() => {
    if (abortControllerRef.current) abortControllerRef.current.abort();
    if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
    setIsAttacking(false);
    attackStartTimeRef.current = null;
  }, []);

  const startAttack = useCallback(async (mode: 'training' | 'attack' = 'attack') => {
    stopAttack();
    setIsAttacking(true);
    setLogs([]);
    setElapsedTime(0);
    attackStartTimeRef.current = Date.now();
    
    timerIntervalRef.current = setInterval(() => {
      if (attackStartTimeRef.current) {
        setElapsedTime(Math.floor((Date.now() - attackStartTimeRef.current) / 1000));
      }
    }, 1000);

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    const queryParams = new URLSearchParams({
      url: url.trim(),
      username,
      password,
      security,
      population: population.toString(),
      generations: generations.toString(),
      targetName,
      mode
    });

    try {
      // Trigger the engine. The logs will now flow through WebSocket.
      const response = await fetch(`/api/run-prometheus?${queryParams.toString()}`, {
        signal: abortController.signal
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || `Server error ${response.status}`);
      }
      
      // We don't necessarily need to read the body if we use WebSockets for ALL logs,
      // but keeping the fetch alive ensures the child process stays alive in the current server setup.
      const reader = response.body?.getReader();
      if (reader) {
        while (true) {
          const { done } = await reader.read();
          if (done) break;
        }
      }

    } catch (error: any) {
      if (error.name !== 'AbortError') {
        const msg = `[ERROR] Connection error: ${error.message}`;
        setSystemLogs(prev => [...prev, msg]);
      }
    } finally {
      setIsAttacking(false);
      if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
    }
  }, [url, username, password, security, population, generations, targetName, stopAttack]);

  return (
    <AttackContext.Provider value={{
      url, setUrl,
      username, setUsername,
      password, setPassword,
      security, setSecurity,
      population, setPopulation,
      generations, setGenerations,
      targetName, setTargetName,
      isAttacking,
      logs,
      learningLogs,
      successLogs,
      systemLogs,
      currentGeneration,
      elapsedTime,
      attemptHistory,
      telemetryHistory,
      startAttack,
      stopAttack
    }}>
      {children}
    </AttackContext.Provider>
  );
}

export function useAttack() {
  const context = useContext(AttackContext);
  if (context === undefined) throw new Error('useAttack must be used within an AttackProvider');
  return context;
}
