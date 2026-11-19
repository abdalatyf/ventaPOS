import React, { useState, useEffect, useRef } from 'react';

export default function DebouncedInput({
  value,
  onChange,
  delay = 300,
  allowClear = true,
  style = {},
  ...props
}) {
  const [localValue, setLocalValue] = useState(value || '');
  const inputRef = useRef(null);

  // Update local value if parent value changes externally (e.g. reset filters)
  useEffect(() => {
    setLocalValue(value || '');
  }, [value]);

  useEffect(() => {
    const handler = setTimeout(() => {
      if (localValue !== (value || '')) {
        onChange({ target: { name: props.name, value: localValue } });
      }
    }, delay);
    
    return () => clearTimeout(handler);
  }, [localValue, value, onChange, props.name, delay]);

  const showClear =
    allowClear &&
    !props.disabled &&
    props.type !== 'number' &&
    Boolean(localValue && String(localValue).trim().length > 0);

  const handleClear = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setLocalValue('');
    onChange({ target: { name: props.name, value: '' } });
    if (inputRef.current) {
      inputRef.current.focus();
    }
  };

  return (
    <div
      className="position-relative d-inline-block w-100"
      style={{ flex: '1 1 auto', minWidth: 0 }}
    >
      <input
        ref={inputRef}
        {...props}
        style={{
          paddingLeft: showClear ? '2rem' : undefined,
          ...style,
        }}
        value={localValue}
        onChange={(e) => setLocalValue(e.target.value)}
      />
      {showClear && (
        <span
          className="input-icon-addon cursor-pointer"
          onClick={handleClear}
          title="مسح الحقل"
          style={{
            position: 'absolute',
            left: '8px',
            top: '50%',
            transform: 'translateY(-50%)',
            zIndex: 3,
            cursor: 'pointer',
            pointerEvents: 'auto',
            color: '#6c757d',
            fontSize: '14px',
            lineHeight: 1,
            padding: '2px 4px',
          }}
        >
          ✕
        </span>
      )}
    </div>
  );
}
