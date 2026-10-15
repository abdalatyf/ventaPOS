import React, { useState, useRef, useEffect, useCallback } from 'react';
import { toEnglish } from '../utils/formatUtils';

/**
 * ReportAutocomplete — Unified Searchable Autocomplete Dropdown for Reports
 * 
 * Supports both static options (`items`) and dynamic server searches (`fetchSuggestions`).
 * Fully supports RTL layout, Arabic/English digit normalization, keyboard navigation,
 * clear button (x), and high-contrast styling.
 * 
 * @param {Object} props
 * @param {Array<Object|string>} [props.items=[]] - Static list of options for client-side search
 * @param {Function} [props.fetchSuggestions] - Async search function: (query: string) => Promise<Array>
 * @param {string} [props.value=''] - Current text value in the input field
 * @param {Function} props.onChange - Input text change handler: (text: string) => void
 * @param {Function} props.onSelect - Selection handler: (item: Object|string|null) => void
 * @param {string} [props.displayKey='name'] - Object key to display in input and list
 * @param {string} [props.idKey='id'] - Object key for unique identifier
 * @param {Array<string>} [props.searchKeys=['name', 'local_id']] - Object keys to match in client-side search
 * @param {string} [props.placeholder=''] - Input placeholder in Arabic
 * @param {string} [props.className='form-control form-control-sm'] - Bootstrap / Tabler input class
 * @param {boolean} [props.allowClear=true] - Whether to show clear (x) button when text is present
 * @param {number} [props.debounceMs=250] - Debounce delay in milliseconds for async fetching
 * @param {boolean} [props.disabled=false] - Whether the input is disabled
 * @param {Object} [props.style] - Container style overrides
 * @param {Object} [props.inputStyle] - Input style overrides
 * @param {string} [props.name] - HTML name attribute for input
 * @param {string} [props.id] - HTML id attribute for input
 * @param {boolean} [props.autoFocus=false] - Auto focus on mount
 */
