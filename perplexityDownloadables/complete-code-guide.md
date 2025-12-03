# Complete Main Script & Utilities

## Create `src/utils/logger.py`

```python
"""
Logging setup and configuration
"""

import logging
import logging.handlers
from pathlib import Path
from config.settings import Config

# Create logs directory
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only configure if not already configured
    if not logger.handlers:
        logger.setLevel(getattr(logging, Config.LOG_LEVEL))
        
        # File handler for all logs
        fh = logging.handlers.RotatingFileHandler(
            LOG_DIR / "app.log",
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        fh.setLevel(logging.DEBUG)
        
        # File handler for errors
        eh = logging.handlers.RotatingFileHandler(
            LOG_DIR / "errors.log",
            maxBytes=10485760,
            backupCount=5
        )
        eh.setLevel(logging.ERROR)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(getattr(logging, Config.LOG_LEVEL))
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        fh.setFormatter(formatter)
        eh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(eh)
        logger.addHandler(ch)
    
    return logger
```

---

## Create `src/utils/helpers.py`

```python
"""
Helper utility functions
"""

from typing import List, Dict, Any
from src.utils.logger import get_logger

logger = get_logger(__name__)

def validate_isin(isin: str) -> bool:
    """
    Validate ISIN format (basic check)
    ISIN format: 2 letter country code + 9 digit identifier + 1 check digit
    
    Args:
        isin: ISIN code to validate
    
    Returns:
        True if valid, False otherwise
    """
    if not isin or len(isin) != 12:
        return False
    
    # First 2 characters should be letters
    if not isin[:2].isalpha():
        return False
    
    # Remaining should be alphanumeric
    if not isin[2:].isalnum():
        return False
    
    return True

def validate_exchange_code(code: str) -> bool:
    """Validate exchange code format"""
    return code and len(code) <= 5 and code.isalpha()

def validate_currency(currency: str) -> bool:
    """Validate currency code format (ISO 4217)"""
    return currency and len(currency) == 3 and currency.isalpha()

def deduplicate_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove duplicate records based on ISIN
    
    Args:
        records: List of records with ISIN
    
    Returns:
        Deduplicated list
    """
    seen = set()
    unique_records = []
    
    for record in records:
        isin = record.get("ISIN")
        if isin not in seen:
            seen.add(isin)
            unique_records.append(record)
    
    logger.info(f"Deduplicated {len(records)} records to {len(unique_records)}")
    return unique_records

def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split list into chunks of specified size
    
    Args:
        items: List to chunk
        chunk_size: Size of each chunk
    
    Returns:
        List of chunked lists
    """
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]
```

---

## Create `src/data_processor/mapper.py`

```python
"""
Main mapping orchestration logic
Maps ISIN to BBG Symbol and BBGID using OpenFIGI API
"""

from typing import List, Dict, Any
from src.api.openfigi_client import OpenFIGIClient
from src.data_processor.transformer import DataTransformer
from src.utils.logger import get_logger
from src.utils.helpers import deduplicate_records, chunk_list
from config.constants import APIConstants

logger = get_logger(__name__)

class ISINToBBGMapper:
    """Maps ISIN codes to BBG Symbol and FIGI using OpenFIGI API"""
    
    def __init__(self):
        """Initialize mapper with OpenFIGI client"""
        self.client = OpenFIGIClient()
        self.transformer = DataTransformer()
    
    def map_batch(
        self,
        isin_records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Map a batch of ISIN records to FIGI data
        
        Args:
            isin_records: List of records with ISIN, ExchangeCode, Currency, etc.
        
        Returns:
            List of transformed mapping results
        """
        
        # Deduplicate input records
        unique_records = deduplicate_records(isin_records)
        
        logger.info(f"Starting batch mapping for {len(unique_records)} records")
        
        transformed_results = []
        
        # Process in chunks to respect API limits
        for chunk in chunk_list(unique_records, APIConstants.MAX_BATCH_SIZE):
            logger.debug(f"Processing chunk of {len(chunk)} records")
            
            for record in chunk:
                try:
                    isin = record.get("ISIN")
                    exch_code = record.get("ExchangeCode")
                    currency = record.get("Currency")
                    investment_id = record.get("InvestmentId")
                    exchange_id = record.get("ExchangeId")
                    
                    # Validate inputs
                    if not all([isin, exch_code, currency]):
                        logger.warning(f"Missing required fields for record: {record}")
                        continue
                    
                    logger.debug(f"Mapping ISIN: {isin}, ExchangeCode: {exch_code}, Currency: {currency}")
                    
                    # Call OpenFIGI API
                    api_response = self.client.map_isin_to_figi(isin, exch_code, currency)
                    
                    # Transform response
                    transformed = self.transformer.transform_mapping_result(
                        isin=isin,
                        investment_id=investment_id,
                        exchange_id=exchange_id,
                        api_response=api_response
                    )
                    
                    if transformed:
                        transformed_results.append(transformed)
                    
                except Exception as e:
                    logger.error(f"Error mapping ISIN {record.get('ISIN')}: {str(e)}")
                    continue
        
        logger.info(f"Completed batch mapping: {len(transformed_results)} successful mappings")
        return transformed_results
```

