"""核心模块"""

from .report_sections_model import (
    SECTION_TYPES,
    ALL_SECTION_TYPES,
    get_section_type_info,
    get_all_section_types,
    is_valid_section_type,
)

__all__ = [
    "SECTION_TYPES",
    "ALL_SECTION_TYPES",
    "get_section_type_info",
    "get_all_section_types",
    "is_valid_section_type",
]
