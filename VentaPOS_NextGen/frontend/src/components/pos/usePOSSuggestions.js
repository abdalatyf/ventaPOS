import { useState, useRef } from 'react';
import api from '../../api';
import { toEnglish } from './posUtils';

export default function usePOSSuggestions({
  salespersons,
  saleMonth,
  saleYear,
  customerName,
  setCustomerName,
  phoneNumber,
  setPhoneNumber,
  area,
  setArea,
  address,
  setAddress,
  salespersonId,
  setSalespersonId,
  setSalespersonQuery,
  isCashSale,
  setSelectedProduct,
  setProductQuery,
  setSellPrice,
  items,
  qtyRef
}) {
  const [suggestions, setSuggestions] = useState([]);
  const [activeInput, setActiveInput] = useState('');
  const [activeIndex, setActiveIndex] = useState(-1);
  const suggestTimerRef = useRef(null);
  const blurTimerRef = useRef(null);
  const activeRequestFieldRef = useRef(null);

  const triggerSuggestions = (val, fieldType) => {
    clearTimeout(suggestTimerRef.current);
    clearTimeout(blurTimerRef.current);
    const term = toEnglish(val).trim();

    if (fieldType === 'salesperson') {
      const q = term.toLowerCase();
      const filtered = salespersons.filter(s => s.name && s.name.toLowerCase().includes(q));
      setSuggestions(filtered);
      setActiveInput(fieldType);
      setActiveIndex(-1);
      return;
    }

    activeRequestFieldRef.current = fieldType;
    suggestTimerRef.current = setTimeout(async () => {
      try {
        let url = '';
        const bId = localStorage.getItem('branchId') || '';
        if (fieldType === 'product') {
          url = `/product-suggestions/?term=${encodeURIComponent(term)}&month=${saleMonth}&year=${saleYear}&branch_id=${bId}`;
        } else {
          const currentArea = toEnglish(area);
          const currentName = toEnglish(customerName);
          url = `/customer-suggestions/?term=${encodeURIComponent(term)}&field=${fieldType}&salesperson_id=${salespersonId}&current_area=${encodeURIComponent(currentArea)}&current_name=${encodeURIComponent(currentName)}&branch_id=${bId}`;
        }

        const res = await api.get(url);
        if (activeRequestFieldRef.current !== fieldType) return;
        
        const data = res.data?.results || res.data;
        const list = Array.isArray(data) ? data : [];
        
        if (fieldType === 'product') {
          setSuggestions(list.slice(0, 10));
        } else {
          setSuggestions(list.map(item => ({ value: item.value })).slice(0, 10));
        }

        setActiveInput(fieldType);
        setActiveIndex(-1);
      } catch {
        setSuggestions([]);
      }
    }, 300);
  };

  const handleKeyDown = (e, fieldType) => {
    if (activeInput !== fieldType || !suggestions.length) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex(prev => (prev + 1) % suggestions.length);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex(prev => (prev - 1 + suggestions.length) % suggestions.length);
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (activeIndex > -1) {
        handleSuggestionSelect(suggestions[activeIndex], fieldType);
      } else if (suggestions.length > 0) {
        handleSuggestionSelect(suggestions[0], fieldType);
      }
    }
  };

  const handleSuggestionSelect = (item, fieldType) => {
    if (fieldType === 'salesperson') {
      setSalespersonId(item.id);
      setSalespersonQuery(item.name);
    } else if (fieldType === 'product') {
      setSelectedProduct(item);
      setProductQuery(item.value);
      setSellPrice(isCashSale ? (item.cash_price || '') : (item.installment_price || ''));
      setTimeout(() => qtyRef.current?.focus(), 50);
      api.get(`/inventory-items/${item.id}/stock/?month=${saleMonth}&year=${saleYear}`)
         .then(res => {
           if (res.data && res.data.safe_available_qty !== undefined) {
             const existing = items.find(i => i.inventory_item === item.id);
             const remaining = res.data.safe_available_qty - (existing ? existing.quantity : 0);
             setSelectedProduct(prev => prev && prev.id === item.id ? { 
               ...prev, 
               safe_qty: remaining,
               bottleneck_month: res.data.bottleneck_month,
               bottleneck_year: res.data.bottleneck_year
             } : prev);
           }
         }).catch(() => {});
    } else {
      const arabicVal = item.value;
      if (fieldType === 'name') setCustomerName(arabicVal);
      else if (fieldType === 'area') setArea(arabicVal);
      else if (fieldType === 'address') setAddress(arabicVal);
      else if (fieldType === 'phone') setPhoneNumber(arabicVal);
    }
    setSuggestions([]);
    setActiveInput('');
    setActiveIndex(-1);
  };

  return {
    suggestions,
    setSuggestions,
    activeInput,
    setActiveInput,
    activeIndex,
    triggerSuggestions,
    handleKeyDown,
    handleSuggestionSelect,
    blurTimerRef
  };
}
