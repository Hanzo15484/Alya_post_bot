import os
from dotenv import load_dotenv

load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "8136083827:AAFu9QFO_v4vSeqOmfhU_ScSk3NJXlhMNfc")
OWNER_ID = 5373577888
OWNER_USERNAME = "Quarel7"
OWNER_URL = "t.me/Quarel7"
BOT_USERNAME = "@Alya_postbot"
BOT_NAME = "Alya"
PYTHON_VERSION = "3.8+"
DATABASE_TYPE = "SQL"

# Bot Start Time
import time
BOT_START_TIME = time.time()