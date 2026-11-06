import React, { useState, useRef, useEffect, useCallback, forwardRef } from 'react';
import { toEnglish } from '../../utils/formatUtils';

/**
 * AppAutocomplete — Unified Searchable Autocomplete Dropdown
 *
 * Supports both static options (`items`) and dynamic async searches (`fetchSuggestions`).
 * Supports RTL layout, Arabic/English digit normalization, arrow keyboard navigation,
 * clear button (x), forwardRef support for keyboard navigation chains, and high-contrast styling.
 */
const AppAutocomplete = forwardRef(function AppAutocomplete({
  items = [],
  fetchSuggestions = null,
  value = '',
  onChange = () => {},
  onSelect = () => {},
  displayKey = 'name',
  idKey = 'id',
  searchKeys = ['name', 'local_id'],
  placeholder = '',
  className = 'form-control',
  allowClear = true,
  debounceMs = 250,
  disabled = false,
  style = {},
  inputStyle = {},
  name,
  id,
  autoFocus = false,
  renderItem = null,
  onKeyDown = null,
  selectOnFocus = false,
}, ref) {
  const [suggestions, setSuggestions] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const [isLoading, setIsLoading] = useState(false);

  const containerRef = useRef(null);
  const localInputRef = useRef(null);
  const activeItemRef = useRef(null);
  const debounceTimerRef = useRef(null);
  const latestQueryRef = useRef('');

  // Use the forwarded ref if provided, otherwise local ref
  const inputRef = ref || localInputRef;

  const getItemLabel = useCallback((item) => {
    if (item === null || item === undefined) return '';
    if (typeof item === 'object') {
      return item[displayKey] ?? item.name ?? item.title ?? item.label ?? item.value ?? '';
    }
    return String(item);
  }, [displayKey]);

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
          if (latestQueryRef.current === text) {
            setSuggestions(Array.isArray(results) ? results : []);
            setIsOpen(true);
          }
        } catch (err) {
          console.error('AppAutocomplete error fetching suggestions:', err);
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
      const filtered = filterStaticItems(text, items);
      setSuggestions(filtered);
      setIsOpen(true);
    }
  };

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
    if (inputRef && inputRef.current) {
      inputRef.current.focus();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (!isOpen) {
        if (fetchSuggestions) {
          if (String(value).trim()) {
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
      if (isOpen && activeIndex >= 0 && suggestions[activeIndex]) {
        e.preventDefault();
        handleSelect(suggestions[activeIndex]);
      } else if (isOpen && suggestions.length === 1) {
        e.preventDefault();
        handleSelect(suggestions[0]);
      } else if (isOpen) {
        setIsOpen(false);
        if (onKeyDown) onKeyDown(e);
      } else {
        if (onKeyDown) onKeyDown(e);
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
    } else {
      if (onKeyDown) onKeyDown(e);
    }
  };

  const handleFocus = (e) => {
    if (disabled) return;
    if (selectOnFocus && e && e.target && typeof e.target.select === 'function') {
      e.target.select();
    }
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

  useEffect(() => {
    if (activeIndex >= 0 && activeItemRef.current) {
      activeItemRef.current.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    }
  }, [activeIndex]);

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
      <div className="input-icon w-100">
        <input
          ref={inputRef}
          type="text"
          name={name}
          id={id}
          className={`${className} ${hasValue && allowClear ? 'pe-4' : ''}`}
          style={{
            textAlign: 'right',
            direction: 'rtl',
            borderRadius: '4px',
            borderColor: isOpen ? '#206bc4' : undefined,
            ...inputStyle,
          }}
          placeholder={placeholder}
          value={localValue}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={handleFocus}
          disabled={disabled}
          autoFocus={autoFocus}
          autoComplete="off"
          spellCheck="false"
        />

        {isLoading && (
          <span
            className="input-icon-addon"
            style={{
              position: 'absolute',
              left: '10px',
              top: '50%',
              transform: 'translateY(-50%)',
              zIndex: 3,
            }}
          >
            <div className="spinner-border spinner-border-sm text-muted" role="status" />
          </span>
        )}

        {hasValue && allowClear && !disabled && !isLoading && (
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

      {isOpen && (
        <ul
          tabIndex="-1"
          className="list-group shadow position-absolute w-100 bg-white"
          onMouseDown={(e) => e.preventDefault()}
          style={{
            zIndex: 1055,
            top: '100%',
            marginTop: '2px',
            maxHeight: '220px',
            overflowY: 'auto',
            border: '1px solid #ced4da',
            borderRadius: '4px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
          }}
        >
          {suggestions.length > 0 ? (
            suggestions.map((item, index) => {
              const label = getItemLabel(item);
              const isSelected = index === activeIndex;

              return (
                <li
                  key={index}
                  ref={isSelected ? activeItemRef : null}
                  className={`list-group-item list-group-item-action py-2 px-3 border-bottom ${
                    isSelected ? 'bg-light' : ''
                  }`}
                  style={{
                    cursor: 'pointer',
                    backgroundColor: isSelected ? '#f1f5f9' : '#ffffff',
                    color: isSelected ? '#123F68' : '#212529',
                    fontSize: '0.875rem',
                    textAlign: 'right',
                    direction: 'rtl',
                  }}
                  onMouseDown={(e) => {
                    e.preventDefault();
                    handleSelect(item);
                  }}
                >
                  {renderItem ? (
                    renderItem(item, isSelected)
                  ) : typeof item === 'object' && (item.phone_number || item.area || item.max !== undefined) ? (
                    <div>
                      <div className="fw-bold">{label}</div>
                      <div className="text-muted small">
                        {item.phone_number && <span>{item.phone_number} </span>}
                        {item.area && <span>· {item.area} </span>}
                        {item.max !== undefined && <span className="badge bg-secondary-lt ms-2">المتاح: {item.max}</span>}
                      </div>
                    </div>
                  ) : (
                    <div className="fw-bold">{label}</div>
                  )}
                </li>
              );
            })
          ) : (
            <li
              className="list-group-item text-muted py-2 px-3 text-center"
              style={{ fontSize: '0.85rem' }}
            >
              لا توجد نتائج مطابقة
            </li>
          )}
        </ul>
      )}
    </div>
  );
});

export default AppAutocomplete;
