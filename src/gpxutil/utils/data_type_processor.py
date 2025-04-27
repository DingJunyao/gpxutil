from functools import partial

def none_if_empty(item: str):
    """如 item 为空或空字符串，则返回 None。否则，返回原值。不要用于其他类型。"""
    return item if item else None


def is_empty_or_none(item: str):
    """判断一个字符串是不是 None 或空字符串。不要用于其他类型。"""
    return none_if_empty(item) is None


def process_or_none(data, processor: callable):
    """
    如果为 None，则返回执行函数后的结果；否则返回 None。
    :param data:
    :param processor:
    :return:
    """
    return processor(data) if data is not None else None

float_or_none = partial(process_or_none, processor=float)

if __name__ == '__main__':
    print(float_or_none('3'))