---

## Create `src/data_processor/validator.py`

```python
"""
Data validation before and after API calls
"""

from typing import List, Dict, Any
from src.utils.logger import get_logger
from src.utils.helpers import validate_isin, validate_exchange_code, validate_currency

logger = get_logger(__name__)

class DataValidator:
    """Validates data at various stages of processing"""
    
    @staticmethod
    def validate_isin_records(records: List[Dict[str, Any]]) -> tuple:
        """
        Validate ISIN records from database
        
        Args:
            records: List of records from database
        
        Returns:
            Tuple of (valid_records, invalid_records)
        """
        valid = []
        invalid = []
        
        for record in records:
            errors = []
            
            isin = record.get("ISIN")
            exch_code = record.get("ExchangeCode")
            currency = record.get("Currency")
            
            if not validate_isin(isin):
                errors.append(f"Invalid ISIN: {isin}")
            
            if not validate_exchange_code(exch_code):
                errors.append(f"Invalid ExchangeCode: {exch_code}")
            
            if not validate_currency(currency):
                errors.append(f"Invalid Currency: {currency}")
            
            if errors:
                invalid.append({"record": record, "errors": errors})
                logger.warning(f"Invalid record: {errors}")
            else:
                valid.append(record)
        
        logger.info(f"Validation complete: {len(valid)} valid, {len(invalid)} invalid records")
        return valid, invalid
    
    @staticmethod
    def validate_transformed_data(data: List[Dict[str, Any]]) -> bool:
        """
        Validate transformed data before batch generation
        
        Args:
            data: List of transformed records
        
        Returns:
            True if all records are valid
        """
        required_fields = ["InvestmentId", "ExchangeId", "ISIN"]
        
        for record in data:
            for field in required_fields:
                if field not in record or record[field] is None:
                    logger.error(f"Missing field {field} in record: {record}")
                    return False
        
        logger.info(f"Transformed data validation passed for {len(data)} records")
        return True
```

---

## Create `requirements.txt`

```
python-dotenv==1.0.0
psycopg2-binary==2.9.9
requests==2.31.0
pandas==2.1.1
```

---

## Create `main.py` (Main Orchestration)

