#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ups_file_path_suggest.py
UserPromptSubmitでユーザーが言及したファイルパスをファジー検索してサジェスト
"""

import sys
import os
import re
from pathlib import Path
from typing import List, Tuple, Dict, Optional

# rapidfuzzの導入
from rapidfuzz import fuzz, process

# hook_utils をインポート
try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from hook_utils import debug_log, get_project_root, get_path_from_config, load_json5

except ImportError as e:
    error_msg = f"Failed to import hook_utils: {e}"
    print(f"[HOOK ERROR] {error_msg}")
    print(f"[HOOK ERROR] Script: {__file__}")
    print(f"[HOOK ERROR] sys.path: {sys.path}")
    sys.stderr.write(f"[HOOK ERROR] {error_msg}\n")
    sys.stderr.write(f"[HOOK ERROR] Script: {__file__}\n")
    sys.exit(1)

def load_config() -> dict:
    """scripts_options.json5から設定を読み込み"""
    # デフォルト設定
    default = {
        "enabled": True,
        "exclude_exact": ["settings.json", "CLAUDE.md", "README.md"],
        "exclude_patterns": ["^\\."],
        "search": {
            "max_suggestions": 3,
            "min_similarity": 0.6,
            "search_scope": "smart",
            "respect_gitignore": True,
            "max_search_depth": 5
        },
        "with_directory": {
            "enabled": True,
            "fuzzy_directory": True
        },
        "heuristics": {
            "extension_hints": {},
            "filename_patterns": {},
            "keyword_hints": {}
        }
    }

    try:
        config_path = get_path_from_config("file_path_suggest_config")
        all_config = load_json5(config_path)
        return all_config.get("ups_file_path_suggest", default)
    except Exception as e:
        debug_log(f"Failed to load config: {e}, using default")
        return default


def extract_mentioned_files(user_message: str) -> List[Dict]:
    """
    ユーザーメッセージからファイル言及を抽出

    Returns:
        [
            {
                "mentioned": "cope_template_cli.py",
                "has_directory": False,
                "context": "cope_template_cli.py を見て"
            },
            ...
        ]
    """
    results = []

    # パターン1: パス区切り文字を含む（ディレクトリ構造あり）
    # 例: "foo/bar.py", ".\scripts\test.py", "template/obsidian_template/file.md"
    pattern_with_dir = r'([a-zA-Z0-9_\-\.\/\\]+[\/\\][a-zA-Z0-9_\-\.\/\\]+)'

    # パターン2: 拡張子付きファイル名のみ
    # 例: "foo.py", "bar.json", "baz.md"
    pattern_filename = r'\b([a-zA-Z0-9_\-]+\.[a-zA-Z0-9]+)\b'

    # パターン1を先にチェック（ディレクトリ構造を含む）
    for match in re.finditer(pattern_with_dir, user_message):
        filepath = match.group(1)
        # Windowsパスの正規化
        filepath = filepath.replace('\\', '/')
        results.append({
            "mentioned": filepath,
            "has_directory": True,
            "context": user_message[max(0, match.start()-20):match.end()+20]
        })

    # パターン2: ファイル名のみ（パターン1で拾われなかったもの）
    already_found = {r["mentioned"] for r in results}
    for match in re.finditer(pattern_filename, user_message):
        filepath = match.group(1)
        if filepath not in already_found and not any(filepath in found for found in already_found):
            results.append({
                "mentioned": filepath,
                "has_directory": False,
                "context": user_message[max(0, match.start()-20):match.end()+20]
            })

    return results


def should_skip_file(filename: str, config: dict) -> bool:
    """除外対象かチェック"""
    # 完全一致チェック
    if filename in config.get("exclude_exact", []):
        return True

    # パターンマッチ
    for pattern in config.get("exclude_patterns", []):
        try:
            if re.match(pattern, filename):
                return True
        except re.error:
            continue

    return False


def calculate_similarity(target: str, candidate: str) -> float:
    """類似度計算（rapidfuzz使用）"""
    target_lower = target.lower()
    candidate_lower = candidate.lower()

    # 完全一致（大小文字のみ違い）
    if candidate_lower == target_lower:
        return 1.0

    # rapidfuzz使用（100点満点 → 0-1スケールに正規化）
    base_score = fuzz.WRatio(target_lower, candidate_lower) / 100.0

    # ボーナス（0-1スケールで調整）
    if len(target_lower) >= 3 and candidate_lower.startswith(target_lower[:3]):
        base_score += 0.05  # 前方一致

    if target_lower in candidate_lower:
        base_score += 0.10  # 部分一致

    # 拡張子が一致
    if Path(target).suffix == Path(candidate).suffix:
        base_score += 0.03

    return min(base_score, 1.0)


def fuzzy_search_in_directory(
    directory: Path,
    target_filename: str,
    recursive: bool = True,
    max_depth: Optional[int] = None,
    respect_gitignore: bool = True
) -> List[Tuple[Path, float]]:
    """ディレクトリ内でファジー検索（rapidfuzz使用で高速化）"""

    if not directory.exists():
        return []

    # ステップ1: 全ファイルパスを収集
    file_paths = []
    file_names = []

    if not recursive:
        # 直下のみ
        try:
            for item in directory.iterdir():
                if item.is_file():
                    file_paths.append(item)
                    file_names.append(item.name)
        except PermissionError:
            pass
    else:
        # 再帰的検索
        try:
            for root, dirs, files in os.walk(directory):
                # 深さ制限
                if max_depth:
                    try:
                        depth = len(Path(root).relative_to(directory).parts)
                        if depth > max_depth:
                            continue
                    except ValueError:
                        continue

                # .gitignore考慮
                if respect_gitignore:
                    dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', 'venv', '.venv']]

                for file in files:
                    file_path = Path(root) / file
                    file_paths.append(file_path)
                    file_names.append(file)
        except PermissionError:
            pass

    if not file_names:
        return []

    # ステップ2: rapidfuzzで一括スコアリング（超高速）
    candidates = []

    # process.extract()で一括スコアリング
    matches = process.extract(
        target_filename.lower(),
        file_names,
        scorer=fuzz.WRatio,
        score_cutoff=50.0,  # 50点未満は無視（0-100スケール）
        limit=None  # 全候補を取得
    )

    # 結果をフォーマット & ボーナス適用
    for match_text, score, index in matches:
        file_path = file_paths[index]

        # ボーナス適用（100点満点で計算）
        adjusted_score = score
        target_lower = target_filename.lower()
        candidate_lower = match_text.lower()

        if len(target_lower) >= 3 and candidate_lower.startswith(target_lower[:3]):
            adjusted_score += 5  # 前方一致
        if target_lower in candidate_lower:
            adjusted_score += 10  # 部分一致
        if Path(target_filename).suffix == Path(match_text).suffix:
            adjusted_score += 3  # 拡張子一致

        adjusted_score = min(adjusted_score, 100.0)

        # 0-1スケールに正規化
        normalized_score = adjusted_score / 100.0

        candidates.append((file_path, normalized_score))

    return sorted(candidates, key=lambda x: x[1], reverse=True)


def smart_search_filename_only(
    filename: str,
    project_root: Path,
    config: dict
) -> List[Tuple[Path, float, str]]:
    """
    ファイル名のみの場合の賢い検索（キャッシュ機能付き）

    Returns:
        [(path, similarity_score, search_method), ...]
    """
    results = []
    heuristics = config.get("heuristics", {})
    min_similarity = config.get("search", {}).get("min_similarity", 0.6)
    max_depth = config.get("search", {}).get("max_search_depth", 5)
    respect_gitignore = config.get("search", {}).get("respect_gitignore", True)

    # 検索済みディレクトリのキャッシュ（重複検索を防ぐ）
    searched_dirs = {}  # {dir_path: [(path, score), ...]}

    def get_or_search(search_dir: Path, method_name: str) -> List[Tuple[Path, float, str]]:
        """キャッシュを使って検索（重複検索を防ぐ）"""
        dir_key = str(search_dir.resolve())

        if dir_key in searched_dirs:
            # キャッシュヒット - 計算済みの結果を再利用
            debug_log(f"Cache hit for {search_dir}")
            return [(path, score, method_name) for path, score in searched_dirs[dir_key]]

        # キャッシュミス - 実際に検索
        if not search_dir.exists():
            return []

        # 完全一致チェック
        exact_match = search_dir / filename
        if exact_match.exists():
            searched_dirs[dir_key] = [(exact_match, 1.0)]
            return [(exact_match, 1.0, "exact")]

        # ファジー検索
        fuzzy_results = fuzzy_search_in_directory(
            search_dir, filename, recursive=True,
            max_depth=max_depth, respect_gitignore=respect_gitignore
        )

        # キャッシュに保存（method抜きで）
        searched_dirs[dir_key] = fuzzy_results

        # min_similarity以上の結果のみ返す
        return [(path, score, method_name) for path, score in fuzzy_results if score >= min_similarity]

    # Step 1: 拡張子ヒント
    ext = Path(filename).suffix
    if ext and ext in heuristics.get("extension_hints", {}):
        priority_dirs = heuristics["extension_hints"][ext]
        debug_log(f"[smart_search] Step 1: Extension hint for '{ext}' -> dirs: {priority_dirs}")

        for dir_hint in priority_dirs:
            search_dir = project_root / dir_hint
            debug_log(f"[smart_search] Searching in: {search_dir}")
            search_results = get_or_search(search_dir, "extension_hint")
            results.extend(search_results)
            debug_log(f"[smart_search] Found {len(search_results)} result(s)")

            # 完全一致が見つかったら即return
            if search_results and any(score == 1.0 for _, score, _ in search_results):
                debug_log(f"[smart_search] Exact match found, returning early")
                return results
    else:
        debug_log(f"[smart_search] Step 1: No extension hints for '{ext}'")

    # Step 2: ファイル名パターンマッチ
    filename_patterns = heuristics.get("filename_patterns", {})
    matched_patterns = []
    for pattern, priority_dirs in filename_patterns.items():
        try:
            if re.match(pattern, filename):
                matched_patterns.append(pattern)
                debug_log(f"[smart_search] Step 2: Pattern '{pattern}' matched -> dirs: {priority_dirs}")
                for dir_hint in priority_dirs:
                    search_dir = project_root / dir_hint
                    debug_log(f"[smart_search] Searching in: {search_dir}")
                    search_results = get_or_search(search_dir, "pattern_hint")
                    results.extend(search_results)
                    debug_log(f"[smart_search] Found {len(search_results)} result(s)")
        except re.error:
            continue
    if not matched_patterns:
        debug_log(f"[smart_search] Step 2: No filename patterns matched")

    # Step 3: キーワードヒント
    keyword_hints = heuristics.get("keyword_hints", {})
    matched_keywords = []
    for keyword, priority_dirs in keyword_hints.items():
        if keyword.lower() in filename.lower():
            matched_keywords.append(keyword)
            debug_log(f"[smart_search] Step 3: Keyword '{keyword}' matched -> dirs: {priority_dirs}")
            for dir_hint in priority_dirs:
                search_dir = project_root / dir_hint
                debug_log(f"[smart_search] Searching in: {search_dir}")
                search_results = get_or_search(search_dir, "keyword_hint")
                results.extend(search_results)
                debug_log(f"[smart_search] Found {len(search_results)} result(s)")
    if not matched_keywords:
        debug_log(f"[smart_search] Step 3: No keyword hints matched")

    # Step 4: 全体ファジー検索（他で見つからなかった場合のみ）
    if not results:
        debug_log(f"[smart_search] Step 4: Fallback to full fuzzy search in project root")
        search_results = get_or_search(project_root, "fuzzy")
        results.extend(search_results)
        debug_log(f"[smart_search] Found {len(search_results)} result(s)")
    else:
        debug_log(f"[smart_search] Step 4: Skipped (already have {len(results)} result(s))")

    # 重複排除 & スコアでソート
    unique_results = {}
    for path, score, method in results:
        path_str = str(path)
        if path_str not in unique_results or unique_results[path_str][1] < score:
            unique_results[path_str] = (path, score, method)

    sorted_results = sorted(
        unique_results.values(),
        key=lambda x: x[1],
        reverse=True
    )

    max_suggestions = config.get("search", {}).get("max_suggestions", 3)
    return sorted_results[:max_suggestions]


def search_continuation(base_dir: Path, remaining: Path, config: dict) -> List[Path]:
    """
    base_dir配下でremainingパスの続きを探す
    """
    candidates = []
    remaining_parts = remaining.parts

    # 完全一致優先
    full_path = base_dir / remaining
    if full_path.exists():
        candidates.append(full_path)
        return candidates

    # 部分的にファジーマッチ
    max_depth = config.get("search", {}).get("max_search_depth", 3)
    try:
        for root, dirs, files in os.walk(base_dir):
            root_path = Path(root)

            # 深さ制限
            try:
                depth = len(root_path.relative_to(base_dir).parts)
                if depth > max_depth:
                    continue
            except ValueError:
                continue

            # 各階層でファジーマッチ
            all_items = dirs + files
            for part in remaining_parts:
                for item in all_items:
                    if calculate_similarity(part, item) >= 0.7:
                        candidate = root_path / item
                        if candidate.exists():
                            candidates.append(candidate)
    except PermissionError:
        pass

    return candidates[:5]


def search_top_directory_globally(
    project_root: Path,
    top_dir_name: str,
    remaining: Optional[Path],
    config: dict
) -> List[Path]:
    """プロジェクト全体から top_dir_name を探し、remaining を繋げる"""
    candidates = []
    max_depth = config.get("search", {}).get("max_search_depth", 5)

    try:
        for root, dirs, files in os.walk(project_root):
            # 深さ制限
            try:
                depth = len(Path(root).relative_to(project_root).parts)
                if depth > max_depth:
                    continue
            except ValueError:
                continue

            # .git, __pycache__ などをスキップ
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', 'venv', '.venv']]

            # ファジーマッチでディレクトリを探す
            for dir_name in dirs:
                if calculate_similarity(top_dir_name, dir_name) >= 0.7:
                    found_base = Path(root) / dir_name

                    if remaining:
                        # 残りパスを繋げる
                        full_path = found_base / remaining
                        if full_path.exists():
                            candidates.append(full_path)
                        else:
                            # ファジーマッチで続きを探す
                            fuzzy_candidates = search_continuation(found_base, remaining, config)
                            candidates.extend(fuzzy_candidates)
                    else:
                        candidates.append(found_base)
    except PermissionError:
        pass

    return candidates[:5]


def resolve_partial_path(partial_path: str, project_root: Path, config: dict) -> List[Tuple[str, str]]:
    """
    部分パスを解決

    Returns:
        [(resolved_path, match_type), ...]
        match_type: "exact" | "directory_match" | "reconnected"
    """
    # Windowsパスを正規化
    partial_path = partial_path.replace('\\', '/')
    debug_log(f"[resolve_partial_path] Input: {partial_path}")

    # Step 1: そのまま存在確認
    test_path = project_root / partial_path
    debug_log(f"[resolve_partial_path] Step 1: Testing exact path: {test_path}")
    if test_path.exists():
        debug_log(f"[resolve_partial_path] Step 1: Exact match found!")
        return [(str(test_path.relative_to(project_root)), "exact")]
    debug_log(f"[resolve_partial_path] Step 1: Not found")

    # Step 2: どこまで辿れるかチェック
    parts = Path(partial_path).parts
    debug_log(f"[resolve_partial_path] Step 2: Checking path parts: {parts}")
    for i in range(len(parts), 0, -1):
        sub_path = Path(*parts[:i])
        test_path = project_root / sub_path
        debug_log(f"[resolve_partial_path] Step 2: Testing sub-path ({i}/{len(parts)}): {test_path}")

        if test_path.exists():
            # 途中まで一致 → そこから続きを探す
            matched_base = test_path
            remaining = Path(*parts[i:]) if i < len(parts) else None
            debug_log(f"[resolve_partial_path] Step 2: Partial match! Base: {matched_base}, Remaining: {remaining}")

            if remaining:
                debug_log(f"[resolve_partial_path] Step 2: Searching continuation from base...")
                candidates = search_continuation(matched_base, remaining, config)
                debug_log(f"[resolve_partial_path] Step 2: Found {len(candidates)} candidate(s)")
                results = []
                for c in candidates:
                    try:
                        rel_path = c.relative_to(project_root)
                        results.append((str(rel_path), "directory_match"))
                    except ValueError:
                        results.append((str(c), "directory_match"))
                return results
            else:
                try:
                    rel_path = matched_base.relative_to(project_root)
                    return [(str(rel_path), "directory_match")]
                except ValueError:
                    return [(str(matched_base), "directory_match")]

    debug_log(f"[resolve_partial_path] Step 2: No partial matches found")

    # Step 3: 最上位ディレクトリから逆引き
    top_dir = parts[0]
    remaining = Path(*parts[1:]) if len(parts) > 1 else None
    debug_log(f"[resolve_partial_path] Step 3: Global search for top dir '{top_dir}' + remaining '{remaining}'")

    reconnected = search_top_directory_globally(project_root, top_dir, remaining, config)
    debug_log(f"[resolve_partial_path] Step 3: Found {len(reconnected)} candidate(s)")

    results = []
    for c in reconnected:
        try:
            rel_path = c.relative_to(project_root)
            results.append((str(rel_path), "reconnected"))
        except ValueError:
            results.append((str(c), "reconnected"))

    return results


def format_smart_suggestions(suggestions_output: List[dict]) -> str:
    """サジェストメッセージのフォーマット"""
    lines = [
        "<system-reminder>",
        "File path suggestions based on user mentions:",
        ""
    ]

    for item in suggestions_output:
        mentioned = item["mentioned"]
        has_dir = item["has_directory"]
        results = item["results"]

        path_type = "partial path" if has_dir else "filename only"
        lines.append(f'"{mentioned}" ({path_type}):')

        for i, result in enumerate(results[:3], 1):
            if len(result) == 2:
                # (i) の結果: (path, match_type)
                path, match_type = result
                lines.append(f"  {i}. {path} (method: {match_type})")
            else:
                # (ii) の結果: (path, score, method)
                path, score, method = result
                lines.append(f"  {i}. {path} (similarity: {score:.2f}, method: {method})")

        lines.append("")

    lines.append("Please verify paths before using Read/Edit tools.")
    lines.append("</system-reminder>")

    return "\n".join(lines)


def main(hook_data: dict):
    """UserPromptSubmit エントリーポイント"""
    try:
        config = load_config()

        if not config.get("enabled", True):
            debug_log("[ups_file_path_suggest] Hook is disabled")
            return

        user_message = hook_data.get("prompt", "")
        if not user_message:
            debug_log("[ups_file_path_suggest] No user message found")
            return

        debug_log(f"[ups_file_path_suggest] Processing user message: {user_message[:100]}...")

        mentioned_files = extract_mentioned_files(user_message)
        if not mentioned_files:
            debug_log("[ups_file_path_suggest] No file mentions detected")
            return

        debug_log(f"[ups_file_path_suggest] Detected {len(mentioned_files)} file mention(s): {[m['mentioned'] for m in mentioned_files]}")

        project_root = get_project_root()
        debug_log(f"[ups_file_path_suggest] Project root: {project_root}")

        suggestions_output = []

        for item in mentioned_files:
            mentioned = item["mentioned"]
            has_directory = item["has_directory"]

            debug_log(f"[ups_file_path_suggest] Processing: '{mentioned}' (has_directory={has_directory})")

            # 除外チェック
            filename_only = Path(mentioned).name
            if should_skip_file(filename_only, config):
                debug_log(f"[ups_file_path_suggest] Skipping excluded file: {filename_only}")
                continue

            results = []

            if has_directory:
                # (i) 中途半端なディレクトリパス
                if not config.get("with_directory", {}).get("enabled", True):
                    debug_log(f"[ups_file_path_suggest] Directory path search is disabled")
                    continue

                debug_log(f"[ups_file_path_suggest] Resolving partial path: {mentioned}")
                results = resolve_partial_path(mentioned, project_root, config)
                debug_log(f"[ups_file_path_suggest] Partial path resolution found {len(results)} result(s)")

            else:
                # (ii) ファイル名のみ
                debug_log(f"[ups_file_path_suggest] Smart search for filename: {mentioned}")
                results = smart_search_filename_only(
                    mentioned,
                    project_root,
                    config
                )
                debug_log(f"[ups_file_path_suggest] Smart search found {len(results)} result(s)")

            if results:
                # 結果の詳細をログ
                for i, result in enumerate(results[:3], 1):
                    if len(result) == 2:
                        path, match_type = result
                        debug_log(f"[ups_file_path_suggest]   {i}. {path} (method: {match_type})")
                    else:
                        path, score, method = result
                        debug_log(f"[ups_file_path_suggest]   {i}. {path} (score: {score:.2f}, method: {method})")

                suggestions_output.append({
                    "mentioned": mentioned,
                    "has_directory": has_directory,
                    "results": results
                })
            else:
                debug_log(f"[ups_file_path_suggest] No results found for: {mentioned}")

        if suggestions_output:
            debug_log(f"[ups_file_path_suggest] Outputting suggestions for {len(suggestions_output)} file(s)")
            message = format_smart_suggestions(suggestions_output)
            print(message)
        else:
            debug_log("[ups_file_path_suggest] No suggestions to output")

    except Exception as e:
        debug_log(f"[ups_file_path_suggest] Error: {e}")
        import traceback
        debug_log(f"[ups_file_path_suggest] Traceback:\n{traceback.format_exc()}")


if __name__ == "__main__":
    import json

    # stdinからデータを読み取り
    try:
        input_data = sys.stdin.read()
        if input_data.strip():
            hook_data = json.loads(input_data)
        else:
            hook_data = {}
    except json.JSONDecodeError:
        hook_data = {}
    except Exception:
        hook_data = {}

    main(hook_data)
