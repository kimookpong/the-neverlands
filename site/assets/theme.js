// Apply a saved theme before first paint. Reading remains available without storage.
try {
  const theme = localStorage.getItem('neverlands-theme');
  if (theme === 'light' || theme === 'dark') document.documentElement.dataset.theme = theme;
} catch (_) { /* Storage may be disabled. */ }