```python
#!/usr/bin/env python3
"""
Main orchestration script for ISIN to BBG Symbol mapping
Executes all 6 steps of the process
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import Config
from src.database.db_connection import DatabaseConnection
from src.database.queries import QUERY_GET_ISIN_WITHOUT_BBG
from src.data_processor.mapper import ISINToBBGMapper
from src.data_processor.validator import DataValidator
from src.data_processor.transformer import DataTransformer
from src.batch_generator.batch_creator import BatchCreator
from src.utils.logger import get_logger

logger = get_logger(__name__)

class MainPipeline:
    """Main pipeline orchestrator"""
    
    def __init__(self):
        """Initialize pipeline components"""
        self.db_conn = None
        self.mapper = ISINToBBGMapper()
        self.validator = DataValidator()
        self.transformer = DataTransformer()
        self.batch_creator = BatchCreator()
    
    def step_1_retrieve_isin_data(self, limit: int = 100) -> list:
        """
        STEP 1: Retrieve Ids with ISIN where BBG Symbol & BBGID are not updated
        
        Args:
            limit: Maximum number of records to retrieve
        
        Returns:
            List of records with ISIN and related fields
        """
        logger.info("="*60)
        logger.info("STEP 1: Retrieving ISIN records without BBG Symbol/BBGID")
        logger.info("="*60)
        
        try:
            conn = DatabaseConnection.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(QUERY_GET_ISIN_WITHOUT_BBG, (limit,))
            columns = [desc[0] for desc in cursor.description]
            
            records = []
            for row in cursor.fetchall():
                record = dict(zip(columns, row))
                records.append(record)
            
            cursor.close()
            DatabaseConnection.return_connection(conn)
            
            logger.info(f"Retrieved {len(records)} ISIN records")
            return records
        
        except Exception as e:
            logger.error(f"Step 1 failed: {str(e)}")
            raise
    
    def step_2_3_establish_mappings(self) -> tuple:
        """
        STEP 2 & 3: Establish ExchangeId ↔ ExchangeCode mapping
                    Establish CurrencyId ↔ Currency mapping
        
        Returns:
            Tuple of (exchange_mapping, currency_mapping)
        """
        logger.info("="*60)
        logger.info("STEP 2 & 3: Establishing Exchange and Currency Mappings")
        logger.info("="*60)
        
        # For now, we use the constants already in the data
        # In production, you'd query the mappings from your database
        
        logger.info("Exchange and Currency mappings established from database records")
        return None, None
    
    def step_4_map_to_figi(self, isin_records: list) -> list:
        """
        STEP 4: Retrieve data from OpenFIGI API using ISIN + ExchangeCode + Currency
        
        Args:
            isin_records: List of ISIN records to map
        
        Returns:
            List of transformed results with BBG Symbol and FIGI
        """
        logger.info("="*60)
        logger.info("STEP 4: Calling OpenFIGI API to map ISIN to FIGI")
        logger.info("="*60)
        
        try:
            # Validate records before API calls
            valid_records, invalid_records = self.validator.validate_isin_records(isin_records)
            
            if invalid_records:
                logger.warning(f"{len(invalid_records)} invalid records found, skipping...")
            
            # Map valid records
            transformed_data = self.mapper.map_batch(valid_records)
            
            return transformed_data
        
        except Exception as e:
            logger.error(f"Step 4 failed: {str(e)}")
            raise
    
    def step_5_transform_data(self, api_results: list) -> list:
        """
        STEP 5: Transform API data into desired format
                Columns: ISIN, BBG Symbol, FIGI (BBGID)
        
        Args:
            api_results: Results from OpenFIGI API
        
        Returns:
            Transformed data ready for batch files
        """
        logger.info("="*60)
        logger.info("STEP 5: Transforming data into desired format")
        logger.info("="*60)
        
        # Data is already transformed in step 4
        # Additional validation here
        if self.validator.validate_transformed_data(api_results):
            logger.info("Data transformation validation passed")
            return api_results
        else:
            raise ValueError("Data transformation validation failed")
    
    def step_6_generate_batch_files(self, transformed_data: list) -> dict:
        """
        STEP 6: Prepare batch update files
                File 1: InvestmentId, ExchangeId, BBG Symbol
                File 2: InvestmentId, ExchangeId, BBGID (FIGI)
        
        Args:
            transformed_data: Transformed mapping results
        
        Returns:
            Dictionary with paths to generated batch files
        """
        logger.info("="*60)
        logger.info("STEP 6: Generating batch update files")
        logger.info("="*60)
        
        try:
            bbg_updates, bbgid_updates = self.transformer.prepare_batch_updates(transformed_data)
            
            file_paths = self.batch_creator.generate_batch_files(bbg_updates, bbgid_updates)
            
            logger.info("Batch files generated successfully")
            logger.info(f"  BBG Symbol file: {file_paths['bbg_symbol_file']}")
            logger.info(f"  BBGID file: {file_paths['bbgid_file']}")
            
            return file_paths
        
        except Exception as e:
            logger.error(f"Step 6 failed: {str(e)}")
            raise
    
    def run(self, isin_limit: int = 100):
        """
        Execute complete pipeline (Steps 1-6)
        
        Args:
            isin_limit: Maximum number of ISIN records to process
        """
        logger.info("╔═══════════════════════════════════════════════════════╗")
        logger.info("║  ISIN to BBG Symbol Mapping Pipeline Started         ║")
        logger.info("╚═══════════════════════════════════════════════════════╝")
        
        try:
            # Initialize database connection
            DatabaseConnection.initialize_pool()
            
            # Step 1: Retrieve ISIN data
            isin_records = self.step_1_retrieve_isin_data(limit=isin_limit)
            
            if not isin_records:
                logger.warning("No ISIN records found. Pipeline halted.")
                return
            
            # Step 2 & 3: Establish mappings (already in records)
            self.step_2_3_establish_mappings()
            
            # Step 4: Call OpenFIGI API
            api_results = self.step_4_map_to_figi(isin_records)
            
            if not api_results:
                logger.warning("No successful API mappings. Pipeline halted.")
                return
            
            # Step 5: Transform data
            transformed_data = self.step_5_transform_data(api_results)
            
            # Step 6: Generate batch files
            batch_files = self.step_6_generate_batch_files(transformed_data)
            
            logger.info("╔═══════════════════════════════════════════════════════╗")
            logger.info("║  Pipeline Completed Successfully                      ║")
            logger.info("╚═══════════════════════════════════════════════════════╝")
            
            return batch_files
        
        except Exception as e:
            logger.error(f"Pipeline failed with error: {str(e)}")
            raise
        
        finally:
            # Cleanup
            DatabaseConnection.close_all_connections()


def main():
    """Entry point"""
    pipeline = MainPipeline()
    result = pipeline.run(isin_limit=100)
    print("\n✅ Pipeline execution complete!")
    print(f"Output files: {result}")


if __name__ == "__main__":
    main()
```

