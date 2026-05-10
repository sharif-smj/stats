import asyncio
import html
import json
import math
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple


LANGUAGE_COLORS = {
    "Dart": "#00B4AB",
    "Go": "#00ADD8",
    "Java": "#b07219",
    "JavaScript": "#f1e05a",
    "Kotlin": "#A97BFF",
    "Python": "#3572A5",
    "Rust": "#dea584",
    "Shell": "#89e051",
    "Swift": "#F05138",
    "TypeScript": "#3178c6",
    "Other": "#444444",
}

EXTENSION_LANGUAGES = {
    ".c": "C",
    ".cc": "C++",
    ".cpp": "C++",
    ".cs": "C#",
    ".dart": "Dart",
    ".go": "Go",
    ".java": "Java",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".m": "Objective-C",
    ".mm": "Objective-C++",
    ".php": "PHP",
    ".py": "Python",
    ".rb": "Ruby",
    ".rs": "Rust",
    ".sh": "Shell",
    ".swift": "Swift",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
}

EXCLUDED_EXTENSIONS = {
    ".css",
    ".csv",
    ".gif",
    ".html",
    ".jpeg",
    ".jpg",
    ".jsonl",
    ".lock",
    ".md",
    ".mdx",
    ".png",
    ".svg",
    ".toml",
    ".txt",
    ".webp",
    ".xml",
    ".yaml",
    ".yml",
}

EXCLUDED_FILENAMES = {
    "cargo.lock",
    "package-lock.json",
    "pnpm-lock.yaml",
    "poetry.lock",
    "pubspec.lock",
    "yarn.lock",
}

EXCLUDED_DIR_PARTS = {
    ".git",
    ".github",
    ".next",
    "assets",
    "build",
    "coverage",
    "dist",
    "docs",
    "generated",
    "node_modules",
    "out",
    "public",
    "target",
    "vendor",
}


@dataclass
class LanguageChange:
    name: str
    color: str
    changes: int


@dataclass
class RecentCodeLanguageResult:
    languages: Dict[str, LanguageChange]
    excluded_changes: int


def changed_lines(file_obj: Dict[str, Any]) -> int:
    return int(file_obj.get("additions", 0) or 0) + int(
        file_obj.get("deletions", 0) or 0
    )


def language_for_path(path: str) -> Optional[str]:
    normalized = path.replace("\\", "/")
    parts = [part.lower() for part in normalized.split("/")[:-1]]
    basename = os.path.basename(normalized).lower()
    _, ext = os.path.splitext(basename)

    if basename in EXCLUDED_FILENAMES:
        return None
    if any(part in EXCLUDED_DIR_PARTS for part in parts):
        return None
    if basename.endswith(".min.js") or basename.endswith(".min.css"):
        return None
    if ext in EXCLUDED_EXTENSIONS:
        return None

    return EXTENSION_LANGUAGES.get(ext)


def aggregate_recent_code_language_files(
    files: Iterable[Dict[str, Any]]
) -> RecentCodeLanguageResult:
    languages: Dict[str, LanguageChange] = {}
    excluded_changes = 0

    for file_obj in files:
        path = str(file_obj.get("filename", ""))
        changes = changed_lines(file_obj)
        language = language_for_path(path)

        if language is None:
            excluded_changes += changes
            continue

        if language not in languages:
            languages[language] = LanguageChange(
                name=language,
                color=LANGUAGE_COLORS.get(language, LANGUAGE_COLORS["Other"]),
                changes=0,
            )
        languages[language].changes += changes

    return RecentCodeLanguageResult(languages=languages, excluded_changes=excluded_changes)


def build_recent_code_language_payload(
    result: RecentCodeLanguageResult,
    generated_at: Optional[str] = None,
    window_days: int = 365,
) -> Dict[str, Any]:
    sorted_languages = sorted(
        result.languages.values(), key=lambda language: language.changes, reverse=True
    )

    return {
        "generated_at": generated_at
        or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "window_days": window_days,
        "metric": "changed_lines",
        "languages": [
            {
                "name": language.name,
                "color": language.color,
                "changes": language.changes,
            }
            for language in sorted_languages
        ],
        "excluded_changes": result.excluded_changes,
    }


