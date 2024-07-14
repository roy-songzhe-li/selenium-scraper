import json
import csv

def json_to_csv(json_file, csv_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
        raise ValueError("JSON data should be a list of dictionaries")
    
    required_keys = {'sub_url', 'html', 'text'}
    for item in data:
        if not required_keys.issubset(item.keys()):
            raise ValueError(f"Each dictionary should have the keys: {required_keys}")
    
    header = ['sub_url', 'html', 'text']

    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        for row in data:
            writer.writerow(row)

json_file = 'suburls-ndis-gov-au.json'
csv_file = 'suburls-ndis-gov-au.csv'
json_to_csv(json_file, csv_file)
