# Quick Start Guide - Environment Configuration & .env Setup

## 🚀 5-Minute Setup

### Step 1: Create Project Structure
```bash
mkdir openfigi-bbg-mapper
cd openfigi-bbg-mapper
git init
```

### Step 2: Create Python Virtual Environment
```bash
# On macOS/Linux
python3 -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
venv\Scripts\activate
```

### Step 3: Create .env File (MOST IMPORTANT)

**Create file: `.env` in project root**

```env
# ===== OpenFIGI API Configuration =====
OPENFIGI_API_KEY=your_actual_api_key_here_from_openfigi.com
OPENFIGI_BASE_URL=https://api.openfigi.com/v3

# ===== Database Configuration =====
DATABASE_HOST=your_postgres_host.com
DATABASE_PORT=5432
DATABASE_NAME=your_database_name
DATABASE_USER=your_username
DATABASE_PASSWORD=your_secure_password

# ===== Application Configuration =====
LOG_LEVEL=INFO
DEBUG=False
```

### Step 4: Create .gitignore

**Create file: `.gitignore` in project root**

```
# Environment variables - NEVER COMMIT
.env
.env.local
.env.*.local

# Virtual environment
venv/
env/
ENV/

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Logs
logs/
*.log

# Database
*.db
*.sqlite
*.sqlite3
```

### Step 5: Create requirements.txt

**Create file: `requirements.txt` in project root**

```
python-dotenv==1.0.0
psycopg2-binary==2.9.9
requests==2.31.0
pandas==2.1.1
```

### Step 6: Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🔐 Understanding .env Configuration

### Why .env File?

| Aspect | Benefit |
|--------|---------|
| **Security** | API keys never hardcoded in source code |
| **Privacy** | .env in .gitignore prevents accidental commits |
| **Flexibility** | Different configs for dev/staging/production |
| **Team Safe** | Share .env.example, not actual .env |
| **Environment Aware** | Use different keys for different environments |

### Load .env in Python

**In your config/settings.py:**

```python
from dotenv import load_dotenv
import os
from pathlib import Path

# Load .env file
ENV_PATH = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

# Access variables
API_KEY = os.getenv("OPENFIGI_API_KEY")
BASE_URL = os.getenv("OPENFIGI_BASE_URL", "https://api.openfigi.com/v3")  # With default
```

### Error Handling for Missing Variables

```python
api_key = os.getenv("OPENFIGI_API_KEY")
if not api_key:
    raise ValueError("OPENFIGI_API_KEY not found in .env file")
```

---

## 📝 Complete Folder Structure After Setup

```
openfigi-bbg-mapper/
│
├── .env                          ✅ CREATE THIS (DO NOT COMMIT)
├── .env.example                  ✅ CREATE THIS (SHARE WITH TEAM)
├── .gitignore                    ✅ CREATE THIS
├── requirements.txt              ✅ CREATE THIS
├── README.md
│
├── config/
│   ├── __init__.py              (empty or imports)
│   ├── settings.py              (loads .env)
│   └── constants.py             (app constants)
│
├── src/
│   ├── __init__.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── db_connection.py
│   │   └── queries.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── openfigi_client.py
│   ├── data_processor/
│   │   ├── __init__.py
│   │   ├── mapper.py
│   │   ├── transformer.py
│   │   └── validator.py
│   ├── batch_generator/
│   │   ├── __init__.py
│   │   └── batch_creator.py
│   └── utils/
│       ├── __init__.py
│       ├── logger.py
│       └── helpers.py
│
├── logs/                         (auto-created)
├── output/                       (auto-created)
├── main.py                       (main script)
└── venv/                         (auto-created)
```

---

## ✅ Configuration Checklist

Before running the project:

- [ ] Created `.env` file with actual API key from OpenFIGI
- [ ] Created `.env.example` as template
- [ ] Added `.env` to `.gitignore`
- [ ] Database credentials are correct in `.env`
- [ ] `.env` is in project root (same level as main.py)
- [ ] Ran `pip install -r requirements.txt`
- [ ] Virtual environment is activated
- [ ] All folder structure created as shown

