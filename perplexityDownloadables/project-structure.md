# OpenFIGI ISIN to BBG Mapping - Project Structure

## 📁 Complete Project Folder Structure

```
openfigi-bbg-mapper/
│
├── .env                              # Environment variables (NEVER commit to Git)
├── .env.example                      # Template for environment variables
├── .gitignore                        # Git ignore file
├── requirements.txt                  # Python dependencies
├── README.md                         # Project documentation
│
├── config/
│   ├── __init__.py
│   ├── settings.py                  # Configuration management
│   └── constants.py                 # Constants and enums
│
├── src/
│   ├── __init__.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── db_connection.py         # Database connection logic
│   │   └── queries.py               # SQL queries
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── openfigi_client.py       # OpenFIGI API wrapper
│   │
│   ├── data_processor/
│   │   ├── __init__.py
│   │   ├── mapper.py                # Mapping logic
│   │   ├── transformer.py           # Data transformation
│   │   └── validator.py             # Data validation
│   │
│   ├── batch_generator/
│   │   ├── __init__.py
│   │   └── batch_creator.py         # Batch update file generation
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logger.py                # Logging setup
│       └── helpers.py               # Helper functions
│
├── logs/
│   ├── app.log
│   └── errors.log
│
├── output/
│   ├── batch_bbg_symbol_updates.csv
│   └── batch_bbgid_updates.csv
│
└── main.py                          # Main execution script
```

---

## 📋 File Descriptions

| File | Purpose |
|------|---------|
| `.env` | Stores API_KEY and BASE_URL (DO NOT COMMIT) |
| `.env.example` | Template showing required environment variables |
| `config/settings.py` | Loads and manages environment variables |
| `src/database/db_connection.py` | Handles database connections |
| `src/api/openfigi_client.py` | Wraps OpenFIGI API calls |
| `src/data_processor/mapper.py` | Maps ISIN + ExchangeCode + Currency to FIGI |
| `src/data_processor/transformer.py` | Transforms raw API response to desired format |
| `src/batch_generator/batch_creator.py` | Generates batch update CSV files |
| `main.py` | Orchestrates all 6 steps |

---

## 🔐 Security Best Practices Implemented

✅ API key stored in .env file (not in code)
✅ .env added to .gitignore (prevents accidental commits)
✅ .env.example shows structure without secrets
✅ Environment variables loaded at startup
✅ Logging of operations (without exposing secrets)
✅ Error handling for missing configuration
