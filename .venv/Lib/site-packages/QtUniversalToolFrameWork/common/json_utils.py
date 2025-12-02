# coding:utf-8
import os

import json

def read_json_file(file_path: str) -> dict:

    if not is_json_file(file_path):
        raise ValueError("文件路径不是一个JSON文件")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件路径不存在: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    return data


def is_json_file(file_path: str) -> bool:
    return file_path.lower().endswith(".json")

