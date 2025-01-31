import csv
from typing import IO

from celery import shared_task
from django.conf import settings

from sea_saw_crm.utilis import flatten


@shared_task
def generate_csv_task(queryset, serializer, file_name):
    """
    生成筛选后的 CSV 文件并返回文件路径
    """
    file_path = f"{settings.MEDIA_ROOT}/downloads/{file_name}.csv"

    # 获取扁平化后的数据和字段头部
    data, headers = flatten(queryset, serializer)

    # 使用 'w' 模式以文本模式打开文件，确保文件是支持写入字符串的
    with open(file_path, "w", newline='', encoding='utf-8') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=headers)

        # 写入头部字段
        writer.writeheader()

        # 写入数据行
        writer.writerows(data)

    return file_path