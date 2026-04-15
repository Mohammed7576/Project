import React, { createContext, useContext, useState, useCallback, useRef } from 'react';

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
  isAttacking: boolean;
  logs: string[];
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
  const [isAttacking, setIsAttacking] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  
  const abortControllerRef = useRef<AbortController | null>(null);

  const startAttack = useCallback(async () => {
    // Sanitize URL: remove leading slashes and trim whitespace
    const sanitizedUrl = url.trim().replace(/^\/+/, '');
    const finalUrl = sanitizedUrl.startsWith('http') ? sanitizedUrl : `http://${sanitizedUrl}`;
    
    if (!finalUrl || isAttacking) return;
    
    setIsAttacking(true);
    setLogs([]);
    
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    const queryParams = new URLSearchParams({
      url: finalUrl,
      username,
      password,
      security,
      population: population.toString(),
      generations: generations.toString()
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
          
          setLogs(prev => {
            const newLogs = [...prev, ...lines];
            // Keep only last 500 lines to save memory/CPU
            return newLogs.slice(-500);
          });
        }
      }
    } catch (error: any) {
      if (error.name === 'AbortError') {
        setLogs(prev => [...prev, `[SYSTEM] Attack aborted by user.`]);
      } else {
        setLogs(prev => [...prev, `[ERROR] Failed to connect to engine: ${error}`]);
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
      isAttacking,
      logs,
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
