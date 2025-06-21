from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import wraps
from typing import Iterable, Callable, TypeVar, Collection

from tqdm import tqdm

T = TypeVar('T')
R = TypeVar('R')

def threaded_map(desc="Processing", unit="item(s)", max_workers=None):
    def decorator(func):
        @wraps(func)
        def wrapper(items, *args, **kwargs):
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交任务
                futures = {executor.submit(func, item, *args, **kwargs): item
                           for item in items}

                # 进度条处理
                for future in tqdm(as_completed(futures),
                                   total=len(items),
                                   desc=desc,
                                   unit=unit):
                    future.result()  # 可获取返回值或处理异常

        return wrapper

    return decorator


# def threaded_map_list(desc="Processing...", unit='item(s)', ensure_order: bool = True, max_workers=None):
#     def decorator(func):
#         @wraps(func)
#         def wrapper(in_list, *args, **kwargs):
#             out_list = [None] * len(in_list)
#             with ThreadPoolExecutor(max_workers=max_workers) as executor:
#                 if ensure_order:
#                     futures = {
#                         executor.submit(func, item, *args, **kwargs): idx
#                         for idx, item in enumerate(in_list)
#                     }
#                 else:
#                     futures = {
#                         executor.submit(func, item, *args, **kwargs): item
#                         for item in in_list
#                     }
#                 for future in tqdm(as_completed(futures), total=len(futures), desc=desc, unit=unit):
#                     result = future.result()
#                     out_list[futures[future]] = result  # 按索引存储结果
#             return out_list
#         return wrapper
#     return decorator


def threaded_map_list(
    desc: str = "Processing...",
    unit: str = 'item(s)',
    ensure_order: bool = True,
    max_workers: int | None = None
) -> Callable[[Callable[[T], R]], Callable[[Collection[T]], list[R]]]:
    """
    通过多线程执行方式，对集合中的每个元素应用给定的函数，并返回结果列表。

    使用方式：

    @threaded_map_list()
    def test_func(list_item):
        return list_item * 2

    l = range(100000)
    print(test_func(l)[0])

    :param desc: 进度条的描述文本。
    :param unit: 进度条中处理单位的字符串表示。
    :param ensure_order: 是否保持结果顺序与输入集合顺序一致。
    :param max_workers: 最大工作线程数，如果为None，则使用默认值。
    :return 一个装饰器，用于装饰接受单个参数并返回结果的函数。装饰后的函数将接受一个集合作为参数，并返回一个包含每个元素处理结果的列表。
    """
    def decorator(func: Callable[[T], R]) -> Callable[[Collection[T]], list[R]]:
        @wraps(func)
        def wrapper(in_list: Collection[T]) -> list[R]:
            out_list = [None] * len(in_list)
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                if ensure_order:
                    futures = {
                        executor.submit(func, item): idx
                        for idx, item in enumerate(in_list)
                    }
                else:
                    futures = {
                        executor.submit(func, item): item
                        for item in in_list
                    }

                for future in tqdm(as_completed(futures), total=len(futures), desc=desc, unit=unit):
                    result = future.result()
                    out_list[futures[future]] = result  # 按索引存储结果

            return out_list
        return wrapper
    return decorator

def metric(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        import time
        start_time = time.time()
        result = fn(*args, **kwargs)
        end_time = time.time()
        elapsed_time = (end_time - start_time) * 1000  # 转换为毫秒
        print('%s executed in %.2f ms' % (fn.__name__, elapsed_time))
        return result
    return wrapper

if __name__ == '__main__':

    l = range(100000)

    @metric
    @threaded_map_list()
    def test_func(list_item):
        return list_item * 2

    @metric
    def test_func_2(in_list):
        out_list = []
        for i in tqdm(in_list, total=len(in_list), desc="Processing...", unit='item(s)'):
            out_list.append(i * 2)
        return out_list

    print(test_func(l)[0])  # 输出将保持与输入列表相同的顺序
    print(test_func_2(l)[0])
