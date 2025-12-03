import os
import pandas as pd
import pyodbc
import sys
from dotenv import load_dotenv

load_dotenv()

def pull_data_from_database(ids_to_search):
    # --- Connection Details ---
    SERVER = os.getenv('SERVER') 
    DATABASE = os.getenv('DATABASE')
    USERNAME = os.getenv('USERNAME')
    PASSWORD = os.getenv('PASSWORD')
    TABLE_NAME = os.getenv('TABLE_NAME')
    # ... other connection details as before ...

    # Example List of IDs you want to search for
    # These are the values that will go inside the IN clause
    # ids_to_search = ['US3205175017', 'US78462F1030', 'US0378331005']

    # --- Establish Connection ---
    
    try:
        conn_str = (
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER={SERVER};'
            f'DATABASE={DATABASE};'
            f'UID={USERNAME};'
            f'PWD={PASSWORD}'
        )
        conn = pyodbc.connect(conn_str)
        print("Connection established successfully using SQL Auth!")

        # --- Prepare Query ---
        # 1. Create a placeholder string for the IN clause
        # This creates a string like '?, ?, ?, ?' based on the list length
        placeholders = ', '.join(['?'] * len(ids_to_search))
        
        # 2. Construct the SQL query with the dynamic placeholders
        # Ensure your column name is correct (e.g., 'Id', 'UserID', etc.)
        sql_query = f"SELECT top 10 InvestmentId, ExchangeId, RIGHT(CurrencyId, 3), Identifier FROM InvestmentIdentifier WHERE IdentifierType = 2 and Identifier IN ({placeholders})"


        print(f"Executing SQL: {sql_query}")
        print(f"With parameters: {ids_to_search}")

        # 3. Execute the query using pandas read_sql_query
        # Pass the connection and the list of IDs as parameters (the last argument)
        sqlPulledIds = pd.read_sql_query(sql_query, conn, params=ids_to_search)
        
        # Display results
        # print(sqlPulledIds.head())
        print(f"Retrieved {len(sqlPulledIds)} rows.")

        return sqlPulledIds
    
    except pyodbc.Error as e:
        print("Error connecting to database: ", e)
        sys.exit(1)

    finally:
        if 'conn' in locals():
            conn.close()
            print("Connection closed.")