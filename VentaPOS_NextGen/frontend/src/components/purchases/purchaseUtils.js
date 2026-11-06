import api from '../../api';

export const toEnglish = (str) => {
  if (str === undefined || str === null) return '';
  return String(str)
    .replace(/[٠-٩]/g, (d) => '٠١٢٣٤٥٦٧٨٩'.indexOf(d))
    .replace(/×/g, '*')
    .replace(/،/g, ',');
};

export const checkSafeStockForReturn = async (productId, reqQty, month, year, existingQty = 0) => {
  let retries = 3;
  while (retries > 0) {
    try {
      const res = await api.get(`/inventory-items/${productId}/stock/?month=${month}&year=${year}`);
      if (res.data && res.data.safe_available_qty !== undefined) {
        const remaining = res.data.safe_available_qty + existingQty;
        return {
          ok: reqQty <= remaining,
          safeQty: remaining,
          error: reqQty > remaining ? `الكمية المطلوبة أكبر من المتاح: ${remaining}` : null
        };
      }
      break;
    } catch {
      retries--;
      if (retries > 0) await new Promise(r => setTimeout(r, 50));
    }
  }
  return { ok: true, safeQty: undefined, error: null };
};

export const fetchSuppliersList = async (branchId) => {
  try {
    const branch = branchId || localStorage.getItem('branchId');
    const url = branch ? `/suppliers/?branch_id=${branch}` : '/suppliers/';
    const res = await api.get(url);
    return res.data?.results || (Array.isArray(res.data) ? res.data : []);
  } catch (error) {
    console.error('Error fetching suppliers:', error);
    return [];
  }
};

export const fetchProductsMap = async (branchId) => {
  try {
    const branch = branchId || localStorage.getItem('branchId');
    const url = branch ? `/inventory-items/?limit=1000&branch_id=${branch}` : '/inventory-items/?limit=1000';
    const res = await api.get(url);
    const data = res.data?.results || res.data;
    if (Array.isArray(data)) {
      const pMap = {};
      data.forEach(p => { pMap[p.id] = p.name; });
      return pMap;
    }
    return {};
  } catch (error) {
    console.error('Error fetching inventory map:', error);
    return {};
  }
};

export const fetchPurchaseEntryInitialData = async (id, branchId) => {
  const branch = branchId || localStorage.getItem('branchId');
  const itemsUrl = branch ? `/inventory-items/?limit=5000&branch_id=${branch}` : '/inventory-items/?limit=5000';
  const suppsUrl = branch ? `/suppliers/?branch_id=${branch}` : '/suppliers/';
  const [suppliersRes, productsRes] = await Promise.all([
    api.get(suppsUrl).catch(() => ({ data: [] })),
    api.get(itemsUrl).catch(() => ({ data: [] }))
  ]);
  const suppData = suppliersRes.data?.results || suppliersRes.data;
  const prodData = productsRes.data?.results || productsRes.data;
  
  const supps = Array.isArray(suppData) ? suppData : [];
  const prods = Array.isArray(prodData) ? prodData : [];
  let invoiceData = null;

  if (id) {
    const invRes = await api.get(`/purchase-invoices/${id}/`);
    invoiceData = invRes.data;
  }
  return { supps, prods, invoiceData };
};
