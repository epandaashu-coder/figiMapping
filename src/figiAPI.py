import pandas as pd
import requests
import json
import openpyxl


def get_figi(payload):
    """
    Send a POST request to OpenFIGI and return response as DataFrame.

    Args:
        payload (list/dict): Your JSON payload (Python object, not string)
        api_key (str): Your OpenFIGI API key

    Returns:
        pd.DataFrame: Response converted to a pandas DataFrame
    """
    url = 'https://api.openfigi.com/v3/mapping'
    api_key = '879eac47-fad9-4138-8726-24c8f563701b'
    headers = {
        'Content-Type': 'text/json',
        'X-OPENFIGI-APIKEY': api_key
    }
    data = json.dumps(payload)
    # printing("Payload:", data)
    print(data)
    # Send POST request
    response = requests.post(url, headers=headers, data=data)

    # Error handling
    try:
        response.raise_for_status()
    except Exception as e:
        print("Error:", e)
        print("Response text:", response.text)
        return None

    # Convert response json → DataFrame
    json_data = response.json()
    return pd.DataFrame(json_data)


# DataFrame with ISIN data

# DataFrame with ISIN data
df = pd.DataFrame({
    'idType': ['ID_ISIN', 'ID_ISIN', 'ID_ISIN'],
    'idValue': ['US0378331005', 'US5949181045', 'DE0008469008'],
    'exchCode': ['US', 'US', 'GF'],
    'currency': ['USD', 'USD', 'EUR']
})

payload = df.to_dict(orient='records')

figi_df = get_figi(payload)
print(figi_df)

figi_df.to_excel('figi_output.xlsx', index=False)