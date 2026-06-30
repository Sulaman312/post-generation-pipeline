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
# MongoDB persistence

Set `MONGODB_URI` to make MongoDB the durable source of truth. All files under `clients/`, including
context, run manifests, generated images, formatted images, logos, and template assets, are stored in
GridFS. The application hydrates a disposable local cache at startup because the rendering pipeline
uses filesystem and Pillow APIs.

Seed the current repository data before the first Mongo-backed deployment:

```bash
MONGODB_URI='mongodb+srv://...' MONGODB_DB='post_generation_pipeline' \
  backend/venv/bin/python scripts/seed_mongodb.py
```

The seed command mirrors `clients/` exactly and removes database files that no longer exist locally.
Use `--keep-extra` to retain additional database files. Keep the deployed service at one instance;
the Docker configuration already uses one Gunicorn worker.

The Docker image does not include `clients/`. Once the initial seed has completed and been verified,
the local folder may be moved outside the repository. For future reseeds, pass its new location:

```bash
backend/venv/bin/python scripts/seed_mongodb.py --source /path/to/clients
```

## Long-running pipeline steps

Pipeline steps run as background jobs. The step endpoint returns `202 Accepted` immediately and the
UI polls the run status until completion, avoiding Koyeb's public HTTP request timeout. Final outputs,
errors, and timing data are written to the run manifest and synchronized to MongoDB by the worker.
