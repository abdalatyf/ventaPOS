import api from '../api';

const logQueue = [];
let isSending = false;
const SEND_INTERVAL = 2000; // Send logs every 2 seconds

const sendLogs = async () => {
  if (logQueue.length === 0 || isSending) return;
  
  isSending = true;
  const logsToSend = [...logQueue];
  logQueue.length = 0; // Clear the queue
  
  try {
    // Use the api instance which handles base URL and auth token
    await api.post('/frontend-logs/', { logs: logsToSend });
  } catch (err) {
    // If it fails, put the logs back at the beginning of the queue
    // (We silently swallow the error to avoid an infinite loop of console.error)
    logQueue.unshift(...logsToSend);
    
    // Don't let the queue grow infinitely if the backend is down
    if (logQueue.length > 500) {
      logQueue.length = 500;
    }
  } finally {
    isSending = false;
  }
};

const formatArgs = (args) => {
  return args.map(arg => {
    if (typeof arg === 'object') {
      try {
        // Handle Error objects specifically to get stack traces
        if (arg instanceof Error) {
          return `${arg.name}: ${arg.message}\n${arg.stack}`;
        }
        return JSON.stringify(arg, null, 2);
      } catch (e) {
        return String(arg);
      }
    }
    return String(arg);
  }).join(' ');
};

const setupFileLogger = () => {
  // Start the interval
  setInterval(sendLogs, SEND_INTERVAL);

  const originalLog = console.log;
  const originalError = console.error;
  const originalWarn = console.warn;
  const originalInfo = console.info;

  console.log = (...args) => {
    originalLog(...args);
    logQueue.push({ level: 'INFO', message: formatArgs(args), timestamp: new Date().toISOString() });
  };

  console.info = (...args) => {
    originalInfo(...args);
    logQueue.push({ level: 'INFO', message: formatArgs(args), timestamp: new Date().toISOString() });
  };

  console.warn = (...args) => {
    originalWarn(...args);
    logQueue.push({ level: 'WARN', message: formatArgs(args), timestamp: new Date().toISOString() });
  };

  console.error = (...args) => {
    originalError(...args);
    logQueue.push({ level: 'ERROR', message: formatArgs(args), timestamp: new Date().toISOString() });
  };
};

export default setupFileLogger;
