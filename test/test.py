import os
from dotenv import load_dotenv

from nbdapi import NationalBank

# Load environment variables from .env file
load_dotenv()

print(os.getenv('NBDB_USERNAME'))

nb = NationalBank(os.getenv('NBDB_USERNAME'), os.getenv('NBDB_PASSWORD'))
