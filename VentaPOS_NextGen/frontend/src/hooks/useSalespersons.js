import { useState, useEffect } from 'react';
import api from '../../api';

export const useSalespersons = (branchId) => {
    const [salespersons, setSalespersons] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        let isMounted = true;
        const fetchSalespersons = async () => {
            if (!branchId) {
                setSalespersons([]);
                return;
            }
            setLoading(true);
            setError(null);
            try {
                const res = await api.get(`/api/v1/salespersons/?branch=${branchId}`);
                if (isMounted) {
                    const data = Array.isArray(res.data) ? res.data : (res.data?.results || []);
                    setSalespersons(data);
                }
            } catch (err) {
                if (isMounted) {
                    setError('فشل تحميل قائمة المناديب. حاول مرة أخرى.');
                }
            } finally {
                if (isMounted) {
                    setLoading(false);
                }
            }
        };

        fetchSalespersons();
        return () => { isMounted = false; };
    }, [branchId]);

    return { salespersons, loading, error, setSalespersons };
};
