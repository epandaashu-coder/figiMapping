# OpenFIGI ISIN to BBG Mapping - Implementation Guide

## 🔧 Step-by-Step Implementation with Code

---

## STEP 1: Environment Configuration (.env & settings.py)

### A. Create `.env` File (Project Root)

```env
# OpenFIGI API Configuration
OPENFIGI_API_KEY=your_api_key_here
OPENFIGI_BASE_URL=https://api.openfigi.com/v3

# Database Configuration
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=your_database_name
DATABASE_USER=your_username
DATABASE_PASSWORD=your_password

# Application Configuration
LOG_LEVEL=INFO
DEBUG=False
```

### B. Create `.env.example` (Template for Team)

```env
# Copy this file to .env and fill in your actual values
OPENFIGI_API_KEY=
OPENFIGI_BASE_URL=https://api.openfigi.com/v3
DATABASE_HOST=
DATABASE_PORT=5432
DATABASE_NAME=
DATABASE_USER=
DATABASE_PASSWORD=
LOG_LEVEL=INFO
DEBUG=False
```

### C. Add to `.gitignore`

```
# Environment variables
.env
.env.local
.env.*.local

# Virtual environment
venv/
env/

# IDE
.vscode/
.idea/
*.pyc

# Logs
logs/
*.log

# Database
*.db
*.sqlite
```

### D. Create `config/settings.py`

```python
"""
Configuration management using python-dotenv
Loads environment variables from .env file
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env file from project root
ENV_PATH = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

class Config:
    """Base configuration class"""
    
    # OpenFIGI API
    OPENFIGI_API_KEY = os.getenv("OPENFIGI_API_KEY")
    OPENFIGI_BASE_URL = os.getenv("OPENFIGI_BASE_URL", "https://api.openfigi.com/v3")
    
    # Database
    DATABASE_HOST = os.getenv("DATABASE_HOST", "localhost")
    DATABASE_PORT = int(os.getenv("DATABASE_PORT", "5432"))
    DATABASE_NAME = os.getenv("DATABASE_NAME")
    DATABASE_USER = os.getenv("DATABASE_USER")
    DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
    
    # Application
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    @classmethod
    def validate_config(cls):
        """Validate that all required environment variables are set"""
        required_vars = [
            "OPENFIGI_API_KEY",
            "DATABASE_HOST",
            "DATABASE_NAME",
            "DATABASE_USER",
            "DATABASE_PASSWORD"
        ]
        
        missing_vars = [var for var in required_vars if not getattr(cls, var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True

# Validate on module load
Config.validate_config()
```

### E. Create `config/__init__.py`

```python
from config.settings import Config

__all__ = ["Config"]
```

---

## STEP 2 & 3: Database Connection & Mapping Setup

### Create `src/database/db_connection.py`

```python
"""
Database connection management
"""

import psycopg2
from psycopg2.pool import SimpleConnectionPool
from config.settings import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)

class DatabaseConnection:
    """Manages database connections"""
    
    _pool = None
    
    @classmethod
    def initialize_pool(cls, min_conn=1, max_conn=5):
        """Initialize connection pool"""
        try:
            cls._pool = SimpleConnectionPool(
                min_conn,
                max_conn,
                host=Config.DATABASE_HOST,
                port=Config.DATABASE_PORT,
                database=Config.DATABASE_NAME,
                user=Config.DATABASE_USER,
                password=Config.DATABASE_PASSWORD
            )
            logger.info("Database connection pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {str(e)}")
            raise
    
    @classmethod
    def get_connection(cls):
        """Get connection from pool"""
        if cls._pool is None:
            cls.initialize_pool()
        return cls._pool.getconn()
    
    @classmethod
    def return_connection(cls, conn):
        """Return connection to pool"""
        if cls._pool:
            cls._pool.putconn(conn)
    
    @classmethod
    def close_all_connections(cls):
        """Close all pooled connections"""
        if cls._pool:
            cls._pool.closeall()
            logger.info("All database connections closed")
```

### Create `src/database/queries.py`

```python
"""
SQL queries for data retrieval
"""

# STEP 1: Retrieve IDs with ISIN where BBG Symbol & BBGID are not updated
QUERY_GET_ISIN_WITHOUT_BBG = """
    SELECT 
        eq.InvestmentId,
        eq.ISIN,
        eq.ExchangeId,
        eq.CurrencyId,
        exc.ExchangeCode,
        cur.Currency
    FROM 
        EquityCoverage eq
        INNER JOIN Exchanges exc ON eq.ExchangeId = exc.ExchangeId
        INNER JOIN Currencies cur ON eq.CurrencyId = cur.CurrencyId
    WHERE 
        eq.BBGSymbol IS NULL 
        OR eq.BBGID IS NULL
    LIMIT %s;
"""

# Query to check existing mappings
QUERY_CHECK_EXISTING_MAPPING = """
    SELECT COUNT(*) as count
    FROM EquityCoverage
    WHERE ISIN = %s AND ExchangeId = %s AND CurrencyId = %s;
"""

# Query to retrieve exchange and currency mappings
QUERY_GET_EXCHANGE_MAPPING = """
    SELECT ExchangeId, ExchangeCode FROM Exchanges;
"""

QUERY_GET_CURRENCY_MAPPING = """
    SELECT CurrencyId, Currency FROM Currencies;
"""
```

