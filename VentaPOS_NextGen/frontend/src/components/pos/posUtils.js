import api from '../../api';

export const fmt = (n) => Math.round(parseFloat(n) || 0).toLocaleString('en-US');

export function genSchedule(count, amount, startMonth, startYear) {
  const rows = [];
  let m = parseInt(startMonth), y = parseInt(startYear);
  let countInt = parseInt(count || 0);
  if (countInt > 360) countInt = 360;
  for (let i = 0; i < countInt; i++) {
    m++; if (m > 12) { m = 1; y++; }
    if (parseFloat(amount) > 0) rows.push({ payment_month: m, payment_year: y, amount: parseFloat(amount) });
  }
  return rows;
}

export const toEnglish = (str) => {
  if (str === undefined || str === null) return '';
  return String(str)
    .replace(/[٠-٩]/g, (d) => '٠١٢٣٤٥٦٧٨٩'.indexOf(d))
    .replace(/×/g, '*')
    .replace(/،/g, ',');
};

export const parseInstallmentTextToBoxes = (textVal) => {
  const cleanText = toEnglish(textVal);
  const parts = cleanText.split('+');
  const newSystems = [
    { count: '', amount: '' },
    { count: '', amount: '' },
    { count: '', amount: '' }
  ];

  parts.forEach((part, index) => {
    if (index >= 3) return;
    let [val1, val2] = part.trim().split('*');
    if (val1 && val2) {
      let v1 = parseInt(val1) || 0;
      let v2 = parseInt(val2) || 0;
      let amount, count;
      if (v2 > 20) {
        amount = v2;
        count = v1;
      } else {
        amount = v1;
        count = v2;
      }
      newSystems[index] = {
        count: count,
        amount: amount
      };
    }
  });
  return newSystems;
};

export const formatBoxesToInstallmentText = (sysArray) => {
  const parts = sysArray
    .filter(s => s.count && s.amount && parseInt(toEnglish(s.count)) !== 0 && parseFloat(toEnglish(s.amount)) !== 0)
    .map(s => `${toEnglish(s.amount)}*${toEnglish(s.count)}`);
  return parts.join('+');
};

export const addItemToCart = async ({
  selectedProduct,
  productQuery,
  saleMonth,
  saleYear,
  quantity,
  sellPrice,
  items,
  setItems,
  setItemError,
  setProductQuery,
  setSelectedProduct,
  setQuantity,
  setSellPrice,
  prodQueryRef
}) => {
  setItemError('');
  let currentProduct = selectedProduct;
  if (!currentProduct && productQuery.trim() !== '') {
    try {
      const bId = localStorage.getItem('branchId') || '';
      const res = await api.get(`/product-suggestions/?term=${encodeURIComponent(productQuery.trim())}&month=${saleMonth}&year=${saleYear}&branch_id=${bId}`);
      const exactMatch = res.data.find(p => p.value === productQuery.trim());
      if (exactMatch) {
        currentProduct = exactMatch;
      } else {
        setItemError('يرجى اختيار منتج أولاً أو كتابة اسمه بدقة.');
        return;
      }
    } catch {
      setItemError('خطأ في الاتصال أثناء التحقق من المنتج.');
      return;
    }
  } else if (!currentProduct) {
    setItemError('يرجى اختيار منتج أولاً أو كتابة اسمه بدقة.');
    return;
  }
  if (!quantity || quantity < 1) { setItemError('الكمية يجب أن تكون 1 على الأقل.'); return; }
  if (!sellPrice || parseFloat(sellPrice) <= 0) { setItemError('أدخل سعر صحيح.'); return; }

  const existing = items.find(i => i.inventory_item === currentProduct.id);
  const reqQty = parseInt(quantity) + (existing ? existing.quantity : 0);
  let safeQty = currentProduct.safe_qty;

  if (safeQty !== undefined) {
    if (reqQty > safeQty) {
      setItemError(`الكمية المطلوبة أكبر من المتاح بأمان: ${safeQty}`);
      return;
    }
  } else {
    let retries = 3;
    while (retries > 0) {
      try {
        const res = await api.get(`/inventory-items/${currentProduct.id}/stock/?month=${saleMonth}&year=${saleYear}`);
        if (res.data && res.data.safe_available_qty !== undefined) {
          safeQty = res.data.safe_available_qty;
          if (reqQty > safeQty) {
            setItemError(`الكمية المطلوبة أكبر من المتاح بأمان: ${safeQty}`);
            return;
          }
        }
        break;
      } catch {
        retries--;
        if (retries > 0) await new Promise(r => setTimeout(r, 50));
      }
    }
  }

  if (existing) {
    setItems(items.map(i => i.inventory_item === currentProduct.id
      ? { ...i, quantity: reqQty, sell_price: parseFloat(sellPrice), safe_qty: safeQty !== undefined ? safeQty : i.safe_qty } : i));
  } else {
    setItems([...items, {
      id: Date.now(), 
      inventory_item: currentProduct.id,
      productName: currentProduct.value,
      quantity: parseInt(quantity), 
      sell_price: parseFloat(sellPrice),
      safe_qty: safeQty,
    }]);
  }
  setProductQuery(''); setSelectedProduct(null); setQuantity(1); setSellPrice('');
  setTimeout(() => prodQueryRef.current?.focus(), 50);
};
