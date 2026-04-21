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
  startAttack: () => Promise<void>;
  stopAttack: () => void;
}

const AttackContext = createContext<AttackContextType | undefined>(undefined);

console.log("[CONTEXT] Initializing AttackProvider...");
export function AttackProvider({ children }: { children: React.ReactNode }) {
  console.log("[CONTEXT] AttackProvider mounting...");
  const [url, setUrl] = useState('http://localhost/');
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('password');
  const [security, setSecurity] = useState('medium');
  const [population, setPopulation] = useState(12);
  const [generations, setGenerations] = useState(30);
  const [targetName, setTargetName] = useState('dvwa_lab');
  const [isAttacking, setIsAttacking] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [learningLogs, setLearningLogs] = useState<string[]>([]);
  const [successLogs, setSuccessLogs] = useState<string[]>([]);
  const [systemLogs, setSystemLogs] = useState<string[]>([]);
  const [currentGeneration, setCurrentGeneration] = useState(0);
  const [elapsedTime, setElapsedTime] = useState(0);
  
  const abortControllerRef = useRef<AbortController | null>(null);
  const attackStartTimeRef = useRef<number | null>(null);
  const timerIntervalRef = useRef<any>(null);

  useEffect(() => {
    fetch('/api/last-session')
      .then(res => res.json())
      .then(data => {
        if (data.target_url) setUrl(data.target_url);
      })
      .catch(err => console.error("Failed to load last session", err));

    // Restore the current generation max
    fetch('/api/strategic-metrics')
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data) && data.length > 0) {
          const maxGen = Math.max(...data.map((d: any) => d.generation));
          setCurrentGeneration(maxGen);
        }
      })
      .catch(e => console.error("Could not fetch max generation", e));
    fetch('/api/exploits')
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) {
           setSuccessLogs(data.map((exp: any) => `[SUCCESS - RESTORED] ... ${exp.payload}`).slice(-50));
        }
      })
      .catch(e => console.error("Could not fetch historical exploits", e));
      
    fetch('/api/brain-logs')
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) {
           setLearningLogs(data.map((log: any) => `[RESTORED] ${log.message}`).slice(-50));
        }
      })
      .catch(e => console.error("Could not fetch historical brain logs", e));
  }, []);

  const stopAttack = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    if (timerIntervalRef.current) {
      clearInterval(timerIntervalRef.current);
    }
    setIsAttacking(false);
    attackStartTimeRef.current = null;
  }, []);

  const startAttackLoop = useCallback(async (isResume = false) => {
    // Sanitize URL: remove leading slashes and trim whitespace
    let sanitizedUrl = url.trim().replace(/^\/+/, '');
    
    // Fix common typos in localhost
    const localhostTypos = ['loaclhost', 'loclahost', 'localhost', 'lcoalhost', 'localhost:3000'];
    const lowerUrl = sanitizedUrl.toLowerCase();
    
    for (const typo of localhostTypos) {
      if (lowerUrl.includes(typo) && !lowerUrl.includes('localhost')) {
        sanitizedUrl = sanitizedUrl.replace(new RegExp(typo, 'gi'), 'localhost');
        break;
      }
    }

    const finalUrl = sanitizedUrl.startsWith('http') ? sanitizedUrl : `http://${sanitizedUrl}`;
    
    if (!finalUrl) return;

    if (!isResume) {
      setIsAttacking(true);
      // We no longer clear successLogs or learningLogs completely here to keep historical info visible
      // We only clear the live execution log area so the terminal looks clean for the new run
      setLogs([]); 
      // If desired, you can add a fetch here to repopulate them if they were empty, 
      // but they are kept in state across restarts in the same tab.
      setCurrentGeneration(0);
      setElapsedTime(0);
      attackStartTimeRef.current = Date.now();
      
      timerIntervalRef.current = setInterval(() => {
        if (attackStartTimeRef.current) {
          setElapsedTime(Math.floor((Date.now() - attackStartTimeRef.current) / 1000));
        }
      }, 1000);
    }
    
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    const queryParams = new URLSearchParams({
      url: finalUrl,
      username,
      password,
      security,
      population: population.toString(),
      generations: generations.toString(),
      targetName
    });

    try {
      const response = await fetch(`/api/run-prometheus?${queryParams.toString()}`, {
        signal: abortController.signal
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || `Server returned ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          
          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split('\n').filter(line => line.trim() !== '');
          
          lines.forEach(line => {
            if (line.includes(': keep-alive')) return;
            
            // Categorization logic
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
          });

          setLogs(prev => {
            const newLogs = [...prev, ...lines.filter(l => !l.includes(': keep-alive'))];
            return newLogs.slice(-500);
          });
        }
      }

      // Persistent Loop logic: Never stop automatically.
      // Resume indefinitely as long as the user hasn't clicked 'STOP'
      if (!abortController.signal.aborted) {
        const elapsed = attackStartTimeRef.current ? (Date.now() - attackStartTimeRef.current) / 1000 : 0;
        const msg = `[SYSTEM] Cycle completed at ${Math.floor(elapsed/60)}m. Continuous evolution active: Resuming...`;
        setSystemLogs(prev => [...prev, msg]);
        
        // Short delay to allow the server to settle between cycles
        await new Promise(r => setTimeout(r, 2000));
        startAttackLoop(true);
      } else {
        setIsAttacking(false);
        if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
      }

    } catch (error: any) {
      if (error.name === 'AbortError') {
        const msg = `[SYSTEM] Attack aborted by user.`;
        setSystemLogs(prev => [...prev, msg]);
        setLogs(prev => [...prev, msg]);
        setIsAttacking(false);
        if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
      } else {
        const msg = `[ERROR] Failed to connect to engine: ${error}`;
        setSystemLogs(prev => [...prev, msg]);
        setLogs(prev => [...prev, msg]);
        
        // Auto-recovery: If it's a stream error but not an abort, try to resume
        if (!abortController.signal.aborted) {
          const recoveryMsg = `[SYSTEM] Connection lost. Attempting auto-recovery in 3s...`;
          setSystemLogs(prev => [...prev, recoveryMsg]);
          await new Promise(r => setTimeout(r, 3000));
          startAttackLoop(true);
        } else {
          setIsAttacking(false);
          if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
        }
      }
    } finally {
      // ONLY clear the ref if it's still ours. 
      // If a recursive call already replaced it, don't touch it!
      if (abortControllerRef.current === abortController) {
        abortControllerRef.current = null;
      }
    }
  }, [url, username, password, security, population, generations, targetName]);

  const startAttack = useCallback(() => startAttackLoop(false), [startAttackLoop]);

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
      startAttack,
      stopAttack
    }}>
      {children}
    </AttackContext.Provider>
  );
}

export function useAttack() {
  const context = useContext(AttackContext);
  if (context === undefined) {
    console.error("[CONTEXT] useAttack called OUTSIDE of AttackProvider!");
    throw new Error('useAttack must be used within an AttackProvider');
  }
  return context;
}
