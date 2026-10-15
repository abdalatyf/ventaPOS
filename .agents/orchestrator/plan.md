# VentaPOS NextGen Docs Restructure and Codebase Scan Plan

This plan outlines the steps to scan the codebase, analyze the documentation, identify gaps, update the documentation hub, and implement a programmatic verification script.

## Phase 1: Exploration and Scanning
### Step 1: Scan and Summarize Existing Documentation
- **Objective**: Identify all pages, components, and API endpoints already documented.
- **Subagent**: `teamwork_preview_explorer` (docs_explorer)
- **Task**:
  - Read all markdown files in `D:\Projects\VentaPOS\VentaPOS_NextGen\docs\`.
  - Extract all documented frontend pages/routes and backend endpoints.
  - Produce a structured registry of documented entities.
  - Suggest any potential documentation restructuring.
- **Verification**: Handoff report listing all documented items.

### Step 2: Scan Codebase for Frontend Routes and Backend API Endpoints
- **Objective**: Discover all actual frontend routes and backend endpoints.
- **Subagent**: `teamwork_preview_explorer` (code_explorer)
- **Task**:
  - Scan `frontend/src/` (especially `App.jsx` and pages) to compile all frontend routes and page components.
  - Scan `backend/api/` (especially `urls.py`, `views.py`, etc.) to compile all API endpoints.
  - Produce a structured registry of actual codebase routes and endpoints.
- **Verification**: Handoff report listing all codebase items.

## Phase 2: Gap Analysis and Documentation Update
### Step 3: Identify Gaps (Undocumented Features)
- **Objective**: Reconcile codebase scan against existing docs to find new undocumented features.
- **Task**:
  - Compare registries from Step 1 and Step 2.
  - Identify pages/routes and endpoints that are NOT documented in the existing markdown files.
  - Exclude the old TODO items (as they are already documented or will be cleared).
- **Verification**: A clear markdown list of gaps.

### Step 4: Restructure Docs & Update Master Index (`docs/index.md`)
- **Objective**: Organize docs, update links/summaries, and populate the Missing Documentation list.
- **Subagent**: `teamwork_preview_worker` (docs_updater)
- **Task**:
  - Cleanly organize/restructure any docs folders/files if needed.
  - Update `docs/index.md` with:
    - Relative links and 1-line summaries for all markdown documentation files.
    - An updated "Missing Documentation (TODO)" list containing the newly identified undocumented items.
- **Verification**: Review updated `docs/index.md` file content.

## Phase 3: Scripted Verification
### Step 5: Implement and Run Verification Script
- **Objective**: Create a python script that programmatically matches codebase routes/endpoints against docs + TODO list.
- **Subagent**: `teamwork_preview_worker` (verifier_worker)
- **Task**:
  - Write `verify_docs.py` (or similar) at `VentaPOS_NextGen/` root.
  - The script should:
    - Parse/list all actual frontend routes from the codebase.
    - Parse/list all actual backend endpoints from Django `urls.py` / codebase.
    - Parse all markdown files in `docs/` to find mentions of these routes/endpoints.
    - Check the TODO list in `docs/index.md` for remaining ones.
    - Output success if 100% of discovered routes and endpoints are either mentioned in docs or listed in the TODO section.
    - Fail with exit code 1 and show the missing items otherwise.
- **Verification**: Run the script and show output indicating success.

## Phase 4: Review, Challenger, and Audit
### Step 6: Review and Verification
- **Objective**: Run reviewer, challenger, and forensic auditor to verify correctness and integrity.
- **Subagents**:
  - `teamwork_preview_reviewer` to check the updated docs and verification script.
  - `teamwork_preview_challenger` to run the verification script and verify logic.
  - `teamwork_preview_auditor` to check for integrity violations.
- **Verification**: Passing reviews and clean audit.
