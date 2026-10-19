"""
Diagnostic: why uvicorn can't import license_server_pg

Run:
  python diag_import_license_server_pg.py

It will:
- print current working directory
- list files
- try to import license_server_pg and show the real error if any
"""

import os
import sys
import traceback
from pathlib import Path

print("Python:", sys.executable)
print("CWD:", os.getcwd())
print("Files here:")
for p in sorted(Path(".").glob("*")):
    if p.is_file():
        print(" -", p.name)

print("\nTrying import license_server_pg ...")
try:
    import license_server_pg  # noqa
    print("✅ Imported license_server_pg OK")
except Exception as e:
    print("❌ Import failed:")
    traceback.print_exc()
    print("\nMost common fixes:")
    print("1) Ensure license_server_pg.py is in this folder (same folder you run from).")
    print("2) If Windows hides extensions, file might be license_server_pg.py.txt — rename to .py")
    print("3) Ensure dependencies installed in this Python: fastapi uvicorn cryptography psycopg2-binary")