---

## Create `README.md`

```markdown
# OpenFIGI ISIN to BBG Symbol Mapping

A production-grade Python project to map ISIN codes to BBG Symbols and FIGIs using the OpenFIGI API.

## Setup Instructions

### 1. Clone/Initialize Project
\`\`\`bash
mkdir openfigi-bbg-mapper
cd openfigi-bbg-mapper
git init
\`\`\`

### 2. Create Virtual Environment
\`\`\`bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
\`\`\`

### 3. Install Dependencies
\`\`\`bash
pip install -r requirements.txt
\`\`\`

### 4. Configure Environment
\`\`\`bash
cp .env.example .env
# Edit .env with your actual values
\`\`\`

### 5. Run Pipeline
\`\`\`bash
python main.py
\`\`\`

## Project Structure

```
openfigi-bbg-mapper/
├── config/              # Configuration management
├── src/                 # Source code
├── logs/                # Application logs
├── output/              # Generated batch files
├── main.py              # Main script
└── requirements.txt     # Dependencies
```

## Process Overview

**Step 1:** Retrieve ISIN records from database
**Step 2-3:** Establish Exchange and Currency mappings
**Step 4:** Call OpenFIGI API
**Step 5:** Transform API response
**Step 6:** Generate batch update CSV files

## API Key

Get your free OpenFIGI API key at: https://www.openfigi.com/api

## Security

- Never commit `.env` file to Git
- Use `.env.example` as template
- Rotate API keys periodically
- Review logs for any issues

## Documentation

See `project-structure.md` and `implementation-guide.md` for detailed information.
```

---

## Getting Started Checklist

- [ ] Create project folder
- [ ] Initialize Git repository
- [ ] Create Python virtual environment
- [ ] Copy folder structure from `project-structure.md`
- [ ] Create all files from `implementation-guide.md`
- [ ] Create `.env` file with your actual credentials
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Test database connection
- [ ] Test OpenFIGI API connection
- [ ] Run `main.py`
```
