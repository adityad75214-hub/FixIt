# FixIt update notes

## Included changes

### Interface and branding
- Standardized the remaining legacy navy/blue UI accents to the selected Forest + Cream design tokens.
- Replaced hard-coded text, page-background, border, and brand colors with theme variables on the affected React pages. Functional status/priority/SLA colors remain distinct so urgent tickets are still recognizable.
- Updated the landing and registration surfaces to use the shared theme.

### Production safety
- Quick demo login controls, demo credential display, and demo-only ticket-form fallback data are now gated to Vite development builds. They are not included in production builds.
- Student public-registration UI is development-only by default. Production requires an explicit frontend/backend configuration and the backend independently blocks public registration in production.
- First-admin bootstrap now reads `backend/.env`, requires an explicit email and a 12+ character password, refuses to promote existing non-admin accounts, and leaves existing administrators unchanged.

### Data preservation
- Demo seeding changed from upsert/update behavior to insert-only behavior. Existing matching users, campus records, categories, SLA policies, knowledge articles, tickets, comments, and feedback are skipped rather than updated.
- No database schema migration, collection deletion, or database reset was added.
- The ZIP does not include `.env`, `.venv`, `node_modules`, `dist`, or a MongoDB data dump. Copy your existing `backend/.env` into the test copy; do not replace it with the example file.

### Performance
- Application pages are loaded on demand with React lazy imports; the public landing page remains eager so the first page can render immediately.
- Recharts/D3, React Router, and React vendor code are split into separate build chunks.

## Verification status
- All 55 Python files in the updated backend parsed successfully with Python's AST parser.
- The new seed helper has a regression test that checks an existing user is not overwritten.
- The owner previously reported 62 backend tests and 7 frontend tests passing, with a successful frontend build. Those results are the pre-update baseline.
- The updated copy's full pytest/Vitest/build suites could not be executed in this environment because `mongomock`, `motor`/`pymongo`, and frontend npm packages are not installed here and dependency installation is unavailable. Run the verification commands in `README.md` on the E: drive copy before replacing your current project.

## Deliberately unchanged
- Single-college architecture.
- Existing API routes, ticket lifecycle, role permissions, campus structure, and current data model.
- Existing live MongoDB data and the user's local environment files.
