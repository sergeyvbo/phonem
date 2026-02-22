import os
from pathlib import Path

class Settings:
    PROJECT_NAME: str = "Pronunciation Trainer"
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    INPUT_DIR: Path = DATA_DIR / "inputs"
    OUTPUT_DIR: Path = DATA_DIR / "outputs"

settings = Settings()