---

## 🐛 Troubleshooting

### Issue: "API_KEY not found"
**Solution:** Check that .env file exists in project root and OPENFIGI_API_KEY is set

### Issue: "Database connection failed"
**Solution:** Verify DATABASE_HOST, DATABASE_USER, DATABASE_PASSWORD in .env

### Issue: "dotenv not found"
**Solution:** Run `pip install python-dotenv` or check requirements.txt

### Issue: ".env changes not detected"
**Solution:** Restart Python process or virtual environment

### Issue: "Permission denied" on logs/
**Solution:** Ensure logs/ and output/ folders have write permissions

---

## 🔒 Security Best Practices Checklist

✅ **Never commit .env to Git**
```bash
# Verify in .gitignore
grep -i ".env" .gitignore
```

✅ **Share .env.example instead**
```bash
# Team gets this template
cp .env .env.example
# Remove actual secrets from .env.example
```

✅ **Rotate API keys periodically**
- Visit https://www.openfigi.com/api
- Generate new API key
- Update .env
- Delete old key

✅ **Use environment variables in production**
- Don't rely on local .env files
- Use container secrets or cloud providers' secret managers

✅ **Log rotation enabled**
- Logs auto-rotate at 10MB
- Keeps last 5 backup files
- Prevents disk space issues

---

## 📚 Complete Usage Example

### Run Full Pipeline
```bash
cd openfigi-bbg-mapper
source venv/bin/activate
python main.py
```

### Expected Output
```
============================================================
║  ISIN to BBG Symbol Mapping Pipeline Started         ║
============================================================

STEP 1: Retrieving ISIN records without BBG Symbol/BBGID
Retrieved 100 ISIN records

STEP 2 & 3: Establishing Exchange and Currency Mappings
Exchange and Currency mappings established from database records

STEP 4: Calling OpenFIGI API to map ISIN to FIGI
Validation complete: 98 valid, 2 invalid records
Completed batch mapping: 95 successful mappings

STEP 5: Transforming data into desired format
Data transformation validation passed for 95 records

STEP 6: Generating batch update files
Generated batch files at output/
  BBG Symbol file: batch_bbg_symbol_20250101_120000.csv
  BBGID file: batch_bbgid_20250101_120000.csv

============================================================
║  Pipeline Completed Successfully                      ║
============================================================

✅ Pipeline execution complete!
Output files: {'bbg_symbol_file': '...', 'bbgid_file': '...'}
```

---

## 📞 Getting OpenFIGI API Key

1. Visit: https://www.openfigi.com/api
2. Click "Request an API key"
3. Fill in the form (free!)
4. Check your email for API key
5. Add to .env: `OPENFIGI_API_KEY=your_key_here`

**API Key Benefits:**
- Higher rate limits (vs. no API key)
- Better support
- Production ready

---

## 🎯 Next Steps After Initial Setup

1. **Test database connection:**
   ```python
   from src.database.db_connection import DatabaseConnection
   conn = DatabaseConnection.get_connection()
   print("Connected!")
   ```

2. **Test OpenFIGI API:**
   ```python
   from src.api.openfigi_client import OpenFIGIClient
   client = OpenFIGIClient()
   result = client.map_isin_to_figi("US0378331005", "US", "USD")
   print(result)
   ```

3. **Run full pipeline:**
   ```bash
   python main.py
   ```

4. **Check logs:**
   ```bash
   tail -f logs/app.log
   ```

---

## 📖 Files Reference

| File | Purpose | Must Create |
|------|---------|------------|
| `.env` | Your actual secrets | ✅ YES |
| `.env.example` | Template for team | ✅ YES |
| `.gitignore` | Git ignore rules | ✅ YES |
| `requirements.txt` | Python dependencies | ✅ YES |
| `config/settings.py` | Load .env config | ✅ YES |
| `main.py` | Run pipeline | ✅ YES |

---

**🎉 You're ready to start! Create the .env file first, then run the pipeline.**
