#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
file_structure_extractor.py
ファイルの構造（クラス、関数、キーなど）を抽出するモジュール
"""

import re
import json
from pathlib import Path
from typing import Optional


def extract_python_structure(file_path: Path) -> str:
    """
    Pythonファイルからクラス・関数の構造を抽出

    Returns:
        構造を表す文字列（行番号付き）
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except Exception:
        return ""

    structures = []
    # クラス定義: class ClassName または class ClassName(Base)
    class_pattern = re.compile(r'^class\s+(\w+)')
    # 関数定義: def func または async def func
    func_pattern = re.compile(r'^(\s*)(async\s+)?def\s+(\w+)')

    current_class = None
    current_class_indent = 0

    for i, line in enumerate(lines, 1):
        # クラス定義
        class_match = class_pattern.match(line)
        if class_match:
            class_name = class_match.group(1)
            current_class = class_name
            current_class_indent = 0
            structures.append(f"  L{i}: class {class_name}")
            continue

        # 関数定義
        func_match = func_pattern.match(line)
        if func_match:
            indent = len(func_match.group(1))
            is_async = func_match.group(2) is not None
            func_name = func_match.group(3)
            prefix = "async def" if is_async else "def"

            # インデントがあればメソッド、なければトップレベル関数
            if indent > 0 and current_class:
                structures.append(f"  L{i}:   {prefix} {func_name}")
            else:
                current_class = None
                structures.append(f"  L{i}: {prefix} {func_name}")

    if not structures:
        return ""

    return "\n".join(structures)


def extract_json_structure(file_path: Path, max_depth: int = 2) -> str:
    """
    JSON/JSON5ファイルからキー構造を抽出

    Args:
        file_path: ファイルパス
        max_depth: 表示する最大深さ

    Returns:
        構造を表す文字列
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # JSON5のコメントを除去（簡易的）
        # 行コメント
        content = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
        # ブロックコメント
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        # 末尾カンマを除去（JSON5対応）
        content = re.sub(r',(\s*[}\]])', r'\1', content)

        data = json.loads(content)
    except Exception:
        return ""

    def format_structure(obj, depth: int = 0, prefix: str = "") -> list[str]:
        """再帰的に構造を抽出"""
        results = []
        indent = "  " * depth

        if isinstance(obj, dict):
            for key in obj:
                value = obj[key]
                if isinstance(value, dict):
                    if depth < max_depth:
                        results.append(f"{indent}{prefix}{key}: {{...}}")
                        results.extend(format_structure(value, depth + 1, ""))
                    else:
                        results.append(f"{indent}{prefix}{key}: {{...}}")
                elif isinstance(value, list):
                    if value and isinstance(value[0], dict) and depth < max_depth:
                        results.append(f"{indent}{prefix}{key}: [{{...}}] ({len(value)} items)")
                    else:
                        results.append(f"{indent}{prefix}{key}: [...] ({len(value)} items)")
                else:
                    type_name = type(value).__name__
                    results.append(f"{indent}{prefix}{key}: <{type_name}>")
        elif isinstance(obj, list) and obj:
            if isinstance(obj[0], dict):
                results.append(f"{indent}[0]: {{...}}")
                if depth < max_depth:
                    results.extend(format_structure(obj[0], depth + 1, ""))

        return results

    structures = format_structure(data)
    if not structures:
        return ""

    return "\n".join(["  " + s for s in structures])


def extract_file_structure(file_path: Path) -> Optional[str]:
    """
    ファイル拡張子に基づいて適切な構造抽出を行う

    Args:
        file_path: 対象ファイルのパス

    Returns:
        構造を表す文字列、対応していない場合はNone
    """
    suffix = file_path.suffix.lower()

    if suffix == '.py':
        return extract_python_structure(file_path)
    elif suffix in {'.json', '.json5'}:
        return extract_json_structure(file_path)

    return None


def get_supported_extensions() -> set[str]:
    """サポートしている拡張子のセットを返す"""
    return {'.py', '.json', '.json5'}
