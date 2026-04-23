# Website — Cloudflare Pages

This folder contains a static landing page for the Kira AI assistant. Quick deploy notes for Cloudflare Pages:

- Repository: select this repo.
- Branch: choose the branch you deploy from (e.g., `main` or a `pages` branch).
- Build settings: there is no build step for the static site. Set "Build command" empty and set "Build output directory" to `website` (or leave empty if Cloudflare allows it).
- If you add a static site generator later, update the build command accordingly.

Files:
- `index.html`, `style.css`, `script.js` — static site source.