### Create `config/constants.py`

```python
"""
Application constants and enums
"""

class ExchangeMapping:
    """Exchange Code to GID mappings (example)"""
    MAPPINGS = {
        "US": 1,  # Example: NYSE/NASDAQ
        "IN": 2,  # India
        "UK": 3,  # UK
        # Add more as needed
    }

class CurrencyMapping:
    """Currency to GID mappings (example)"""
    MAPPINGS = {
        "USD": 1,
        "INR": 2,
        "GBP": 3,
        # Add more as needed
    }

class APIConstants:
    """OpenFIGI API constants"""
    MAPPING_ENDPOINT = "/mapping"
    FILTER_ENDPOINT = "/filter"
    MAX_BATCH_SIZE = 100  # OpenFIGI batch limit
    REQUEST_TIMEOUT = 30  # seconds
    RETRY_COUNT = 3
    RETRY_DELAY = 2  # seconds
```

---

## STEP 3 & 4: OpenFIGI API Integration

### Create `src/api/openfigi_client.py`

```python
"""
OpenFIGI API Client wrapper
Handles API calls with rate limiting and retry logic
"""

import requests
import time
from typing import List, Dict, Any
from config.settings import Config
from config.constants import APIConstants
from src.utils.logger import get_logger

logger = get_logger(__name__)

class OpenFIGIClient:
    """Wrapper for OpenFIGI API v3"""
    
    def __init__(self, api_key: str = None, base_url: str = None):
        """
        Initialize OpenFIGI client
        
        Args:
            api_key: OpenFIGI API key (uses Config if not provided)
            base_url: API base URL (uses Config if not provided)
        """
        self.api_key = api_key or Config.OPENFIGI_API_KEY
        self.base_url = base_url or Config.OPENFIGI_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "X-OPENFIGI-APIKEY": self.api_key
        })
    
    def map_isin_to_figi(self, isin: str, exch_code: str, currency: str) -> Dict[str, Any]:
        """
        Map ISIN to FIGI using OpenFIGI API
        
        Args:
            isin: ISIN identifier
            exch_code: Exchange code (e.g., 'US', 'IN')
            currency: Currency code (e.g., 'USD', 'INR')
        
        Returns:
            Dictionary with mapping results or error
        """
        mapping_job = {
            "idType": "ISIN",
            "idValue": isin,
            "exchCode": exch_code,
            "currency": currency,
            "marketSecDes": "Equity"
        }
        
        return self.batch_map([mapping_job])
    
    def batch_map(self, mapping_jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Batch map multiple jobs to FIGIs
        Respects OpenFIGI rate limits
        
        Args:
            mapping_jobs: List of mapping job dictionaries
        
        Returns:
            API response with mapping results
        """
        url = f"{self.base_url}{APIConstants.MAPPING_ENDPOINT}"
        
        # Respect OpenFIGI rate limiting (1 request per 250ms without API key)
        wait_time = 0.3 if not self.api_key else 0.1
        
        retry_count = 0
        while retry_count < APIConstants.RETRY_COUNT:
            try:
                time.sleep(wait_time)  # Rate limiting
                
                response = self.session.post(
                    url,
                    json=mapping_jobs,
                    timeout=APIConstants.REQUEST_TIMEOUT
                )
                
                if response.status_code == 200:
                    logger.debug(f"Successfully mapped {len(mapping_jobs)} jobs")
                    return {"status": "success", "data": response.json()}
                
                elif response.status_code == 429:  # Too many requests
                    logger.warning("Rate limited by OpenFIGI API, waiting...")
                    time.sleep(APIConstants.RETRY_DELAY)
                    retry_count += 1
                
                else:
                    logger.error(f"API Error: {response.status_code} - {response.text}")
                    return {"status": "error", "message": response.text}
            
            except requests.Timeout:
                logger.warning(f"Request timeout (attempt {retry_count + 1})")
                retry_count += 1
                time.sleep(APIConstants.RETRY_DELAY)
            
            except Exception as e:
                logger.error(f"API request failed: {str(e)}")
                return {"status": "error", "message": str(e)}
        
        logger.error(f"Failed after {APIConstants.RETRY_COUNT} retries")
        return {"status": "error", "message": "Max retries exceeded"}
```

---

## STEP 5 & 6: Data Transformation & Batch Generation

### Create `src/data_processor/transformer.py`

