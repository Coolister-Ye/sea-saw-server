import itertools
import importlib
from rest_framework.serializers import ListSerializer, ModelSerializer


def combine_lists(lst_a, lst_b):
    """
    将两个列表中的字典合并，返回一个包含所有合并结果的列表。
    合并时，如果两个列表的元素是字典，将它们合并为字典。
    """
    if not lst_a:
        return lst_b
    if not lst_b:
        return lst_a

    res = []
    # 遍历两个列表中的元素，将每个元素合并为字典并加入结果列表
    for b in lst_b:
        for a in lst_a:
            res.append({**a, **b})  # 合并字典，**表示解包字典并合并
    return res


def traverse(data, serializer, prefix=""):
    """
    遍历给定的数据，将嵌套的数据结构（如字典和列表）递归转换为扁平结构。
    这会基于给定的序列化器将数据递归地展开。
    """
    # 如果序列化器是一个 ListSerializer（即多个项目的序列化器）
    if isinstance(serializer, ListSerializer):
        # 对列表中的每个项应用 traverse，并将结果合并成一个列表
        _res = [traverse(d, serializer.child, prefix) for d in data]
        return list(itertools.chain.from_iterable(_res))  # 扁平化列表

    # 如果序列化器不是 ModelSerializer，返回当前的 prefix 和数据
    if not isinstance(serializer, ModelSerializer):
        return {prefix: data}

    # 如果数据为 None，则返回 None
    if data is None:
        return

    result = {}
    # 遍历数据中的每个字段，将字段的值通过序列化器进行处理
    for k, v in data.items():
        # 递归生成字段的前缀（如 'field1.subfield'）
        _prefix = f'{prefix}.{k}' if prefix else k
        _serializer = serializer.fields[k]  # 获取字段对应的序列化器
        _result = traverse(v, _serializer, _prefix)  # 递归处理字段值
        if isinstance(_result, dict):
            result[k] = [_result]  # 如果是字典，放入列表中
        else:
            result[k] = _result

    # 最后合并所有字段的结果
    dkr_result = []
    for k, v in result.items():
        dkr_result = combine_lists(dkr_result, v)  # 合并字段的结果
    return dkr_result


def flatten_header(serializer, prefix=""):
    """
    获取序列化器的所有字段名（包含嵌套字段），并生成一个包含所有字段路径的列表。
    用于获取所有字段的头部信息（如字段的名称路径）。
    """
    # 如果序列化器是一个 ListSerializer，递归处理其子序列化器
    if isinstance(serializer, ListSerializer):
        return flatten_header(serializer.child, prefix)

    # 如果序列化器不是 ModelSerializer，返回当前 prefix
    if not isinstance(serializer, ModelSerializer):
        return [prefix]

    result = []
    # 遍历序列化器的字段，并递归处理每个字段
    for k, v in serializer.fields.items():
        _prefix = f'{prefix}.{k}' if prefix else k  # 拼接当前字段的前缀
        _headers = flatten_header(v, _prefix)  # 递归获取字段头部信息
        result.extend(_headers)  # 将所有头部信息扩展到结果列表中

    return result


def flatten(queryset, serializer):
    """
    序列化给定的 queryset，并将结果进行扁平化处理。
    同时生成字段头部信息（字段名的路径）。
    """
    # 使用序列化器序列化 queryset 数据
    serialized = serializer(queryset, many=True)

    # 获取字段的头部信息
    headers = flatten_header(serialized)

    # 对序列化后的数据进行扁平化处理
    data = traverse(serialized.data, serialized)

    return data, headers


def dynamic_import_model(app_name, model_name):
    """
    Dynamically import a model given an app name and model name as strings.
    """
    try:
        # Construct the module path (e.g., 'myapp.models')
        module_path = f"{app_name}.models"

        # Dynamically import the module
        models_module = importlib.import_module(module_path)

        # Get the model class from the imported module
        model_class = getattr(models_module, model_name)
        return model_class
    except ImportError as e:
        raise Exception(f"Failed to import model {model_name} from app {app_name}: {e}")
    except AttributeError:
        raise Exception(f"Model {model_name} not found in app {app_name}")


def dynamic_import_serializer(app_name, serializer_name):
    """
    Dynamically import a serializer given an app name and serializer name as strings.
    """
    try:
        # Construct the module path (e.g., 'myapp.serializers')
        module_path = f"{app_name}.serializers"

        # Dynamically import the module
        serializers_module = importlib.import_module(module_path)

        # Get the serializer class from the imported module
        serializer_class = getattr(serializers_module, serializer_name)
        return serializer_class
    except ImportError as e:
        raise Exception(f"Failed to import serializer {serializer_name} from app {app_name}: {e}")
    except AttributeError:
        raise Exception(f"Serializer {serializer_name} not found in app {app_name}")


