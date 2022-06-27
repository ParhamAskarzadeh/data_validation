import os
from dotenv import load_dotenv

load_dotenv()

MONGO_HOST = os.getenv("MONGO_HOST", 'localhost')
MONGO_PORT = os.getenv('MONGO_PORT', default=27017)
MONGO_DB = os.getenv('MONGO_DB', default='mohaymen')
