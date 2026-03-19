import importlib
import itertools
import logging

from django.utils.translation import gettext as _
from rest_framework.serializers import ListSerializer, ModelSerializer

logger = logging.getLogger(__name__)


def combine_lists(lst_a, lst_b):
    """将两个字典列表做笛卡尔积合并。"""
    if not lst_a:
        return lst_b
    if not lst_b:
        return lst_a
    return [{**a, **b} for b in lst_b for a in lst_a]


def traverse(data, serializer, prefix=""):
    """将序列化后的嵌套数据结构递归展平为行列表，每行是 {字段路径: 值} 的字典。"""
    if isinstance(serializer, ListSerializer):
        rows = [traverse(d, serializer.child, prefix) for d in data]
        return list(itertools.chain.from_iterable(rows))

    if not isinstance(serializer, ModelSerializer):
        return {prefix: data}

    if data is None:
        return

    result = {}
    for k, v in data.items():
        _prefix = f"{prefix}.{k}" if prefix else k
        _result = traverse(v, serializer.fields[k], _prefix)
        result[k] = [_result] if isinstance(_result, dict) else _result

    rows = []
    for v in result.values():
        rows = combine_lists(rows, v)
    return rows


def flatten_header(serializer, prefix=""):
    """递归提取序列化器所有字段的标签，返回 {字段路径: 字段标签} 字典。"""
    if isinstance(serializer, ListSerializer):
        return flatten_header(serializer.child, prefix)

    if not isinstance(serializer, ModelSerializer):
        return {prefix: _(serializer.label) if serializer.label else prefix}

    result = {}
    for k, v in serializer.fields.items():
        _prefix = f"{prefix}.{k}" if prefix else k
        result.update(flatten_header(v, _prefix))
    return result


def flatten(queryset, serializer):
    """序列化 queryset 并展平为 (rows, headers)，供 CSV 写入使用。"""
    serialized = serializer(queryset, many=True)
    headers = flatten_header(serialized)
    data = traverse(serialized.data, serialized)
    return data, headers


# 安全白名单：防止 importlib 被用于任意模块注入
ALLOWED_MODELS = {
    'sea_saw_crm': ['Company', 'Contact', 'Supplier'],
    'sea_saw_sales': ['Order'],
    'sea_saw_pipeline': ['Pipeline'],
    'sea_saw_finance': ['Payment'],
    'sea_saw_production': ['ProductionOrder'],
    'sea_saw_procurement': ['PurchaseOrder'],
    'sea_saw_warehouse': ['OutboundOrder'],
    'sea_saw_auth': ['User', 'Role'],
    'sea_saw_download': ['DownloadTask'],
}

ALLOWED_SERIALIZERS = {
    'sea_saw_crm': ['CompanySerializer', 'ContactSerializer', 'SupplierSerializer'],
    'sea_saw_sales': ['OrderSerializerForOrderView'],
    'sea_saw_pipeline': ['PipelineSerializer'],
    'sea_saw_finance': ['PaymentSerializer'],
    'sea_saw_production': ['ProductionOrderSerializer'],
    'sea_saw_procurement': ['PurchaseOrderSerializer'],
    'sea_saw_warehouse': ['OutboundOrderSerializer'],
    'sea_saw_auth': ['UserSerializer', 'RoleSerializer'],
    'sea_saw_download': ['DownloadTaskSerializer'],
}


def _whitelist_check(name, allowed_map, kind):
    """校验 app_name 和 class_name 是否在白名单中，不通过则抛出 ValueError。"""
    app_name, class_name = name.split(".", 1)
    if app_name not in allowed_map:
        raise ValueError(
            f"Security Error: App '{app_name}' is not allowed for {kind}. "
            f"Allowed: {list(allowed_map.keys())}"
        )
    if class_name not in allowed_map[app_name]:
        raise ValueError(
            f"Security Error: {kind} '{class_name}' is not allowed for app '{app_name}'. "
            f"Allowed: {allowed_map[app_name]}"
        )
    return app_name, class_name


def dynamic_import_model(app_name, model_name):
    """安全地动态导入模型类（白名单校验）。"""
    _whitelist_check(f"{app_name}.{model_name}", ALLOWED_MODELS, "model")
    try:
        module = importlib.import_module(f"{app_name}.models")
        return getattr(module, model_name)
    except ImportError as e:
        raise ImportError(f"Failed to import model {model_name} from {app_name}: {e}")
    except AttributeError:
        raise AttributeError(f"Model {model_name} not found in {app_name}.models")


def dynamic_import_serializer(app_name, serializer_name):
    """安全地动态导入序列化器类（白名单校验）。"""
    _whitelist_check(f"{app_name}.{serializer_name}", ALLOWED_SERIALIZERS, "serializer")
    try:
        module = importlib.import_module(f"{app_name}.serializers")
        return getattr(module, serializer_name)
    except ImportError as e:
        raise ImportError(f"Failed to import serializer {serializer_name} from {app_name}: {e}")
    except AttributeError:
        raise AttributeError(f"Serializer {serializer_name} not found in {app_name}.serializers")
