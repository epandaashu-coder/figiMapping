import pandas as pd
from src.pulling_data_InvIdent import pull_data_from_database

# Example list of IDs to search for
id_list = ['US3205175017', 'US78462F1030', 'US0378331005']

print("Starting data pull...")

sqlPulledIds = pull_data_from_database(id_list)

print("Data pull complete.")
print(sqlPulledIds.head())