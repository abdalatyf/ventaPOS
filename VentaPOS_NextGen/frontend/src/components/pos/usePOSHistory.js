import { useState, useEffect } from 'react';
import api from '../../api';

export default function usePOSHistory({
  setCustomerName,
  setPhoneNumber,
  setArea,
  setAddress
}) {
  const [historyCursors, setHistoryCursors] = useState({ name: null, phone: null, area: null, address: null });

  const handleHistoryCursor = async (fieldType, direction) => {
    try {
      const currentCursor = historyCursors[fieldType];
      const bId = localStorage.getItem('branchId') || '';
      let url = `/receipts-history-cursor/?direction=${direction}&branch_id=${bId}`;
      if (currentCursor !== null && currentCursor !== undefined) {
        url += `&current_receipt_number=${currentCursor}`;
      } else if (direction === 'next') {
        return;
      }
      
      const res = await api.get(url);
      
      if (res.data && res.data.receipt_number) {
        setHistoryCursors(prev => ({ ...prev, [fieldType]: res.data.receipt_number }));
        
        let val = '';
        if (fieldType === 'name') val = res.data.customer_name;
        else if (fieldType === 'phone') val = res.data.phone_number;
        else if (fieldType === 'area') val = res.data.area;
        else if (fieldType === 'address') val = res.data.address;
        
        const arabicVal = val || '';
        if (fieldType === 'name') setCustomerName(arabicVal);
        else if (fieldType === 'phone') setPhoneNumber(arabicVal);
        else if (fieldType === 'area') setArea(arabicVal);
        else if (fieldType === 'address') setAddress(arabicVal);
        
      } else if (direction === 'next' && (!res.data || !res.data.receipt_number)) {
        setHistoryCursors(prev => ({ ...prev, [fieldType]: null }));
        if (fieldType === 'name') setCustomerName('');
        else if (fieldType === 'phone') setPhoneNumber('');
        else if (fieldType === 'area') setArea('');
        else if (fieldType === 'address') setAddress('');
      }
    } catch (err) {
      console.log('No history found');
    }
  };

  useEffect(() => {
    const handleGlobalKeyDown = (e) => {
      if (e.altKey && (e.key === 'ArrowLeft' || e.key === 'ArrowRight')) {
        const activeElem = document.activeElement;
        let fieldType = null;
        if (activeElem && activeElem.id) {
          if (activeElem.id === 'input_name') fieldType = 'name';
          else if (activeElem.id === 'input_phone') fieldType = 'phone';
          else if (activeElem.id === 'input_area') fieldType = 'area';
          else if (activeElem.id === 'input_address') fieldType = 'address';
        }
        
        if (fieldType) {
          e.preventDefault();
          e.stopPropagation();
          if (e.key === 'ArrowRight') handleHistoryCursor(fieldType, 'prev');
          if (e.key === 'ArrowLeft') handleHistoryCursor(fieldType, 'next');
        }
      }
    };
    window.addEventListener('keydown', handleGlobalKeyDown, { capture: true });
    return () => window.removeEventListener('keydown', handleGlobalKeyDown, { capture: true });
  }, [historyCursors]);

  return { historyCursors, setHistoryCursors };
}
