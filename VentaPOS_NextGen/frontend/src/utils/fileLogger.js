/**
 * Global Frontend Logger & Console Bridge
 * Streams frontend console logs, unhandled runtime errors, and route navigation
 * directly to the backend (/api/v1/frontend-logs/) and live cmd console.
 */

const logQueue = [];
let isSending = false;
let flushTimer = null;
const DEBOUNCE_INTERVAL = 250; // Batch and flush within 250ms

const getEndpointUrl = () => {
  const base = import.meta.env.VITE_API_URL || '/api/v1';
  return `${base.replace(/\/+$/, '')}/frontend-logs/`;
};

const sendLogs = async () => {
  if (logQueue.length === 0 || isSending) return;

  isSending = true;
  const logsToSend = [...logQueue];
  logQueue.length = 0;

  try {
    const url = getEndpointUrl();
    await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ logs: logsToSend }),
    });
  } catch (err) {
    // If backend is unreachable or shutting down, preserve recent logs without overflow
    logQueue.unshift(...logsToSend);
    if (logQueue.length > 300) {
      logQueue.length = 300;
    }
  } finally {
    isSending = false;
    if (logQueue.length > 0 && !flushTimer) {
      flushTimer = setTimeout(() => {
        flushTimer = null;
        sendLogs();
      }, DEBOUNCE_INTERVAL);
    }
  }
};

const scheduleFlush = (immediate = false) => {
  if (immediate) {
    if (flushTimer) {
      clearTimeout(flushTimer);
      flushTimer = null;
    }
    sendLogs();
    return;
  }

  if (!flushTimer) {
    flushTimer = setTimeout(() => {
      flushTimer = null;
      sendLogs();
    }, DEBOUNCE_INTERVAL);
  }
};

const safeStringify = (obj) => {
  const seen = new WeakSet();
  try {
    return JSON.stringify(obj, (key, value) => {
      if (typeof value === 'object' && value !== null) {
        if (seen.has(value)) {
          return '[Circular]';
        }
        seen.add(value);
      }
      return value;
    }, 2);
  } catch (e) {
    return String(obj);
  }
};

const formatArgs = (args) => {
  return args.map((arg) => {
    if (arg === undefined) return 'undefined';
    if (arg === null) return 'null';
    if (arg instanceof Error) {
      return `${arg.name}: ${arg.message}${arg.stack ? '\n' + arg.stack : ''}`;
    }
    if (typeof arg === 'object') {
      return safeStringify(arg);
    }
    return String(arg);
  }).join(' ');
};

const pushLog = (level, message, details = '') => {
  // Guard against recursion loops from network or logging errors
  if (
    typeof message === 'string' &&
    (message.includes('/frontend-logs') || message.includes('frontend_console'))
  ) {
    return;
  }

  const currentPath = typeof window !== 'undefined' ? window.location.pathname : '';
  logQueue.push({
    level,
    message,
    details,
    url: currentPath,
    timestamp: new Date().toISOString(),
  });

  // Errors and warnings flush immediately to console
  const isPriority = level === 'ERROR' || level === 'WARN' || logQueue.length >= 20;
  scheduleFlush(isPriority);
};

const setupFileLogger = () => {
  if (typeof window === 'undefined') return;
  if (window.__ventaLoggerInitialized) return;
  window.__ventaLoggerInitialized = true;

  const originalLog = console.log.bind(console);
  const originalInfo = console.info.bind(console);
  const originalWarn = console.warn.bind(console);
  const originalError = console.error.bind(console);

  console.log = (...args) => {
    originalLog(...args);
    pushLog('INFO', formatArgs(args));
  };

  console.info = (...args) => {
    originalInfo(...args);
    pushLog('INFO', formatArgs(args));
  };

  console.warn = (...args) => {
    originalWarn(...args);
    pushLog('WARN', formatArgs(args));
  };

  console.error = (...args) => {
    originalError(...args);
    pushLog('ERROR', formatArgs(args));
  };

  // Capture unhandled runtime JavaScript exceptions
  window.addEventListener('error', (event) => {
    const errorMsg = event.message || 'Unknown runtime error';
    const sourceInfo = event.filename ? ` at ${event.filename}:${event.lineno}:${event.colno}` : '';
    const stack = event.error && event.error.stack ? `\n${event.error.stack}` : '';
    pushLog('ERROR', `Uncaught Exception: ${errorMsg}${sourceInfo}`, stack);
  });

  // Capture unhandled Promise rejections
  window.addEventListener('unhandledrejection', (event) => {
    let reasonStr = '';
    if (event.reason instanceof Error) {
      reasonStr = `${event.reason.name}: ${event.reason.message}${event.reason.stack ? '\n' + event.reason.stack : ''}`;
    } else {
      reasonStr = safeStringify(event.reason);
    }
    pushLog('ERROR', `Unhandled Promise Rejection: ${reasonStr}`);
  });

  // Capture route navigation
  const logRoute = () => {
    pushLog('INFO', `Navigated to: ${window.location.pathname}${window.location.search}`);
  };

  const originalPushState = window.history.pushState.bind(window.history);
  window.history.pushState = (...args) => {
    originalPushState(...args);
    logRoute();
  };

  const originalReplaceState = window.history.replaceState.bind(window.history);
  window.history.replaceState = (...args) => {
    originalReplaceState(...args);
    logRoute();
  };

  window.addEventListener('popstate', logRoute);

  // Flush remaining logs on window unload
  window.addEventListener('beforeunload', () => {
    if (logQueue.length > 0) {
      try {
        const payload = JSON.stringify({ logs: logQueue });
        if (navigator.sendBeacon) {
          navigator.sendBeacon(getEndpointUrl(), new Blob([payload], { type: 'application/json' }));
        } else {
          fetch(getEndpointUrl(), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: payload,
            keepalive: true,
          });
        }
      } catch (e) {
        // Ignored on exit
      }
    }
  });
};

export default setupFileLogger;
