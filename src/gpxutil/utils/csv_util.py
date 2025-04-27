import csv
from typing import Optional

from src.gpxutil.utils.data_type_processor import none_if_empty


def csv_to_dict_list(
        file_path: str,
        processor: callable = None,  # 新增：行处理回调函数
        **kwargs
) -> list[dict]:
    """
    将 CSV 文件转换为字典列表，支持自定义行处理

    :param file_path: CSV 文件路径
    :param processor: 可选的回调函数，接收原始行字典，返回处理后的字典
    :param kwargs: 传递给 `open` 的其他参数（如编码方式）
    :return: 处理后的字典列表
    """

    with open(file_path, 'r', **kwargs) as csv_file:
        csv_reader = csv.DictReader(csv_file)

        ret_list = []
        for raw_row in csv_reader:
            # 基础处理：空字符串转 None
            base_row = {
                key: none_if_empty(value)
                for key, value in raw_row.items()
            }

            # 如果提供了处理函数，则应用自定义逻辑
            if processor is not None:
                processed_row = processor(base_row)
                ret_list.append(processed_row)
            else:
                ret_list.append(base_row)

        return ret_list

def call_func_to_specified_dict_key(row: dict[str, Optional[str]], key: str, func: callable):
    """
    Apply a given function to the value of a specified key in a dictionary.

    This function aims to operate on a specific key within a dictionary, applying a passed function to modify its value.
    It first checks if the key exists in the dictionary and ensures that the value for that key is not None.
    If these conditions are met, the function is applied to the value of that key, and the dictionary is updated with the new value.

    :param row: A dictionary where the key-value pairs are of type string, and the value can be None or a string.
    :param key: The key in the dictionary whose value is to be modified.
    :param func: The function to apply to the value of the specified key. This function should accept a string parameter and return a string.
    """
    if key in row and row[key] is not None:
        row[key] = func(row[key])

def call_func_to_specified_dict_key_list(row: dict[str, Optional[str]], keys: list[str], func: callable):
    for key in keys:
        call_func_to_specified_dict_key(row, key, func)

def dict_list_to_csv(dict_list: list[dict], file_path: str, **kwargs):
    """
    将字典列表转换为 CSV 文件

    :param dict_list: 字典列表
    :param file_path: CSV 文件路径
    :param kwargs: 传递给 open() 的其他参数（如编码方式）
    """
    fieldnames = dict_list[0].keys()
    with open(file_path, 'w', newline='', **kwargs) as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for row_dict in dict_list:
            write_row = row_dict.copy()
            writer.writerow(write_row)

if __name__ == '__main__':
    a = csv_to_dict_list("../../../test/to_csv.csv")
    print(a[0])