def donut_languages(payload: Dict[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
    languages = [
        language
        for language in payload.get("languages", [])
        if int(language.get("changes", 0) or 0) > 0
    ]
    visible = languages[:limit]
    rest = languages[limit:]
    rest_changes = sum(int(language.get("changes", 0) or 0) for language in rest)
    if rest_changes > 0:
        visible.append(
            {"name": "Other", "color": LANGUAGE_COLORS["Other"], "changes": rest_changes}
        )
    return visible


def render_donut_group(payload: Dict[str, Any]) -> str:
    languages = donut_languages(payload)
    if not languages:
        return ""

    total = sum(int(language.get("changes", 0) or 0) for language in languages)
    radius_outer = 117
    radius_inner = 65
    center_x = 130
    center_y = 130

    def point(radius: float, angle: float) -> Tuple[float, float]:
        return (math.cos(angle) * radius, math.sin(angle) * radius)

    parts = ['<g transform="translate(40, 520)">']
    parts.append('<g transform="translate(273, 0)">')
    row_height = 32.5
    y_start = 48.75
    for index, language in enumerate(languages):
        name = html.escape(str(language.get("name", "")))
        color = html.escape(str(language.get("color", LANGUAGE_COLORS["Other"])))
        y = y_start + index * row_height
        parts.append(
            f'<rect x="0" y="{y - 10.8333:.4f}" width="21.6667" height="21.6667" '
            f'fill="{color}" class="stroke-bg" stroke-width="1px"></rect>'
        )
        parts.append(
            f'<text dominant-baseline="middle" x="26" y="{y:.4f}" '
            f'class="fill-fg" font-size="21.6667px">{name}</text>'
        )
    parts.append("</g>")

    parts.append(f'<g transform="translate({center_x}, {center_y})">')
    start_angle = -math.pi / 2
    for language in languages:
        changes = int(language.get("changes", 0) or 0)
        end_angle = start_angle + (2 * math.pi * changes / total)
        large_arc = 1 if end_angle - start_angle > math.pi else 0
        outer_start = point(radius_outer, start_angle)
        outer_end = point(radius_outer, end_angle)
        inner_end = point(radius_inner, end_angle)
        inner_start = point(radius_inner, start_angle)
        color = html.escape(str(language.get("color", LANGUAGE_COLORS["Other"])))
        name = html.escape(str(language.get("name", "")))
        path = (
            f"M{outer_start[0]:.3f},{outer_start[1]:.3f}"
            f"A{radius_outer},{radius_outer},0,{large_arc},1,{outer_end[0]:.3f},{outer_end[1]:.3f}"
            f"L{inner_end[0]:.3f},{inner_end[1]:.3f}"
            f"A{radius_inner},{radius_inner},0,{large_arc},0,{inner_start[0]:.3f},{inner_start[1]:.3f}Z"
        )
        parts.append(
            f'<path d="{path}" style="fill: {color};" class="stroke-bg" '
            f'stroke-width="2px"><title>{name} {changes}</title></path>'
        )
        start_angle = end_angle
    parts.append("</g>")
    parts.append("</g>")
    return "".join(parts)


def render_recent_code_language_svg(payload: Dict[str, Any]) -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="520" height="260" '
        'viewBox="0 0 520 260">'
        '<style>* { font-family: "Ubuntu", "Helvetica", "Arial", sans-serif; }'
        '.fill-bg { fill: #0d1117; }.fill-fg { fill: #c9d1d9; }'
        '.stroke-bg { stroke: #0d1117; }</style>'
        '<rect x="0" y="0" width="520" height="260" class="fill-bg"></rect>'
        f"{render_donut_group(payload)}"
        "</svg>"
    )


async def collect_recent_code_language_payload(
    stats: Any, window_days: int = 365
) -> Dict[str, Any]:
    since = datetime.now(timezone.utc) - timedelta(days=window_days)
    since_iso = since.strftime("%Y-%m-%dT%H:%M:%SZ")

    async def fetch_commit_files(repo: str, sha: str) -> List[Dict[str, Any]]:
        detail = await stats.queries.query_rest(f"/repos/{repo}/commits/{sha}")
        if not isinstance(detail, dict):
            return []
        files = detail.get("files", [])
        return files if isinstance(files, list) else []

    async def fetch_repo_files(repo: str) -> List[Dict[str, Any]]:
        repo_files: List[Dict[str, Any]] = []
        page = 1

        while True:
            commits = await stats.queries.query_rest(
                f"/repos/{repo}/commits",
                {
                    "author": stats.username,
                    "since": since_iso,
                    "per_page": 100,
                    "page": page,
                },
            )
            if not isinstance(commits, list) or not commits:
                break

            commit_files = await asyncio.gather(
                *[
                    fetch_commit_files(repo, commit.get("sha"))
                    for commit in commits
                    if commit.get("sha")
                ]
            )
            for files in commit_files:
                repo_files.extend(files)

            if len(commits) < 100:
                break
            page += 1

        return repo_files

    repo_files = await asyncio.gather(
        *[fetch_repo_files(repo) for repo in sorted(await stats.repos)]
    )
    files: List[Dict[str, Any]] = [
        file_obj for files_for_repo in repo_files for file_obj in files_for_repo
    ]

    return build_recent_code_language_payload(
        aggregate_recent_code_language_files(files),
        window_days=window_days,
    )


def write_recent_code_language_outputs(payload: Dict[str, Any]) -> None:
    os.makedirs("generated", exist_ok=True)
    with open("generated/recent-code-languages.json", "w") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")
    with open("generated/recent-code-languages.svg", "w") as f:
        f.write(render_recent_code_language_svg(payload))
