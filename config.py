# config.py
from dotenv import load_dotenv
import os

load_dotenv()

comands = os.getenv("plik")
PORT = int(os.getenv("PORT", 8080))

if not comands:
    raise ValueError("No comands, chceck file")
