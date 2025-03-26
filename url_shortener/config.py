import os
from dotenv import load_dotenv


load_dotenv()


AUTH_TOKEN = os.getenv('AUTH_TOKEN')
LIFETIME = os.getenv('LIFETIME')

DB_USER = os.getenv('DB_USER')
DATABASE_PASS = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')

DATABASE_CREDENTIALS = f'{DB_USER}:{DATABASE_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
ASYNC_DATABASE_URL = 'postgresql+asyncpg://' + DATABASE_CREDENTIALS
SYNC_DATABASE_URL = 'postgresql+psycopg2://' + DATABASE_CREDENTIALS

REDIS_HOST_CACHE = os.getenv('REDIS_HOST_CACHE')
REDIS_PORT_CACHE = os.getenv('REDIS_PORT_CACHE')
REDIS_HOST_CELERY = os.getenv('REDIS_HOST_CELERY')
REDIS_PORT_CELERY = os.getenv('REDIS_PORT_CELERY')
