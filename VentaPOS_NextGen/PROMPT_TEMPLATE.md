# VentaPOS NextGen — Standard Prompt Template

> Copy the template below for every task. Fill in the `[TASK]` section only.

---

## The Template

```text
Project: D:\Projects\VentaPOS\VentaPOS_NextGen
Rules: Read .agents/AGENTS.md before doing anything.
Task: [TODO SECTION NUMBER] — [SECTION TITLE]

## Phase 1: ANALYZE (Read-Only — NO changes)
Read every file involved in this task. List what you found:
- What exists in the code right now
- What works vs what's broken vs what's missing
- Any contradictions with requirements.md or AGENTS.md

## Phase 2: EXPLAIN (Talk to me — NO changes)
Explain in plain English:
- What each file does currently
- What needs to change and WHY
- Any risks or decisions I need to make

## Phase 3: PLAN (Propose — NO changes yet)
Create a numbered checklist of exact changes:
- Which files to modify/create/delete
- What specifically changes in each file
- Expected outcome after each change
Wait for my approval before proceeding.

## Phase 4: EXECUTE (Only after my approval)
Make the changes from the approved plan.
Do not modify existing tests to make new code pass.

## Phase 5: VERIFY (Mandatory Before Completion)
Run backend tests: `cd VentaPOS_NextGen\backend && D:\Projects\VentaPOS\VentaPOS_NextGen\venv\Scripts\python.exe manage.py test api.tests -v 2`
Run frontend build: `cd VentaPOS_NextGen\frontend && npm run build`
If tests/build fail, fix ONLY your code and re-run.
Update TODO.md — mark completed items as [x].
Output a Context Checkpoint summarizing the changes.

---

[TASK]
Items from TODO.md:
- [ ] (paste the specific tasks here)

Files involved:
- (list the files this task touches)

[CONSTRAINTS]
(Checklist-at-End: Place any specific constraints, red lines, or UI_UX_RULES here at the bottom of the prompt for maximum attention weighting)
```

---

## Examples

### Example 1: TODO Section 15

```text
Project: D:\Projects\VentaPOS\VentaPOS_NextGen
Rules: Read .agents/AGENTS.md before doing anything.
Task: Section 15 — Frontend: Reports

## Phase 1: ANALYZE
## Phase 2: EXPLAIN
## Phase 3: PLAN
## Phase 4: EXECUTE (Only after my approval)
## Phase 5: VERIFY

---

[TASK]
Items from TODO.md:
- [ ] Review/fix CashDrawerReport.jsx — cash flow

Files involved:
- frontend/src/pages/reports/CashDrawerReport.jsx
- backend/api/views.py

[CONSTRAINTS]
- Do NOT use raw HTML tables, use ReportTable.jsx
- No Tailwind CSS, use Tabler classes
```
