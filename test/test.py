import os

from nbdapi import NationalBank
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

nb = NationalBank(os.getenv('NBDB_USERNAME'), os.getenv('NBDB_PASSWORD'))
