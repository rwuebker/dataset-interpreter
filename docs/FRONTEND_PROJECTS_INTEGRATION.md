# Frontend Integration Note (`rwuebker.github.io`)

Quick scan notes:
- existing project routes are under `src/app/projects/*`
- current known project pages redirect to `/`
- this gives us a clear insertion point for a future `/projects/dataset-interpreter` page

Planned integration (later, after backend maturity):
- add a dedicated project page at `src/app/projects/dataset-interpreter/page.tsx`
- include architecture summary, API demo flow, and link to live backend endpoint
- keep frontend minimal and focused on demo storytelling
