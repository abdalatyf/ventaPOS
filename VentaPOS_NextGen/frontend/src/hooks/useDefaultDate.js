import { useState, useEffect } from 'react';
import api from '../api';

export function useDefaultDate(branchId) {
    const [defaultYear, setDefaultYear] = useState(new Date().getFullYear());
    const [defaultMonth, setDefaultMonth] = useState(new Date().getMonth() + 1);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let isMounted = true;
        const fetchDate = async () => {
            try {
                const res = await api.get('/default-date/', {
                    params: branchId ? { branch_id: branchId } : {}
                });
                if (isMounted && res.data && res.data.year && res.data.month) {
                    setDefaultYear(res.data.year);
                    setDefaultMonth(res.data.month);
                }
            } catch (err) {
                console.error("Failed to fetch default date:", err);
            } finally {
                if (isMounted) setLoading(false);
            }
        };

        fetchDate();
        return () => { isMounted = false; };
    }, [branchId]);

    return { defaultYear, defaultMonth, loading };
}
