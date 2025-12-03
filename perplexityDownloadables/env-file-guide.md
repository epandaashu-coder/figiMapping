# .env File Deep Dive & Code Examples

## 🔑 What is .env File?

The `.env` file is a **plain text configuration file** that stores sensitive information and environment-specific settings separately from your code.

### Key Principles:
- ✅ Stores secrets (API keys, database passwords)
- ✅ Never committed to Git
- ✅ Different for each developer/environment
- ✅ Loaded at application startup
- ✅ Accessed via `os.getenv()` in Python

---

## 📋 Complete .env Template for Your Project

```env
# ╔════════════════════════════════════════════════════════════╗
# ║         OpenFIGI ISIN Mapping Configuration               ║
# ╚════════════════════════════════════════════════════════════╝

# ============ OpenFIGI API Configuration ============
# Get API key from: https://www.openfigi.com/api
# Free API key provides higher rate limits
OPENFIGI_API_KEY=your_secret_api_key_from_openfigi
OPENFIGI_BASE_URL=https://api.openfigi.com/v3

# ============ PostgreSQL Database Configuration ============
# These credentials connect to your EquityCoverage database
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=corporate_data
DATABASE_USER=data_analyst
DATABASE_PASSWORD=your_secure_db_password_here

# ============ Application Settings ============
# Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO

# Debug mode (True/False) - enables verbose logging
DEBUG=False

# ============ Optional: Advanced Settings ============
# Max records to retrieve per run (0 = unlimited)
MAX_RECORDS=100

# API request timeout in seconds
API_TIMEOUT=30

# Batch size for OpenFIGI (max 100)
BATCH_SIZE=50
```

---

## 🔐 How to Load and Use .env in Code

### Method 1: Simple Loading (Recommended for Your Project)

**File: `config/settings.py`**

```python
"""
Configuration management using python-dotenv
Loads environment variables from .env file at startup
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# CRITICAL: Load .env file first thing
ENV_PATH = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

class Config:
    """Application configuration from .env"""
    
    # ===== OpenFIGI API =====
    OPENFIGI_API_KEY = os.getenv("OPENFIGI_API_KEY")
    OPENFIGI_BASE_URL = os.getenv("OPENFIGI_BASE_URL", "https://api.openfigi.com/v3")
    
    # ===== Database =====
    DATABASE_HOST = os.getenv("DATABASE_HOST", "localhost")
    DATABASE_PORT = int(os.getenv("DATABASE_PORT", "5432"))
    DATABASE_NAME = os.getenv("DATABASE_NAME")
    DATABASE_USER = os.getenv("DATABASE_USER")
    DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
    
    # ===== Application =====
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    MAX_RECORDS = int(os.getenv("MAX_RECORDS", "0"))
    API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", "100"))
    
    @classmethod
    def validate(cls):
        """Validate required environment variables exist"""
        required = [
            "OPENFIGI_API_KEY",
            "DATABASE_HOST",
            "DATABASE_NAME",
            "DATABASE_USER",
            "DATABASE_PASSWORD"
        ]
        
        missing = [var for var in required if not getattr(cls, var)]
        if missing:
            raise ValueError(f"Missing .env variables: {', '.join(missing)}")
        
        print("✅ All required .env variables are set!")
```

---

### Method 2: Using Config in Your Application

**File: `src/api/openfigi_client.py`**

```python
"""
Example: Using Config with .env variables
"""

from config.settings import Config
import requests

class OpenFIGIClient:
    def __init__(self):
        # Load from .env via Config
        self.api_key = Config.OPENFIGI_API_KEY
        self.base_url = Config.OPENFIGI_BASE_URL
        self.timeout = Config.API_TIMEOUT
        
        # Validate API key is set
        if not self.api_key:
            raise ValueError("OPENFIGI_API_KEY not found in .env file!")
        
        self.headers = {
            "Content-Type": "application/json",
            "X-OPENFIGI-APIKEY": self.api_key
        }
    
    def map_isin(self, isin, exch_code, currency):
        """Call API with rate limiting"""
        url = f"{self.base_url}/mapping"
        
        payload = {
            "idType": "ISIN",
            "idValue": isin,
            "exchCode": exch_code,
            "currency": currency
        }
        
        response = requests.post(
            url,
            json=[payload],
            headers=self.headers,
            timeout=self.timeout  # From .env
        )
        
        return response.json()
```

**File: `src/database/db_connection.py`**