export default function ReportAutocomplete({
  items = [],
  fetchSuggestions = null,
  value = '',
  onChange = () => {},
  onSelect = () => {},
  displayKey = 'name',
  idKey = 'id',
  searchKeys = ['name', 'local_id'],
  placeholder = '',
  className = 'form-control form-control-sm',
  allowClear = true,
  debounceMs = 250,
  disabled = false,
  style = {},
  inputStyle = {},
  name,
  id,
  autoFocus = false,
}) {
  const [suggestions, setSuggestions] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const [isLoading, setIsLoading] = useState(false);

  const containerRef = useRef(null);
  const inputRef = useRef(null);
  const activeItemRef = useRef(null);
  const debounceTimerRef = useRef(null);
  const latestQueryRef = useRef('');

  // Helper to extract display label from an item
  const getItemLabel = useCallback((item) => {
    if (item === null || item === undefined) return '';
    if (typeof item === 'object') {
      return item[displayKey] ?? item.name ?? item.title ?? item.label ?? '';
    }
    return String(item);
  }, [displayKey]);

  // Helper to filter static items client-side
  const filterStaticItems = useCallback((query, sourceItems) => {
    if (!sourceItems || !Array.isArray(sourceItems)) return [];
    if (!query || !query.trim()) {
      return sourceItems.slice(0, 50);
    }

    const cleanQuery = query.trim().toLowerCase();
    const queryEn = toEnglish(cleanQuery);
    const queryAr = cleanQuery;

    return sourceItems.filter((item) => {
      if (item === null || item === undefined) return false;
      if (typeof item !== 'object') {
        const itemStr = String(item).toLowerCase();
        const itemEn = toEnglish(itemStr);
        return itemStr.includes(cleanQuery) || itemEn.includes(queryEn) || itemStr.includes(queryAr);
      }

      // Check configured search keys
      const keysToCheck = Array.from(new Set([...searchKeys, displayKey, idKey]));
      return keysToCheck.some((key) => {
        const fieldVal = item[key];
        if (fieldVal === null || fieldVal === undefined) return false;
        const fieldStr = String(fieldVal).toLowerCase();
        const fieldEn = toEnglish(fieldStr);
        return fieldStr.includes(cleanQuery) || fieldEn.includes(queryEn) || fieldStr.includes(queryAr);
      });
    }).slice(0, 50);
  }, [searchKeys, displayKey, idKey]);

  const [localValue, setLocalValue] = useState(value || '');
  const debounceOnChangeRef = useRef(null);

  useEffect(() => {
    setLocalValue(value || '');
  }, [value]);

  // Handle Input typing
  const handleInputChange = (e) => {
    const text = e.target.value;
    setLocalValue(text);
    setActiveIndex(-1);

    if (debounceOnChangeRef.current) {
      clearTimeout(debounceOnChangeRef.current);
    }
    debounceOnChangeRef.current = setTimeout(() => {
      onChange(text);
    }, debounceMs);

    if (fetchSuggestions) {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }

      if (!text.trim()) {
        latestQueryRef.current = '';
        setSuggestions([]);
        setIsOpen(false);
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      latestQueryRef.current = text;

      debounceTimerRef.current = setTimeout(async () => {
        try {
          const results = await fetchSuggestions(text);
          // Only update if query hasn't changed in the meantime
          if (latestQueryRef.current === text) {
            setSuggestions(Array.isArray(results) ? results : []);
            setIsOpen(true);
          }
        } catch (err) {
          console.error('ReportAutocomplete error fetching suggestions:', err);
          if (latestQueryRef.current === text) {
            setSuggestions([]);
          }
        } finally {
          if (latestQueryRef.current === text) {
            setIsLoading(false);
          }
        }
      }, debounceMs);
    } else {
      // Synchronous static filter
      const filtered = filterStaticItems(text, items);
      setSuggestions(filtered);
      setIsOpen(true);
    }
  };

  // Handle Option Selection
  const handleSelect = (item) => {
    if (debounceOnChangeRef.current) clearTimeout(debounceOnChangeRef.current);
    if (!item) {
      setLocalValue('');
      onChange('');
      onSelect(null);
      setSuggestions([]);
      setIsOpen(false);
      setActiveIndex(-1);
      return;
    }

    const label = getItemLabel(item);
    setLocalValue(label);
    onChange(label);
    onSelect(item);
    setSuggestions([]);
    setIsOpen(false);
    setActiveIndex(-1);
  };

  // Handle Clear (x) button
  const handleClear = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (debounceOnChangeRef.current) clearTimeout(debounceOnChangeRef.current);
    setLocalValue('');
    onChange('');
    onSelect(null);
    setSuggestions([]);
    setIsOpen(false);
    setActiveIndex(-1);
    if (inputRef.current) {
      inputRef.current.focus();
    }
  };

  // Keyboard navigation
  const handleKeyDown = (e) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (!isOpen) {
        // Open dropdown on down arrow
        if (fetchSuggestions) {
          if (value.trim()) {
            setIsLoading(true);
            fetchSuggestions(value).then((res) => {
              setSuggestions(Array.isArray(res) ? res : []);
              setIsOpen(true);
              setIsLoading(false);
            });
          }
        } else {
          setSuggestions(filterStaticItems(value, items));
          setIsOpen(true);
        }
        return;
      }
      if (suggestions.length > 0) {
        setActiveIndex((prev) => (prev < suggestions.length - 1 ? prev + 1 : 0));
      }
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (isOpen && suggestions.length > 0) {
        setActiveIndex((prev) => (prev > 0 ? prev - 1 : suggestions.length - 1));
      }
    } else if (e.key === 'Enter') {
      // Prevent submitting parent form
      e.preventDefault();
      if (isOpen && activeIndex >= 0 && suggestions[activeIndex]) {
        handleSelect(suggestions[activeIndex]);
      } else if (isOpen && suggestions.length === 1) {
        handleSelect(suggestions[0]);
      } else if (isOpen) {
        setIsOpen(false);
      }
    } else if (e.key === 'Escape') {
      e.preventDefault();
      setIsOpen(false);
      setActiveIndex(-1);
    } else if (e.key === 'Tab') {
      if (isOpen && activeIndex >= 0 && suggestions[activeIndex]) {
        handleSelect(suggestions[activeIndex]);
      } else {
        setIsOpen(false);
      }
    }
  };

  // On Focus: open list with current items or filtered items
  const handleFocus = () => {
    if (disabled) return;
    if (!fetchSuggestions) {
      const filtered = filterStaticItems(value, items);
      setSuggestions(filtered);
      if (filtered.length > 0) {
        setIsOpen(true);
      }
    } else if (suggestions.length > 0) {
      setIsOpen(true);
    }
  };

  // Scroll active item into view
  useEffect(() => {
    if (activeIndex >= 0 && activeItemRef.current) {
      activeItemRef.current.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    }
  }, [activeIndex]);

  // Click outside listener to close dropdown
  useEffect(() => {
    const handleOutsideClick = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setIsOpen(false);
        setActiveIndex(-1);
      }
    };
    document.addEventListener('mousedown', handleOutsideClick);
    return () => {
      document.removeEventListener('mousedown', handleOutsideClick);
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, []);

  const hasValue = Boolean(localValue && String(localValue).trim().length > 0);

  return (
    <div 
      ref={containerRef} 
      className="position-relative d-inline-block w-100" 
      style={{ minWidth: '130px', ...style }}
    >
      <div className="position-relative w-100">
        <input
          ref={inputRef}
          type="text"
          name={name}
          id={id}
          className={className}
          value={localValue || ''}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={handleFocus}
          placeholder={placeholder}
          disabled={disabled}
          autoFocus={autoFocus}
          autoComplete="off"
          style={{
            paddingLeft: allowClear && hasValue ? '28px' : undefined,
            ...inputStyle,
          }}
        />

        {/* Clear (x) button positioned on left side in RTL */}
        {allowClear && hasValue && !disabled && (
          <button
            type="button"
            className="btn btn-sm btn-link p-0 position-absolute text-muted text-decoration-none"
            style={{
              left: '8px',
              top: '50%',
              transform: 'translateY(-50%)',
              lineHeight: 1,
              fontSize: '15px',
              cursor: 'pointer',
              zIndex: 5,
            }}
            onClick={handleClear}
            tabIndex={-1}
            title="مسح"
            aria-label="مسح"
          >
            &times;
          </button>
        )}

        {/* Loading Spinner */}
        {isLoading && (
          <span 
            className="spinner-border spinner-border-sm text-primary position-absolute"
            style={{
              left: allowClear && hasValue ? '26px' : '8px',
              top: '50%',
              transform: 'translateY(-50%)',
              width: '12px',
              height: '12px',
              borderWidth: '2px',
              zIndex: 4,
            }}
          />
        )}
      </div>

      {/* Dropdown Menu */}
      {isOpen && (
        <ul
          className="list-group shadow-lg position-absolute w-100 bg-white border rounded"
          style={{
            zIndex: 1060,
            top: '100%',
            right: 0,
            left: 0,
            marginTop: '2px',
            maxHeight: '220px',
            overflowY: 'auto',
            borderColor: '#ced4da',
            padding: 0,
            listStyle: 'none',
          }}
        >
          {isLoading && suggestions.length === 0 ? (
            <li className="list-group-item text-center py-2 text-muted small">
              <span className="spinner-border spinner-border-sm me-2 text-primary" />
              جاري البحث...
            </li>
          ) : suggestions.length > 0 ? (
            suggestions.map((item, index) => {
              const label = getItemLabel(item);
              const isActive = index === activeIndex;
              const subId = typeof item === 'object' ? (item[idKey] ?? item.local_id ?? item.id) : null;
              const subArea = typeof item === 'object' ? item.area : null;

              return (
                <li
                  key={typeof item === 'object' && item[idKey] ? item[idKey] : index}
                  ref={isActive ? activeItemRef : null}
                  className={`list-group-item list-group-item-action py-2 px-3 cursor-pointer d-flex justify-content-between align-items-center ${
                    isActive ? 'bg-light text-primary fw-bold' : ''
                  }`}
                  style={{
                    backgroundColor: isActive ? '#e7f1ff' : '#ffffff',
                    color: isActive ? '#123f68' : '#212529',
                    borderBottom: '1px solid #f1f3f5',
                    cursor: 'pointer',
                    fontSize: '0.875rem',
                  }}
                  onMouseDown={(e) => {
                    // Prevent blur before select
                    e.preventDefault();
                    handleSelect(item);
                  }}
                  onMouseEnter={() => setActiveIndex(index)}
                >
                  <span className="text-truncate">{label}</span>
                  {(subArea || subId !== undefined) && (
                    <span className="badge bg-secondary-subtle text-secondary small ms-2">
                      {subArea ? subArea : subId !== null && subId !== undefined ? `#${subId}` : ''}
                    </span>
                  )}
                </li>
              );
            })
          ) : (
            <li className="list-group-item text-center py-2 text-muted small">
              لا توجد نتائج
            </li>
          )}
        </ul>
      )}
    </div>
  );
}
