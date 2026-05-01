import re
from dataclasses import dataclass, field
from typing import Optional
import mimetypes
import os

LANGUAGE_MAP = {
    ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript", ".tsx": "TypeScript",
    ".jsx": "JavaScript", ".java": "Java", ".go": "Go", ".rs": "Rust", ".rb": "Ruby",
    ".php": "PHP", ".cs": "C#", ".cpp": "C++", ".c": "C", ".h": "C/C++ Header",
    ".swift": "Swift", ".kt": "Kotlin", ".scala": "Scala", ".sh": "Shell",
    ".sql": "SQL", ".html": "HTML", ".css": "CSS", ".scss": "SCSS",
    ".yaml": "YAML", ".yml": "YAML", ".json": "JSON", ".md": "Markdown",
    ".tf": "Terraform", ".dockerfile": "Dockerfile",
}

MAX_CHUNK_LINES = 50


@dataclass
class DiffChunk:
    filename: str
    language: str
    start_line: int
    end_line: int
    content: str
    change_type: str  # added, modified, deleted
    added_lines: int = 0
    removed_lines: int = 0


@dataclass
class FileDiff:
    filename: str
    old_filename: Optional[str]
    language: str
    change_type: str
    chunks: list[DiffChunk] = field(default_factory=list)


def detect_language(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext in LANGUAGE_MAP:
        return LANGUAGE_MAP[ext]
    if os.path.basename(filename).lower() == "dockerfile":
        return "Dockerfile"
    return "Unknown"


def parse_diff(raw_diff: str) -> list[FileDiff]:
    file_diffs = []
    # Split on "diff --git" boundaries
    file_sections = re.split(r"(?=^diff --git )", raw_diff, flags=re.MULTILINE)

    for section in file_sections:
        if not section.strip() or not section.startswith("diff --git"):
            continue
        file_diff = _parse_file_section(section)
        if file_diff:
            file_diffs.append(file_diff)

    return file_diffs


def _parse_file_section(section: str) -> Optional[FileDiff]:
    lines = section.splitlines()
    if not lines:
        return None

    # Extract filenames from diff header
    header_match = re.match(r"diff --git a/(.+) b/(.+)", lines[0])
    if not header_match:
        return None

    old_path = header_match.group(1)
    new_path = header_match.group(2)

    change_type = "modified"
    filename = new_path

    for line in lines[1:6]:
        if line.startswith("new file"):
            change_type = "added"
        elif line.startswith("deleted file"):
            change_type = "deleted"
            filename = old_path
        elif line.startswith("+++ b/"):
            filename = line[6:]
        elif line.startswith("--- /dev/null"):
            change_type = "added"

    language = detect_language(filename)
    file_diff = FileDiff(
        filename=filename,
        old_filename=old_path if old_path != new_path else None,
        language=language,
        change_type=change_type,
    )

    # Parse hunks
    hunk_pattern = re.compile(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
    current_hunk_lines: list[str] = []
    current_start_line = 0
    current_new_line = 0

    for line in lines:
        hunk_match = hunk_pattern.match(line)
        if hunk_match:
            if current_hunk_lines:
                _flush_chunks(file_diff, current_hunk_lines, current_start_line, language, change_type)
            current_start_line = int(hunk_match.group(2))
            current_new_line = current_start_line
            current_hunk_lines = [line]
        elif current_hunk_lines is not None and (line.startswith("+") or line.startswith("-") or line.startswith(" ")):
            current_hunk_lines.append(line)

    if current_hunk_lines:
        _flush_chunks(file_diff, current_hunk_lines, current_start_line, language, change_type)

    return file_diff


def _flush_chunks(file_diff: FileDiff, hunk_lines: list[str], start_line: int, language: str, change_type: str):
    # Split hunk into max MAX_CHUNK_LINES chunks for manageable review
    chunks = _split_into_chunks(hunk_lines, start_line, MAX_CHUNK_LINES)
    for chunk_lines, chunk_start in chunks:
        content = "\n".join(chunk_lines)
        added = sum(1 for l in chunk_lines if l.startswith("+") and not l.startswith("+++"))
        removed = sum(1 for l in chunk_lines if l.startswith("-") and not l.startswith("---"))
        end_line = chunk_start + len([l for l in chunk_lines if not l.startswith("-")]) - 1

        if added == 0 and removed == 0:
            continue

        chunk = DiffChunk(
            filename=file_diff.filename,
            language=language,
            start_line=chunk_start,
            end_line=max(end_line, chunk_start),
            content=content,
            change_type=change_type,
            added_lines=added,
            removed_lines=removed,
        )
        file_diff.chunks.append(chunk)


def _split_into_chunks(lines: list[str], start_line: int, max_lines: int) -> list[tuple[list[str], int]]:
    if len(lines) <= max_lines:
        return [(lines, start_line)]

    result = []
    current_line = start_line
    i = 0
    while i < len(lines):
        chunk = lines[i:i + max_lines]
        result.append((chunk, current_line))
        # Advance line counter by non-removal lines
        current_line += sum(1 for l in chunk if not l.startswith("-"))
        i += max_lines

    return result


def get_reviewable_chunks(file_diffs: list[FileDiff], skip_deleted: bool = True) -> list[DiffChunk]:
    chunks = []
    for fd in file_diffs:
        if skip_deleted and fd.change_type == "deleted":
            continue
        # Skip binary/generated files
        if fd.language == "Unknown" and not fd.filename.endswith((".env", ".config")):
            continue
        chunks.extend(fd.chunks)
    return chunks
