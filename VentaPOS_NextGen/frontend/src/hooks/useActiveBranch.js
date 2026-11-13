import { useState, useEffect, useCallback } from 'react';

const BRANCH_CHANGED_EVENT = 'branch_changed';

function readStoredBranch() {
  const rawId = localStorage.getItem('branchId');
  const branchName = localStorage.getItem('branchName') || '';
  return {
    branchId: rawId ? String(rawId) : null,
    branchName,
  };
}

/**
 * Sets the active branch in localStorage and broadcasts a same-tab custom event
 * so all mounted forms and tables react immediately to branch switches.
 */
export function setActiveBranch(branchId, branchName = '') {
  if (branchId === null || branchId === undefined || branchId === '') {
    localStorage.removeItem('branchId');
    localStorage.removeItem('branchName');
  } else {
    localStorage.setItem('branchId', String(branchId));
    if (branchName !== undefined && branchName !== null) {
      localStorage.setItem('branchName', String(branchName));
    }
  }
  window.dispatchEvent(
    new CustomEvent(BRANCH_CHANGED_EVENT, {
      detail: {
        branchId: branchId ? String(branchId) : null,
        branchName: branchName || localStorage.getItem('branchName') || '',
      },
    })
  );
}

/**
 * Reactive hook tracking active branchId & branchName across both same-tab
 * (`branch_changed`) and cross-tab (`storage`) branch switches.
 */
export function useActiveBranch() {
  const [branchState, setBranchState] = useState(readStoredBranch);

  useEffect(() => {
    const syncBranch = () => {
      const next = readStoredBranch();
      setBranchState((prev) =>
        prev.branchId === next.branchId && prev.branchName === next.branchName
          ? prev
          : next
      );
    };

    const handleStorage = (e) => {
      if (!e || e.key === null || e.key === 'branchId' || e.key === 'branchName') {
        syncBranch();
      }
    };

    window.addEventListener(BRANCH_CHANGED_EVENT, syncBranch);
    window.addEventListener('storage', handleStorage);
    return () => {
      window.removeEventListener(BRANCH_CHANGED_EVENT, syncBranch);
      window.removeEventListener('storage', handleStorage);
    };
  }, []);

  const updateBranch = useCallback((id, name) => {
    setActiveBranch(id, name);
  }, []);

  return {
    branchId: branchState.branchId,
    branchName: branchState.branchName,
    setActiveBranch: updateBranch,
  };
}

export default useActiveBranch;
