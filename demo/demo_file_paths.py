#!/usr/bin/env python
"""
演示文件上传路径生成
运行: python demo_file_paths.py
"""
import os
import uuid
from datetime import datetime


def get_upload_path(instance, filename, subfolder="files"):
    """生成唯一的上传路径"""
    ext = os.path.splitext(filename)[1].lower()
    original_name = os.path.splitext(filename)[0]
    unique_filename = f"{uuid.uuid4().hex[:12]}_{original_name}{ext}"
    now = datetime.now()
    date_path = now.strftime("%Y/%m/%d")
    return os.path.join(subfolder, date_path, unique_filename)


def payment_attachment_path(instance, filename):
    """支付附件路径"""
    return get_upload_path(instance, filename, subfolder="payment_attachments")


def production_file_path(instance, filename):
    """生产文件路径"""
    return get_upload_path(instance, filename, subfolder="production_files")


if __name__ == "__main__":
    print("=" * 80)
    print("文件上传路径生成演示")
    print("=" * 80)
    print()

    # 测试同名文件
    print("【测试 1】同名文件不会冲突")
    print("-" * 80)
    filename = "invoice.pdf"
    print(f"原始文件名: {filename}")
    print()
    for i in range(3):
        path = payment_attachment_path(None, filename)
        print(f"第 {i+1} 次上传: {path}")
    print()

    # 测试不同类型的文件
    print("【测试 2】不同文件类型")
    print("-" * 80)
    files = [
        ("bank_slip.jpg", payment_attachment_path, "支付水单"),
        ("production_plan.xlsx", production_file_path, "生产计划"),
        ("contract.pdf", payment_attachment_path, "合同文件"),
        ("material_list.docx", production_file_path, "物料清单"),
    ]

    for fname, func, desc in files:
        path = func(None, fname)
        print(f"{desc:12} | {fname:25} → {path}")
    print()

    # 测试特殊字符
    print("【测试 3】特殊字符处理")
    print("-" * 80)
    special_files = [
        ("file with spaces.pdf", "带空格的文件名"),
        ("文件名-中文.jpg", "中文文件名"),
        ("file_with_underscores.xlsx", "带下划线"),
    ]

    for fname, desc in special_files:
        path = get_upload_path(None, fname, "test")
        print(f"{desc:12} | {fname:30} → {path}")
    print()

    # 路径结构说明
    print("【路径结构说明】")
    print("-" * 80)
    example_path = "payment_attachments/2024/01/15/a3b5c7d9e1f2_invoice.pdf"
    print(f"示例路径: {example_path}")
    print()
    print("结构分解:")
    print("  └─ payment_attachments/  ← 文件类型（按业务分类）")
    print("      └─ 2024/             ← 年份")
    print("          └─ 01/           ← 月份")
    print("              └─ 15/       ← 日期")
    print("                  └─ a3b5c7d9e1f2_invoice.pdf")
    print("                     ↑           ↑")
    print("                     |           └─ 原始文件名")
    print("                     └─ UUID 前缀（确保唯一）")
    print()

    # 优势总结
    print("【优势总结】")
    print("-" * 80)
    print("✅ 避免同名文件覆盖 - 每个文件都有唯一的 UUID 前缀")
    print("✅ 便于文件管理 - 按日期组织，易于查找和归档")
    print("✅ 保留原始文件名 - 用户友好，知道文件内容")
    print("✅ 性能优化 - 避免单个文件夹文件过多")
    print("✅ 可追溯性 - 从路径就能知道上传时间")
    print()
    print("=" * 80)
