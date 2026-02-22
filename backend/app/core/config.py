import os
from pathlib import Path

class Settings:
    PROJECT_NAME: str = "Pronunciation Trainer"
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    # When running on Hugging Face Spaces (or similar), we only have write access to /tmp
    DATA_DIR: Path = Path("/tmp/data") if os.environ.get("ENV") == "prod" else BASE_DIR / "data"
    INPUT_DIR: Path = DATA_DIR / "inputs"
    OUTPUT_DIR: Path = DATA_DIR / "outputs"

settings = Settings()
