import sys
from pathlib import Path

# Make the shared `common` package importable (services/ is its parent).
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
