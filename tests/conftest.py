import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
	sys.path.insert(0, str(ROOT))

os.environ.setdefault("POSTGRES_USER", "neuroflow")
os.environ.setdefault("POSTGRES_PASSWORD", "strongpassword")
os.environ.setdefault("POSTGRES_DB", "neuroflow")
os.environ.setdefault("REDIS_PASSWORD", "redispassword")
