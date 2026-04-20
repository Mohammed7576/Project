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
  startAttack: () => Promise<void>;
  stopAttack: () => void;
}

const AttackContext = createContext<AttackContextType | undefined>(undefined);

export function AttackProvider({ children }: { children: React.ReactNode }) {
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
  
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    fetch('/api/last-session')
      .then(res => res.json())
      .then(data => {
        if (data.target_url) setUrl(data.target_url);
      })
      .catch(err => console.error("Failed to load last session", err));
  }, []);

  const startAttack = useCallback(async () => {
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
    
    if (!finalUrl || isAttacking) return;
    
    setIsAttacking(true);
    setLogs([]);
    setLearningLogs([]);
    setSuccessLogs([]);
    setSystemLogs([]);
    setCurrentGeneration(0);
    
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
            const newLogs = [...prev, ...lines];
            // Keep only last 500 lines to save memory/CPU
            return newLogs.slice(-500);
          });
        }
      }
    } catch (error: any) {
      if (error.name === 'AbortError') {
        const msg = `[SYSTEM] Attack aborted by user.`;
        setSystemLogs(prev => [...prev, msg]);
        setLogs(prev => [...prev, msg]);
      } else {
        const msg = `[ERROR] Failed to connect to engine: ${error}`;
        setSystemLogs(prev => [...prev, msg]);
        setLogs(prev => [...prev, msg]);
      }
    } finally {
      setIsAttacking(false);
      abortControllerRef.current = null;
    }
  }, [url, username, password, security, population, generations, isAttacking]);

  const stopAttack = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setIsAttacking(false);
  }, []);

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
    throw new Error('useAttack must be used within an AttackProvider');
  }
  return context;
}