```python
"""
Transform raw API response to desired format
"""

from typing import Dict, List, Any
from src.utils.logger import get_logger

logger = get_logger(__name__)

class DataTransformer:
    """Transform API responses to desired output format"""
    
    @staticmethod
    def transform_mapping_result(
        isin: str,
        investment_id: int,
        exchange_id: int,
        api_response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Transform OpenFIGI API response to desired format
        
        Args:
            isin: ISIN identifier
            investment_id: Internal investment ID
            exchange_id: Internal exchange ID
            api_response: Response from OpenFIGI API
        
        Returns:
            Transformed data with ISIN, BBG Symbol, and FIGI
        """
        try:
            if not api_response or not api_response.get("data"):
                logger.warning(f"No data in API response for ISIN: {isin}")
                return None
            
            mapping_data = api_response["data"][0]  # First result
            
            transformed = {
                "InvestmentId": investment_id,
                "ExchangeId": exchange_id,
                "ISIN": isin,
                "BBGSymbol": mapping_data.get("ticker"),
                "FIGI": mapping_data.get("figi"),
                "CompositeFIGI": mapping_data.get("compositeFIGI"),
                "Name": mapping_data.get("name"),
                "SecurityType": mapping_data.get("securityType"),
            }
            
            logger.debug(f"Transformed ISIN {isin}: BBGSymbol={transformed['BBGSymbol']}, FIGI={transformed['FIGI']}")
            return transformed
        
        except Exception as e:
            logger.error(f"Error transforming data for ISIN {isin}: {str(e)}")
            return None
    
    @staticmethod
    def prepare_batch_updates(transformed_data: List[Dict[str, Any]]) -> tuple:
        """
        Prepare batch update files for BBG Symbol and BBGID
        
        Args:
            transformed_data: List of transformed mapping results
        
        Returns:
            Tuple of (bbg_symbol_updates, bbgid_updates)
        """
        bbg_symbol_updates = []
        bbgid_updates = []
        
        for record in transformed_data:
            if record is None:
                continue
            
            # BBG Symbol batch
            if record.get("BBGSymbol"):
                bbg_symbol_updates.append({
                    "InvestmentId": record["InvestmentId"],
                    "ExchangeId": record["ExchangeId"],
                    "Identifier": record["BBGSymbol"]
                })
            
            # BBGID (FIGI) batch
            if record.get("FIGI"):
                bbgid_updates.append({
                    "InvestmentId": record["InvestmentId"],
                    "ExchangeId": record["ExchangeId"],
                    "Identifier": record["FIGI"]
                })
        
        logger.info(f"Prepared {len(bbg_symbol_updates)} BBG Symbol updates and {len(bbgid_updates)} BBGID updates")
        return bbg_symbol_updates, bbgid_updates
```

### Create `src/batch_generator/batch_creator.py`

```python
"""
Generate batch update CSV files for database import
"""

import csv
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from src.utils.logger import get_logger

logger = get_logger(__name__)

class BatchCreator:
    """Creates batch update files in CSV format"""
    
    OUTPUT_DIR = Path(__file__).parent.parent.parent / "output"
    
    @classmethod
    def create_output_directory(cls):
        """Ensure output directory exists"""
        cls.OUTPUT_DIR.mkdir(exist_ok=True)
    
    @classmethod
    def generate_batch_files(
        cls,
        bbg_symbol_updates: List[Dict[str, Any]],
        bbgid_updates: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """
        Generate batch update CSV files
        
        Args:
            bbg_symbol_updates: List of BBG Symbol updates
            bbgid_updates: List of BBGID updates
        
        Returns:
            Dictionary with file paths
        """
        cls.create_output_directory()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # BBG Symbol batch file
        bbg_file = cls.OUTPUT_DIR / f"batch_bbg_symbol_{timestamp}.csv"
        cls._write_csv_file(bbg_file, bbg_symbol_updates)
        
        # BBGID batch file
        bbgid_file = cls.OUTPUT_DIR / f"batch_bbgid_{timestamp}.csv"
        cls._write_csv_file(bbgid_file, bbgid_updates)
        
        result = {
            "bbg_symbol_file": str(bbg_file),
            "bbgid_file": str(bbgid_file)
        }
        
        logger.info(f"Generated batch files at {cls.OUTPUT_DIR}")
        logger.info(f"  BBG Symbol: {bbg_file.name}")
        logger.info(f"  BBGID: {bbgid_file.name}")
        
        return result
    
    @staticmethod
    def _write_csv_file(filepath: Path, data: List[Dict[str, Any]]):
        """Write data to CSV file"""
        if not data:
            logger.warning(f"No data to write to {filepath}")
            return
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = data[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                writer.writerows(data)
            
            logger.info(f"Written {len(data)} records to {filepath}")
        
        except Exception as e:
            logger.error(f"Error writing CSV file {filepath}: {str(e)}")
            raise
```

---

## Summary of Implementation

| Step | File | Function |
|------|------|----------|
| 1 | `.env` | Store API credentials securely |
| 2 | `config/settings.py` + `db_connection.py` | Load config & establish DB connection |
| 3 | `db_connection.py` + `queries.py` | Retrieve ISIN data from database |
| 4 | `src/api/openfigi_client.py` | Call OpenFIGI API with ISIN+ExchangeCode+Currency |
| 5 | `data_processor/transformer.py` | Transform API response to desired columns |
| 6 | `batch_generator/batch_creator.py` | Create batch CSV files for database update |
