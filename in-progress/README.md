# In-progress skills

Public drafts live here, one directory per skill, until they meet the rules in `scripts/catalog.py` and the organization's [skill naming and scope rules](https://github.com/z-shell/.github/blob/main/knowledge/domains/agents/skill-naming.md). Nothing in this directory is listed in `catalog.json` or any generated manifest, so no plugin install includes it.

To publish a draft, move its directory to `plugins/<plugin>/skills/<name>/`, add the name to that plugin's `skills` list in `catalog.json`, bump the catalog version and run `python3 scripts/catalog.py`.
