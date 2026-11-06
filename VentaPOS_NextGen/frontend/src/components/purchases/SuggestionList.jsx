import React, { useEffect, useRef } from 'react';

const SuggestionList = ({ open, suggestions, activeIndex, onSelect }) => {
  if (!open || !suggestions.length) return null;
  const activeItemRef = useRef(null);
  
  useEffect(() => {
    if (open && activeItemRef.current) {
      activeItemRef.current.scrollIntoView({ block: 'nearest' });
    }
  }, [activeIndex, open]);

  return (
    <ul 
      tabIndex="-1" 
      className="list-group shadow position-absolute w-100 bg-white"
      onMouseDown={(e) => e.preventDefault()}
      style={{ zIndex: 1055, top: '100%', maxHeight: 200, overflowY: 'auto', border: '1px solid #d8dee4' }}
    >
      {suggestions.map((s, i) => (
        <li
          key={i}
          className={`list-group-item list-group-item-action py-2 cursor-pointer border-bottom ${i === activeIndex ? '' : 'bg-white'}`} 
          style={i === activeIndex ? { backgroundColor: '#f1f5f9', color: '#1e293b' } : {}}
          onMouseDown={() => onSelect(s)}
          ref={i === activeIndex ? activeItemRef : null}
        >
          {typeof s === 'string' ? s : (
            <div>
              <div className="fw-bold">{s.customer_name || s.name || s.value || ''}</div>
              {s.phone_number && <div className="text-muted small">{s.phone_number} · {s.area}</div>}
            </div>
          )}
        </li>
      ))}
    </ul>
  );
};

export default SuggestionList;
