# Example workspace template

Copy this folder to create a local workspace without using the UI:

```bash
cp -r clients/_example clients/my_client_id
```

On Windows (PowerShell):

```powershell
Copy-Item -Recurse clients\_example clients\my_client_id
```

Then open **my_client_id** in ContentFlow at [http://localhost:3000](http://localhost:3000).

Folders:

- `context/` — workspace-level Markdown used by pipeline steps
- `runs/` — one subfolder per article run (created automatically when you start an article)

Do not commit real workspaces; they live under `clients/` and are gitignored.
