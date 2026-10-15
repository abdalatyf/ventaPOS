import React, { useState, useEffect } from 'react';

export default function DebouncedInput({ value, onChange, delay = 300, ...props }) {
  const [localValue, setLocalValue] = useState(value || '');

  // Update local value if parent value changes externally (e.g. reset filters)
  useEffect(() => {
    setLocalValue(value || '');
  }, [value]);

  useEffect(() => {
    const handler = setTimeout(() => {
      if (localValue !== (value || '')) {
        // Create a synthetic event-like object for standard onChange handlers
        onChange({ target: { name: props.name, value: localValue } });
      }
    }, delay);
    
    return () => clearTimeout(handler);
  }, [localValue, value, onChange, props.name, delay]);

  return (
    <input 
      {...props} 
      value={localValue} 
      onChange={(e) => setLocalValue(e.target.value)} 
    />
  );
}
