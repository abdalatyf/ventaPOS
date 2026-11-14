/**
 * Schedule delayed focus on a target ref only if the caller has not cancelled
 * and the user has not already focused another interactive control.
 */
export function scheduleIdleFocus(targetRef, delayMs = 150, shouldSkip = () => false) {
  return setTimeout(() => {
    if (shouldSkip()) return;
    const activeEl = document.activeElement;
    const userAlreadyFocusedField =
      activeEl &&
      activeEl !== document.body &&
      activeEl !== targetRef.current &&
      ['INPUT', 'TEXTAREA', 'SELECT', 'BUTTON'].includes(activeEl.tagName);
    if (!userAlreadyFocusedField) {
      targetRef.current?.focus();
    }
  }, delayMs);
}

/**
 * Schedule a short delayed focus transition (e.g. after selecting an autocomplete item
 * or adding a cart row) without stealing focus if the user/automation has already
 * moved focus to a different interactive element before the timer fires.
 */
export function scheduleTransitionFocus(targetRef, delayMs = 50) {
  const originEl = typeof document !== 'undefined' ? document.activeElement : null;
  return setTimeout(() => {
    const activeEl = typeof document !== 'undefined' ? document.activeElement : null;
    const movedToDifferentControl =
      activeEl &&
      activeEl !== document.body &&
      activeEl !== originEl &&
      activeEl !== targetRef?.current &&
      ['INPUT', 'TEXTAREA', 'SELECT', 'BUTTON'].includes(activeEl.tagName);
    if (!movedToDifferentControl) {
      targetRef?.current?.focus();
    }
  }, delayMs);
}

