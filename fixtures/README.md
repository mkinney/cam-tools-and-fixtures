# Fixtures

CamCraft keeps workholding (vises, blocks, plates, chuck jaws) in a fixture library. The file format is `camcraft-fixtures/1`: each entry is a named mesh plus the datum it is placed by. You can import any STEP as a fixture and save it there.

- **`vendor-fetch/`** downloads vendors' free CAD models straight from the vendor's own site, using the URLs listed in `<vendor>/SOURCES.md`. Those files are the vendors' work, so they are **not** stored here. Run `python3 -I vendor-fetch/fetch.py fireball`, then import the STEP files.
  - Checked with CamCraft: all 25 Fireball Tool models (tower, extension, pin and tooth blocks, and tables) import as fixtures at their stated sizes. They import centred on their own origin, not sitting at z=0.
- **Our own models** (planned): simplified vises, blocks and plates, built in [SolidCraft](https://solidcraft.io/) from published dimensions. We'll publish them here as STEP plus a `camcraft-fixtures/1` library.
