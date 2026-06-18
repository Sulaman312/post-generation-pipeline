# Post Generation Pipeline (standalone)

Self-contained project: **own backend**, **own UI**, **own workspace data** (`clients/`).

You can move this entire folder anywhere on disk and run it without the parent monorepo.

## Copy workspaces from the monorepo

Your real workspaces (`67`, `arsuno`, `ludovic`, etc.) live in the **parent** repo under `clients/`. They are **not** copied automatically when you sync code.

From the **monorepo root**, copy all workspaces into this project:

```powershell
cd path\to\articlegen_projExtended- Copy
.\scripts\migrate-clients-to-project.ps1 -Project post-generation-pipeline -IncludeRuns
```

Copy specific workspaces only:

```powershell
.\scripts\migrate-clients-to-project.ps1 -Project post-generation-pipeline -ClientIds arsuno,ludovic -IncludeRuns
```

Or copy manually in File Explorer:

```
FROM:  articlegen_projExtended- Copy\clients\arsuno\
TO:    post-generation-pipeline\clients\arsuno\
```

Copy the whole folder (including `context/`, `runs/`, logo files). Omit `-IncludeRuns` if you only want context files, not past runs.

Restart `.\start.ps1` after copying so the API picks up the new folders.

## Pipeline screen

After opening a workspace you should see the **Pipelines** card screen (social media card only in this app). Click **Open** to reach the step matrix and new-post form.

Requires `atlas-ui\.env`:

```
REACT_APP_PROJECT_MODE=social
REACT_APP_API_URL=http://localhost:8000
```

If the UI shows both pipelines or skips the card screen, stop the app, confirm that file exists, then run `npm start` again from `atlas-ui/`.

## First-time setup

1. Copy API keys:
   ```powershell
   copy .env.example .env
   # Edit .env — add OPENAI_API_KEY, etc.
   ```

2. Python dependencies (from this folder):
   ```powershell
   pip install -r requirements.txt
   ```

3. If `backend/` or `atlas-ui/` are missing, sync from the monorepo once:
   ```powershell
   cd path\to\articlegen_projExtended- Copy
   .\scripts\sync-standalone-projects.ps1 -Target social
   ```

## Run

```powershell
.\start.ps1
```

- UI: http://localhost:3000  
- API: http://localhost:8000  
- Workspaces: `./clients/`

## After monorepo code changes

From the **parent** repo root, refresh this copy:

```powershell
.\scripts\sync-standalone-projects.ps1 -Target social
```

Then `cd post-generation-pipeline\atlas-ui` and `npm install` if dependencies changed.

## Layout

```
post-generation-pipeline/
  main.py
  backend/
  atlas-ui/
  clients/
  .env
  start.ps1
```
