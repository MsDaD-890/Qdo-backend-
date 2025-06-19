from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

# Определяем Base после импорта
Base = declarative_base()

SQL_DB_URL = 'your_url_database'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    engine = create_engine(SQL_DB_URL)
    logger.info(f"Connected to the database at {SQL_DB_URL} successfully.")

    Base.metadata.create_all(bind=engine)
    logger.info("Tables created successfully.")
    
except Exception as e:
    logger.error(f"Error connecting to the database: {e}")
    raise

session_local = sessionmaker(autoflush=False, autocommit=False, bind=engine)

def get_db():
    db = session_local()
    try:
        yield db
    finally:
        db.close()
        logger.info("Database session closed.")
