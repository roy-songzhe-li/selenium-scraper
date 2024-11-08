import json


def preprocess_json_file(json_file):
    # Read the original JSON file
    with open(json_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    # Add '[' at the beginning
    lines.insert(0, '[\n')
    # Remove the last comma at the end and add ']'
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip().endswith(','):
            lines[i] = lines[i].rstrip(',\n') + '\n'
            break
    lines.append(']\n')

    # Write the modified content to a temporary JSON file
    temp_json_file = 'temp_' + json_file
    with open(temp_json_file, 'w', encoding='utf-8') as file:
        file.writelines(lines)

    return temp_json_file


def extract_sub_urls(json_file, output_file):
    # Preprocess the JSON file
    temp_json_file = preprocess_json_file(json_file)

    # Open and read the preprocessed JSON file
    with open(temp_json_file, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Open a text file for writing
    with open(output_file, 'w', encoding='utf-8') as file:
        # Iterate through each element in the list
        for item in data:
            # Check if the 'sub_url' key exists
            if 'sub_url' in item:
                # Get the sub_url
                sub_url = item['sub_url']
                # Write to the file and add a newline
                file.write(sub_url + '\n')
                # Print to the terminal
                print(sub_url)


# File paths
json_file = 'www_northadelaidepodiatry_com_au.json'
output_file = 'sub_urls.txt'

# Extract sub_urls and write to file
extract_sub_urls(json_file, output_file)