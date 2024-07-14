import json


def preprocess_json_file(json_file):
    # 读取原始 JSON 文件
    with open(json_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    # 添加 '[' 到头部
    lines.insert(0, '[\n')
    # 在尾部删除最后一个逗号并添加 ']'
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip().endswith(','):
            lines[i] = lines[i].rstrip(',\n') + '\n'
            break
    lines.append(']\n')

    # 将修改后的内容写入临时 JSON 文件
    temp_json_file = 'temp_' + json_file
    with open(temp_json_file, 'w', encoding='utf-8') as file:
        file.writelines(lines)

    return temp_json_file


def extract_sub_urls(json_file, output_file):
    # 预处理 JSON 文件
    temp_json_file = preprocess_json_file(json_file)

    # 打开并读取预处理后的 JSON 文件
    with open(temp_json_file, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # 打开一个文本文件用于写入
    with open(output_file, 'w', encoding='utf-8') as file:
        # 遍历列表中的每个元素
        for item in data:
            # 检查是否存在 'sub_url' 键
            if 'sub_url' in item:
                # 获取 sub_url
                sub_url = item['sub_url']
                # 写入文件并添加换行符
                file.write(sub_url + '\n')
                # 打印到终端
                print(sub_url)


# 文件路径
json_file = 'test.json'
output_file = 'sub_urls.txt'

# 提取 sub_urls 并写入文件
extract_sub_urls(json_file, output_file)