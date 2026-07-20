# Setup

1. Create the magic repo (must be named exactly your username):

   ```
   gh repo create Siddhantsatote --public --clone
   ```

   Or just create it via github.com/new — name: `Siddhantsatote`, public, no README (you already have one).

2. Copy everything in this folder into that repo, then:

   ```
   cd Siddhantsatote
   git add .
   git commit -m "profile: animated ASCII portrait + neofetch card + live contrib heatmap"
   git push
   ```

3. Go to the repo's **Actions** tab → "Update profile art" → **Run workflow** once by hand to confirm it commits successfully. After that it runs daily on its own (06:17 UTC).

## Regenerating things

- **New photo** → drop it in as `source-photo.png`, then:
  ```
  pip install -r scripts/requirements.txt
  python scripts/prep_photo.py source-photo.png
  python scripts/make_ascii_svg.py source-prepped.png siddh-ascii.svg
  ```
- **Info card text** → edit the `ROWS` list in `scripts/make_info_card.py`, then `python scripts/make_info_card.py`.
- **Heatmap** → runs automatically via the Action; to force it locally: `python scripts/fetch_contributions.py Siddhantsatote && python scripts/render_heatmap_svg.py`.

## Notes

- All three SVGs already have real content baked in: your actual photo (ASCII-ified), your actual info, and your real contribution data (281 contributions, longest streak 6 days, as of today).
- The heatmap scrapes `github.com/users/Siddhantsatote/contributions` — public HTML, no token needed.
- If GitHub tweaks that page's markup again, `fetch_contributions.py` pulls counts from the `<tool-tip>` text (`"N contributions on <date>."`) — check that regex first if the Action starts failing.
