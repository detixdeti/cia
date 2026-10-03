import { createContext, useContext, useState, type ReactNode } from 'react';
import { Alert, Snackbar } from '@mui/material';

type Severity = 'success' | 'info' | 'error';
type Notify = (message: string, severity?: Severity) => void;

const NotifyContext = createContext<Notify>(() => {});

// Short feedback after an action, e.g. "Szenario übernommen". Any component can call useNotify().
export function NotificationProvider({ children }: { children: ReactNode }) {
  const [notification, setNotification] = useState<{ message: string; severity: Severity } | null>(null);

  return (
    <NotifyContext.Provider value={(message, severity = 'success') => setNotification({ message, severity })}>
      {children}
      <Snackbar
        open={notification !== null}
        autoHideDuration={4000}
        onClose={() => setNotification(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert variant="filled" severity={notification?.severity} onClose={() => setNotification(null)}>
          {notification?.message}
        </Alert>
      </Snackbar>
    </NotifyContext.Provider>
  );
}

export function useNotify() {
  return useContext(NotifyContext);
}
