# The Neverlands Wiki


Public website: https://kimookpong.github.io/the-neverlands/

The reader wiki contains Thai-language world information without hidden identities,
future plot revelations, or the ending. Author-only World Bible files
remain local and are excluded from Git and the website export.

- Edit published articles in `content/wiki.json`.
- `visibility` must be `public`; use `established`, `working`, `developing`, or
  `in-world` for the information status.
- Preserve provisional names and distinguish in-world accounts from established
  setting information. Do not add secret canon to public content or commit history.
- Add a stable, unique `slug`, a category, sections, and valid related-article slugs.
- The site reads **only** `content/wiki.json` and `site/assets/`.

Build and verify with Python 3.9+; no package installation is needed:

```sh
python3 scripts/build.py
python3 scripts/check.py
python3 scripts/serve.py
```

Preview at http://127.0.0.1:4173/the-neverlands/.

Push to `main` to build, verify, and deploy through `.github/workflows/pages.yml`.
GitHub Pages uses **GitHub Actions** as its publishing source. Only `dist/` is
uploaded to Pages. Internal URLs use `/the-neverlands/` so category and article
links work at the project URL. A root-hosted export can be built with
`python3 scripts/build.py --base-path /`.

Publication checks validate every internal link, page anchors, required page
metadata, the search index, and the exported file boundary. In the local author
workspace, an ignored `.publication-policy.json` can additionally supply private
editorial exclusion patterns. Those rules are never committed. Automated checks
are regression guards; new articles still need editorial spoiler review.