```python
"""
Example: Using .env variables for database connection
"""

from config.settings import Config
import psycopg2

class DatabaseConnection:
    @staticmethod
    def connect():
        """Connect using credentials from .env"""
        try:
            conn = psycopg2.connect(
                host=Config.DATABASE_HOST,
                port=Config.DATABASE_PORT,
                database=Config.DATABASE_NAME,
                user=Config.DATABASE_USER,
                password=Config.DATABASE_PASSWORD
            )
            print("✅ Database connected via .env config")
            return conn
        
        except psycopg2.Error as e:
            print(f"❌ Database connection failed: {e}")
            print(f"Check .env variables:")
            print(f"  DATABASE_HOST={Config.DATABASE_HOST}")
            print(f"  DATABASE_PORT={Config.DATABASE_PORT}")
            print(f"  DATABASE_NAME={Config.DATABASE_NAME}")
            print(f"  DATABASE_USER={Config.DATABASE_USER}")
            raise
```

---

## 🔍 Verifying Your .env Setup

### Test Script: `test_env.py`

```python
#!/usr/bin/env python3
"""
Test script to verify .env file is loaded correctly
Run this BEFORE running main.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("Testing .env Configuration")
print("=" * 60)

# Test 1: Load config
print("\n✓ Test 1: Loading .env file...")
try:
    from config.settings import Config
    print("  ✅ .env file loaded successfully!")
except FileNotFoundError:
    print("  ❌ .env file not found in project root!")
    sys.exit(1)

# Test 2: Check critical variables
print("\n✓ Test 2: Checking critical variables...")
critical_vars = [
    ("OPENFIGI_API_KEY", Config.OPENFIGI_API_KEY),
    ("DATABASE_HOST", Config.DATABASE_HOST),
    ("DATABASE_NAME", Config.DATABASE_NAME),
    ("DATABASE_USER", Config.DATABASE_USER),
]

all_ok = True
for var_name, var_value in critical_vars:
    if var_value:
        print(f"  ✅ {var_name}: {var_value[:10]}..." if len(str(var_value)) > 10 else f"  ✅ {var_name}: {var_value}")
    else:
        print(f"  ❌ {var_name}: NOT SET")
        all_ok = False

# Test 3: Check optional variables
print("\n✓ Test 3: Checking optional variables...")
optional_vars = [
    ("LOG_LEVEL", Config.LOG_LEVEL),
    ("DEBUG", Config.DEBUG),
    ("BATCH_SIZE", Config.BATCH_SIZE),
]

for var_name, var_value in optional_vars:
    print(f"  ℹ️  {var_name}: {var_value}")

# Test 4: Try database connection
print("\n✓ Test 4: Testing database connection...")
try:
    from src.database.db_connection import DatabaseConnection
    conn = DatabaseConnection.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT VERSION();")
    db_version = cursor.fetchone()
    print(f"  ✅ Database connected: {db_version[0][:50]}...")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"  ❌ Database connection failed: {str(e)}")
    all_ok = False

# Test 5: Try API connection
print("\n✓ Test 5: Testing OpenFIGI API connection...")
try:
    from src.api.openfigi_client import OpenFIGIClient
    client = OpenFIGIClient()
    # Test with a known ISIN
    result = client.map_isin("US0378331005", "US", "USD")
    if result.get("status") == "success":
        print(f"  ✅ API connected: Got FIGI {result['data'][0].get('figi')}")
    else:
        print(f"  ⚠️  API response: {result.get('message')}")
except Exception as e:
    print(f"  ❌ API connection failed: {str(e)}")
    all_ok = False

print("\n" + "=" * 60)
if all_ok:
    print("✅ ALL TESTS PASSED - Ready to run main.py!")
else:
    print("❌ SOME TESTS FAILED - Check .env configuration!")
print("=" * 60)

sys.exit(0 if all_ok else 1)
```

**Run the test:**
```bash
python test_env.py
```

---

## 🛠️ Common .env Variable Patterns

### String Variables
```env
# No quotes needed for simple strings
API_KEY=abc123def456
API_URL=https://api.example.com

# Access in Python
api_key = os.getenv("API_KEY")  # "abc123def456"
```

### Numeric Variables
```env
# Store as string, convert in Python
PORT=5432
TIMEOUT=30
MAX_ITEMS=100

# Access and convert
port = int(os.getenv("PORT"))  # 5432
timeout = int(os.getenv("TIMEOUT"))  # 30
```

