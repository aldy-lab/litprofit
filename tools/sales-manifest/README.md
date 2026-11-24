# Sales folder → calculator

Reads a year's "Pardavimai" folder (a folder per enquiry) into `manifest.json`,
which the calculator's **Documents → Import a sales folder** uploads.

```sh
python3 -m venv .venv && .venv/bin/pip install extract-msg openpyxl pymupdf xlrd
.venv/bin/python 1_inventory.py            # folder → enquiry number, folders.json
.venv/bin/python 2_extract.py OUT/manifest.json
.venv/bin/python 3_finalize.py OUT/manifest.json
```

The paths to the folder and to the SharePoint CSV export are at the top of
`1_inventory.py` and `2_extract.py`.

**The manifest and `folders.json` contain client data. Never commit them** —
this repository is public. Write them outside it (the Desktop).
