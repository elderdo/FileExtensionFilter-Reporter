import argparse
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# Folders to skip during traversal to avoid clutter and permission errors
IGNORED_DIRS = {".git", ".vs", ".vscode", "bin", "obj", "node_modules", "__pycache__"}


def normalize_extensions(ext_list: list[str]) -> set[str]:
    """Ensure all extensions start with a leading dot and are lowercase."""
    return {ext.lower() if ext.startswith(".") else f".{ext.lower()}" for ext in ext_list}


def deep_scan_for_extensions(
    start_dir: Path,
    target_exts: set[str],
    found_files_log: dict[str, list[Path]],
) -> set[str]:
    """
    Recursively scans start_dir and its subdirectories for target_exts.
    Stops scanning as soon as at least one matching file is found, returning
    the matched extension(s) in that directory.
    """
    for current_dir, dirs, files in start_dir.walk():
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")]

        matched_in_dir = set()
        for f in files:
            ext = Path(f).suffix.lower()
            if ext in target_exts:
                matched_in_dir.add(ext)
                found_files_log[ext].append(current_dir / f)

        # Stop diving deeper once a match is found
        if matched_in_dir:
            return matched_in_dir

    return set()


def analyze_folders(
    root_dir: str,
    primary_exts: set[str],
    max_depth: int | None = None,
    deep_exts: set[str] | None = None,
) -> tuple[list[Path], dict[Path, set[str]], dict[str, list[Path]]]:
    root_path = Path(root_dir).resolve()

    if not root_path.is_dir():
        raise ValueError(f"The path '{root_dir}' is not a valid directory.")

    missing_primary_folders: list[Path] = []
    deep_dive_hits: dict[Path, set[str]] = {}
    found_files_log: dict[str, list[Path]] = defaultdict(list)

    for current_dir, dirs, files in root_path.walk():
        current_depth = len(current_dir.relative_to(root_path).parts)

        if max_depth is not None and current_depth >= max_depth:
            dirs.clear()
        else:
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")]

        # When a depth limit is set (e.g., --depth 1), skip evaluating the root folder itself
        if max_depth is not None and current_depth == 0:
            continue

        has_primary = False
        for f in files:
            ext = Path(f).suffix.lower()
            if ext in primary_exts:
                has_primary = True
                found_files_log[ext].append(current_dir / f)

        if not has_primary:
            missing_primary_folders.append(current_dir)

            # Perform deeper dive for secondary extensions if requested
            if deep_exts:
                matched_deep = deep_scan_for_extensions(current_dir, deep_exts, found_files_log)
                if matched_deep:
                    deep_dive_hits[current_dir] = matched_deep

    return missing_primary_folders, deep_dive_hits, found_files_log


def write_extension_logs(found_files_log: dict[str, list[Path]], output_dir: Path, timestamp: str) -> list[Path]:
    """Writes a separate <ext>-<timestamp>.log file for each extension type found."""
    created_logs: list[Path] = []

    for ext, paths in sorted(found_files_log.items()):
        if not paths:
            continue

        clean_ext = ext.lstrip(".")
        log_path = output_dir / f"{clean_ext}-{timestamp}.log"

        with log_path.open("w", encoding="utf-8") as f:
            f.write(f"# Files matching '{ext}' found on {timestamp}\n")
            f.write(f"# Total: {len(paths)}\n\n")
            for p in sorted(paths):
                f.write(f"{p}\n")

        created_logs.append(log_path)

    return created_logs


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Find folders missing specified file extensions, with optional deep-dive scanning and per-extension logging."
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Root directory to search (defaults to current directory).",
    )
    parser.add_argument(
        "-d", "--depth",
        type=int,
        default=None,
        help="Maximum folder depth to search (e.g., 1 checks only immediate subfolders).",
    )
    parser.add_argument(
        "-e", "--extensions",
        nargs="+",
        default=["sln", "slnx"],
        help="Primary file extensions to check for (default: sln slnx).",
    )
    parser.add_argument(
        "--deep-ext",
        nargs="+",
        default=None,
        help="Secondary extensions to search for recursively inside folders missing the primary extensions (e.g., csproj cs).",
    )
    parser.add_argument(
        "--log-dir",
        default=".",
        help="Directory where timestamped .log files will be saved (defaults to current directory).",
    )

    args = parser.parse_args()

    try:
        if args.depth is not None and args.depth < 1:
            raise ValueError("Depth must be 1 or greater.")

        primary_exts = normalize_extensions(args.extensions)
        deep_exts = normalize_extensions(args.deep_ext) if args.deep_ext else None
        log_dir = Path(args.log_dir).resolve()
        log_dir.mkdir(parents=True, exist_ok=True)

        missing_folders, deep_hits, found_log = analyze_folders(
            args.directory, primary_exts, args.depth, deep_exts
        )

        ext_display = ", ".join(sorted(primary_exts))
        depth_label = f" (max depth: {args.depth})" if args.depth else ""
        print(f"Folders without [{ext_display}] in '{Path(args.directory).resolve()}'{depth_label}:\n")

        for folder in missing_folders:
            if folder in deep_hits:
                found_str = ", ".join(sorted(deep_hits[folder]))
                print(f"{folder}  [Deep dive found: {found_str}]")
            else:
                print(folder)

        print(f"\nTotal folders without [{ext_display}]: {len(missing_folders)}")

        # Write timestamped logs for each extension type found
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        created_logs = write_extension_logs(found_log, log_dir, timestamp)

        if created_logs:
            print("\nExtension logs created:")
            for log_file in created_logs:
                print(f"  {log_file}")
        else:
            print("\nNo matching extension files were found, so no log files were created.")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
