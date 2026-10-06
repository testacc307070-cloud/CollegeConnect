"""
CollegeConnect site server entry point.
Consolidated to delegate directly to backend.app.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app import app

if __name__ == "__main__":
    print()
    print("=" * 70)
    print("COLLEGECONNECT SERVER")
    print("=" * 70)
    print("Registered routes:")
    for rule in sorted(app.url_map.iter_rules(), key=lambda r: str(r)):
        methods = sorted(rule.methods - {"HEAD", "OPTIONS"})
        print(f"  {methods} {rule}")
    print()
    print("Open: http://127.0.0.1:5000")
    print("=" * 70)
    print()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
    )