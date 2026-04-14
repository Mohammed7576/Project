import React, { ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends React.Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("[ErrorBoundary] Uncaught error:", error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div style={{ 
          padding: '40px', 
          background: '#1a0000', 
          color: '#ff4444', 
          fontFamily: 'monospace',
          minHeight: '100vh',
          border: '4px solid #ff0000',
          boxSizing: 'border-box'
        }}>
          <h1 style={{ margin: '0 0 20px 0', fontSize: '24px' }}>REACT RENDER ERROR</h1>
          <div style={{ background: '#000', padding: '20px', border: '1px solid #ff4444', marginBottom: '20px' }}>
            <p style={{ margin: '0 0 10px 0', fontWeight: 'bold' }}>Error Message:</p>
            <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all', margin: 0 }}>
              {this.state.error?.toString()}
            </pre>
          </div>
          <button 
            onClick={() => window.location.reload()}
            style={{
              background: '#ff4444',
              color: '#000',
              border: 'none',
              padding: '10px 20px',
              fontWeight: 'bold',
              cursor: 'pointer'
            }}
          >
            RELOAD APPLICATION
          </button>
        </div>
      );
    }

    return (this as any).props.children;
  }
}
