"""
Legacy base.py - Re-exports from base/ folder for backward compatibility
"""
from .base import BaseModel, Field, FieldType, BaseAttachment

__all__ = ["BaseModel", "Field", "FieldType", "BaseAttachment"]
