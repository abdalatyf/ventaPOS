import React, { useState, useRef, useEffect } from 'react';

const Autocomplete = ({ 
  value, 
  onChange, 
  onSelect, 
  fetchSuggestions, 
  placeholder, 
  displayKey = 'name',
  className = "form-control"
}) => {
  const [suggestions, setSuggestions] = useState([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const debounceRef = useRef(null);
  const activeItemRef = useRef(null);

  // Scroll to active item when using keyboard
  useEffect(() => {
    if (activeIndex >= 0 && activeItemRef.current) {
      activeItemRef.current.scrollIntoView({ block: 'nearest' });
    }
  }, [activeIndex]);

  const handleInputChange = (e) => {
    const val = e.target.value;
    onChange(val);
    setActiveIndex(-1);

    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (!val.trim()) {
      setSuggestions([]);
      setShowDropdown(false);
      return;
    }

    debounceRef.current = setTimeout(async () => {
      const results = await fetchSuggestions(val);
      setSuggestions(results || []);
      setShowDropdown(true);
    }, 300);
  };

  const handleKeyDown = (e) => {
    if (!showDropdown || suggestions.length === 0) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex(prev => (prev < suggestions.length - 1 ? prev + 1 : prev));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex(prev => (prev > 0 ? prev - 1 : -1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (activeIndex >= 0) {
        handleSelect(suggestions[activeIndex]);
      }
    } else if (e.key === 'Escape') {
      setShowDropdown(false);
    }
  };

  const handleSelect = (item) => {
    onSelect(item);
    setShowDropdown(false);
    setSuggestions([]);
  };

  return (
    <div className="position-relative w-100">
      <input
        type="text"
        className={className}
        value={value}
        onChange={handleInputChange}
        onKeyDown={handleKeyDown}
        onFocus={() => { if (suggestions.length > 0) setShowDropdown(true); }}
        onBlur={() => setTimeout(() => setShowDropdown(false), 200)}
        placeholder={placeholder}
        autoComplete="off"
      />
      {showDropdown && suggestions.length > 0 && (
        <ul className="list-group shadow position-absolute w-100 bg-white" 
            style={{ zIndex: 1055, top: '100%', maxHeight: '200px', overflowY: 'auto', border: '1px solid #d8dee4' }}>
          {suggestions.map((s, i) => (
            <li
              key={i}
              ref={i === activeIndex ? activeItemRef : null}
              className={`list-group-item list-group-item-action py-2 cursor-pointer border-bottom ${i === activeIndex ? 'bg-light' : ''}`}
              style={i === activeIndex ? { backgroundColor: '#f1f5f9', color: '#1e293b' } : {}}
              onMouseDown={() => handleSelect(s)}
            >
              <div className="fw-bold">{s[displayKey]}</div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default Autocomplete;
