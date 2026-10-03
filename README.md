# PITF Wiki

A fan wiki for the PITF campaign, built with [MkDocs](https://www.mkdocs.org/) and the [Material](https://squidfunk.github.io/mkdocs-material/) theme. The pages are plain Markdown under `docs/`, so the folder also opens as a vault in Obsidian.

## View it locally

From this folder, in PowerShell:

```powershell
.venv\Scripts\mkdocs.exe serve
```

Then open http://127.0.0.1:8000. The site reloads when a page changes.

If `.venv` is missing, recreate it with any Python 3.9 or later:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install mkdocs-material
```

## Build a static copy

```powershell
.venv\Scripts\mkdocs.exe build
```

The result is in `site/` and can be hosted anywhere that serves static files.

## Publish

The site is hosted on GitHub Pages at https://andretinfante.github.io/pitf-wiki/, served from the `gh-pages` branch. After changing pages:

```powershell
git add -A
git commit -m "Describe the change"
git push
.venv\Scripts\mkdocs.exe gh-deploy
```

`git push` saves the Markdown source on `main`; `mkdocs gh-deploy` rebuilds the site and publishes it.

## Layout

- `docs/`: the wiki pages.
  - `episodes/`: one folder per case, with an arc page and one page per session.
  - `characters/`, `monsters/`, `organizations/`, `locations/`, `items/`, `lore/`: entity pages, plus `minor-*.md` list pages for smaller subjects.
  - `players/`, `meta/`: cast, tropes, quotes, running gags, game mechanics, lost episodes.
- `mkdocs.yml`: site configuration. The `nav:` section is generated; do not edit it by hand.
- `_notes/`: working material used to build the wiki. It is not part of the site, and most of it is kept out of the repository.
  - `tools/build_site.py`: regenerates the category index pages and the `nav:` section. Run it after adding, renaming or deleting pages.
  - `tools/lint.py`: checks for broken links and stray wording.

## Editing

Edit any page under `docs/` directly. After adding or removing pages:

```powershell
.venv\Scripts\python.exe _notes\tools\build_site.py
.venv\Scripts\python.exe _notes\tools\lint.py
```
