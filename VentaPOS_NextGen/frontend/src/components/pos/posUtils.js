import api from '../../api';
import {
  toEnglish as baseToEnglish,
  parseStrictInt,
  parseWholeMoney,
  parseValidMonthYear,
} from '../../utils/formatUtils';

export const fmt = (n) => Math.round(parseFloat(n) || 0).toLocaleString('en-US');

export const toEnglish = (str) => baseToEnglish(str).replace(/×/g, '*');

export function genSchedule(count, amount, startMonth, startYear) {
  const validDate = parseValidMonthYear(startMonth, startYear, { minYear: 2000, maxYear: 2100 });
  const countInt = parseStrictInt(count, { min: 1, max: 360 });
  const amtInt = parseWholeMoney(amount, { min: 1 });
  if (!validDate || countInt === null || amtInt === null) return [];

  const rows = [];
  let m = validDate.month;
  let y = validDate.year;
  for (let i = 0; i < countInt; i++) {
    m++;
    if (m > 12) {
      m = 1;
      y++;
    }
    rows.push({ payment_month: m, payment_year: y, amount: amtInt });
  }
  return rows;
}

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
      let v1 = parseInt(val1, 10) || 0;
      let v2 = parseInt(val2, 10) || 0;
      let amount, count;
      if (v2 > v1 && v1 <= 60) {
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
    .map((s) => ({
      count: parseStrictInt(s.count, { min: 1 }),
      amount: parseWholeMoney(s.amount, { min: 1 }),
    }))
    .filter((s) => s.count !== null && s.amount !== null)
    .map((s) => `${s.amount}*${s.count}`);
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
  prodQueryRef,
  addingItemRef,
}) => {
  if (addingItemRef?.current) return;
  if (addingItemRef) addingItemRef.current = true;

  try {
    setItemError('');
    const validDate = parseValidMonthYear(saleMonth, saleYear, { minYear: 2000, maxYear: 2100 });
    if (!validDate) {
      setItemError('أدخل شهر وسنة صحيحين.');
      return;
    }

    let currentProduct = selectedProduct;
    if (!currentProduct && productQuery.trim() !== '') {
      try {
        const bId = localStorage.getItem('branchId') || '';
        const res = await api.get(`/product-suggestions/?term=${encodeURIComponent(productQuery.trim())}&month=${validDate.month}&year=${validDate.year}&branch_id=${bId}`);
        const list = Array.isArray(res.data) ? res.data : (res.data?.results || []);
        const exactMatch = list.find(p => p.value === productQuery.trim());
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

    const qtyInt = parseStrictInt(quantity, { min: 1 });
    if (qtyInt === null) {
      setItemError('الكمية يجب أن تكون رقمًا صحيحًا (1 على الأقل).');
      return;
    }

    const priceInt = parseWholeMoney(sellPrice, { min: 1 });
    if (priceInt === null) {
      setItemError('أدخل سعر بيع صحيح (1 على الأقل).');
      return;
    }

    const existing = items.find(i => i.inventory_item === currentProduct.id);
    const reqQty = qtyInt + (existing ? existing.quantity : 0);
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
          const res = await api.get(`/inventory-items/${currentProduct.id}/stock/?month=${validDate.month}&year=${validDate.year}`);
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

    setItems(prev => {
      const prevExisting = prev.find(i => i.inventory_item === currentProduct.id);
      if (prevExisting) {
        const nextQty = prevExisting.quantity + qtyInt;
        if (safeQty !== undefined && nextQty > safeQty) {
          return prev;
        }
        return prev.map(i => i.inventory_item === currentProduct.id
          ? { ...i, quantity: nextQty, sell_price: priceInt, safe_qty: safeQty !== undefined ? safeQty : i.safe_qty }
          : i
        );
      }
      return [...prev, {
        id: Date.now(),
        inventory_item: currentProduct.id,
        productName: currentProduct.value,
        quantity: qtyInt,
        sell_price: priceInt,
        safe_qty: safeQty,
      }];
    });
    setProductQuery(''); setSelectedProduct(null); setQuantity(1); setSellPrice('');
    setTimeout(() => prodQueryRef.current?.focus(), 50);
  } finally {
    if (addingItemRef) addingItemRef.current = false;
  }
};
