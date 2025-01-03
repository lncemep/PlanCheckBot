# @my_firstsecond_testing_bot
from dotenv import load_dotenv
import os

load_dotenv()

comands = os.getenv("plik")

if not comands:
    raise ValueError("No comands, chceck file")
