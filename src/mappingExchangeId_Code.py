import pandas as pd

def map_exchange_id_to_code(sqlPulledIds, exchange_mapping):
    """
    Maps ExchangeId in the sqlPulledIds DataFrame to their corresponding exchange codes
    using the provided exchange_mapping dictionary.

    Parameters:
    sqlPulledIds (pd.DataFrame): DataFrame containing at least an 'ExchangeId' column.
    exchange_mapping (dict): Dictionary mapping ExchangeId to exchange codes.

    Returns:
    pd.DataFrame: Updated DataFrame with a new 'ExchangeCode' column.
    """
    # Create a new column 'ExchangeCode' by mapping 'ExchangeId' using the exchange_mapping dictionary
    sqlPulledIds['ExchangeCode'] = sqlPulledIds['ExchangeId'].map(exchange_mapping)

    return sqlPulledIds