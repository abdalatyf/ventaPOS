# Workflow: VentaPOS NextGen

## 1. Git Automation Rules & Coding Standards

1. **Auto-Push Policy**: Upon completion of any major task or logical chunk of work, agents MUST automatically perform `git add .`, `git commit`, and `git push` without requiring explicit user prompts, to ensure the repository remains up-to-date and prevents data loss.
2. **Conventional Commits**: All commit messages must follow the Conventional Commits specification.
   - `feat:` for new features.
   - `fix:` for bug fixes.
   - `docs:` for documentation updates.
   - `refactor:` for code restructuring without changing behavior.
   - `test:` for adding or modifying tests.
   - `chore:` for maintenance or configuration changes.
3. **Branching Strategy**: For major milestones, create a dedicated feature branch. For rapid iterations in the active milestone, pushing to `main` is acceptable if tests pass.

---

## 2. Agent Team Architecture & Handoff Protocols
VentaPOS relies on a 12-agent specialized team. Adhere to these strict bounds to prevent hallucinations and errors:

- **ProductManager**: Writes `requirements.md`. No code.
- **DatabaseArchitect**: Modifies DB Schema. No one else touches the schema without architect approval.
- **UIDesigner**: Generates Declarative A2UI JSON. No logic.
- **Backend**: Implements Django REST endpoints (Server directory). Outputs OpenAPI 3.1 JSON.
- **Frontend**: Implements React components consuming OpenAPI endpoints and A2UI JSON.
- **Mobile**: Implements Flutter mobile endpoints.
- **QA / Security**: Penetration testing and strict hook validations.
- **DevOps**: Automation, CI/CD, and DB Backups.
- **MockData**: Creates DB seed scripts.
- **Documentation**: Writes Swagger docs and READMEs.
- **Orchestrator**: Master coordinator enforcing A2A handoffs.
