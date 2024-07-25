import json
import pandas as pd


def json_to_excel(json_file, excel_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
        raise ValueError("JSON data should be a list of dictionaries")

    required_keys = {'sub_url', 'html', 'text'}
    for item in data:
        if not required_keys.issubset(item.keys()):
            raise ValueError(f"Each dictionary should have the keys: {required_keys}")

    # Convert the list of dictionaries to a DataFrame
    df = pd.DataFrame(data)

    # Save the DataFrame to an Excel file
    df.to_excel(excel_file, index=False)


json_file = '../../www_ndis_gov_au.json'
excel_file = 'www_ndis_gov_au.xlsx'
json_to_excel(json_file, excel_file)