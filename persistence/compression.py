import gzip
import os

LOG_FILE = "data/app.log"
COMPRESSED_FILE = "data/app_logs.gz"


def compress_logs():
    """Compress the app.log file using GZIP."""
    if not os.path.exists(LOG_FILE):
        print(f"  ⚠️  No log file found at {LOG_FILE}")
        return

    with open(LOG_FILE, "rb") as f_in:
        with gzip.open(COMPRESSED_FILE, "wb") as f_out:
            f_out.writelines(f_in)

    original_size = os.path.getsize(LOG_FILE)
    compressed_size = os.path.getsize(COMPRESSED_FILE)
    ratio = (1 - compressed_size / original_size) * 100 if original_size else 0

    print(f"  ✅ Logs compressed → {COMPRESSED_FILE}")
    print(f"     Original : {original_size:,} bytes")
    print(f"     Compressed: {compressed_size:,} bytes  ({ratio:.1f}% saved)")


def decompress_logs() -> str:
    """Read and return the content of compressed logs."""
    if not os.path.exists(COMPRESSED_FILE):
        return ""
    with gzip.open(COMPRESSED_FILE, "rb") as f:
        return f.read().decode("utf-8")