### Boolean Variables
```env
# Store as string, parse in Python
DEBUG=True
PRODUCTION=False

# Access and parse
debug = os.getenv("DEBUG", "False").lower() == "true"  # True
production = os.getenv("PRODUCTION", "False").lower() == "true"  # False
```

### Complex Values (URLs, Paths)
```env
# Can include special characters
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
OUTPUT_PATH=/data/output/batch_files
API_ENDPOINT=https://api.openfigi.com/v3/mapping

# Access directly
db_url = os.getenv("DATABASE_URL")
output_path = os.getenv("OUTPUT_PATH")
```

### Default Values
```python
# Python allows fallback defaults
api_key = os.getenv("API_KEY", "default-key-if-missing")
timeout = int(os.getenv("TIMEOUT", "30"))  # Default 30 seconds
debug = os.getenv("DEBUG", "False").lower() == "true"  # Default False
```

---

## ❌ Common Mistakes & Solutions

### Mistake 1: Forgetting load_dotenv()
```python
# ❌ WRONG
import os
api_key = os.getenv("OPENFIGI_API_KEY")  # Will be None!

# ✅ CORRECT
from dotenv import load_dotenv
import os
load_dotenv()  # Load .env file first!
api_key = os.getenv("OPENFIGI_API_KEY")  # Now it works
```

### Mistake 2: Spaces in .env values
```env
# ❌ WRONG (spaces included in value)
API_KEY=my secret key

# ✅ CORRECT (no spaces around =)
API_KEY=my_secret_key
```

### Mistake 3: Quotes in .env values
```env
# ❌ Avoid unless necessary
API_KEY="abc123"  # Quotes included in value!

# ✅ Correct (no quotes in .env)
API_KEY=abc123
```

### Mistake 4: Committing .env to Git
```bash
# ❌ WRONG - Leaks all secrets!
git add .env
git commit -m "Add config"

# ✅ CORRECT - Add to .gitignore first
echo ".env" >> .gitignore
git add .gitignore
git commit -m "Add gitignore"
```

### Mistake 5: Wrong variable names
```python
# ❌ WRONG - Typo
database_host = os.getenv("DATABASE_HOSTNAME")  # Not in .env!

# ✅ CORRECT - Exact match
database_host = os.getenv("DATABASE_HOST")  # Matches .env
```

---

## 🔄 Development vs Production

### Development (.env)
```env
DEBUG=True
LOG_LEVEL=DEBUG
DATABASE_HOST=localhost
API_KEY=dev-key-with-low-limits
```

### Staging (.env.staging)
```env
DEBUG=False
LOG_LEVEL=INFO
DATABASE_HOST=staging-db.company.com
API_KEY=staging-key
```

### Production (Environment Variables)
```bash
# Set via environment, not .env file
export DEBUG=False
export LOG_LEVEL=WARNING
export DATABASE_HOST=prod-db.company.com
export API_KEY=prod-key-high-security
```

**Never store production credentials in .env files!**

---

## 📊 .env File Checklist

Before committing to GitHub:

- [ ] .env file created in project root
- [ ] .env file added to .gitignore
- [ ] All required variables have values
- [ ] No spaces around = signs
- [ ] No quotes around values (unless necessary)
- [ ] OPENFIGI_API_KEY is actual API key (not placeholder)
- [ ] DATABASE_PASSWORD is secure
- [ ] DATABASE_HOST is correct
- [ ] .env.example created for team
- [ ] .env.example has NO actual secrets
- [ ] Test script (test_env.py) runs successfully

---

## 🎯 Your .env for This Project

```env
# COPY THIS TEMPLATE TO YOUR .env FILE
# Replace values with your actual credentials

OPENFIGI_API_KEY=your_api_key_from_openfigi.com
OPENFIGI_BASE_URL=https://api.openfigi.com/v3

DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=your_database
DATABASE_USER=your_username
DATABASE_PASSWORD=your_password

LOG_LEVEL=INFO
DEBUG=False
MAX_RECORDS=100
API_TIMEOUT=30
BATCH_SIZE=50
```

**Steps:**
1. Create `.env` in project root
2. Paste above template
3. Replace with YOUR actual values
4. Save file
5. Run `python test_env.py` to verify
6. Run `python main.py` to execute pipeline

---

**🎉 Your .env is now properly configured and secure!**
