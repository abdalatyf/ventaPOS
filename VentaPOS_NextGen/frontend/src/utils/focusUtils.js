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
