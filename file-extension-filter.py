# Standard library imports: these come built-in with Python (no 'pip install' required).
import argparse  # Parses command-line arguments and automatically builds '--help' menus.
import sys  # Provides access to system-level tools like standard error output and exit codes.
from collections import defaultdict  # A dictionary that automatically creates a default value (like an empty list) for new keys.
from datetime import datetime  # Used to generate timestamps (e.g., 20261125-161500) for log filenames.
from pathlib import Path  # Modern, object-oriented way to work with file and folder paths across Windows, macOS, and Linux.

# A 'set' (curly braces) is used instead of a list because checking 'if folder in IGNORED_DIRS'
# is virtually instantaneous in a set, regardless of how many items are inside.
IGNORED_DIRS = {".git", ".vs", ".vscode", "bin", "obj", "node_modules", "__pycache__"}


# Type hints (e.g., 'ext_list: list[str] -> set[str]') document what data types a function expects
# and returns, making the code easier to read and helping editors catch mistakes early.
def normalize_extensions(ext_list: list[str]) -> set[str]:
    """Ensure all extensions start with a leading dot and are lowercase."""
    # Set comprehension: builds a new set in one readable line.
    # For example, turns ["SLN", ".slnx"] into {".sln", ".slnx"} so comparisons are always consistent.
    return {ext.lower() if ext.startswith(".") else f".{ext.lower()}" for ext in ext_list}


def deep_scan_for_extensions(
    start_dir: Path,
    target_exts: set[str],
    found_files_log: dict[str, list[Path]],
) -> set[str]:
    """
    Recursively scans start_dir and all its non-ignored subdirectories for target_exts.
    Records every matching file in found_files_log and returns all matched extensions.
    """
    # Create an empty set to track which target extensions were found anywhere under start_dir.
    # Note: We use 'set()' because empty '{}' in Python creates a dictionary, not a set.
    all_matched: set[str] = set()

    # 'start_dir.walk()' (introduced in Python 3.12) traverses a directory tree from top to bottom,
    # yielding a 3-item tuple at each step: (current folder Path, list of subfolder names, list of file names).
    for current_dir, dirs, files in start_dir.walk():
        # Modifying 'dirs[:]' in-place (the slice '[:]' mutates the original list in memory)
        # tells '.walk()' NOT to descend into ignored or hidden folders (folders starting with '.').
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")]

        for f in files:
            # 'Path(f).suffix' extracts just the file extension (e.g., 'App.csproj' -> '.csproj').
            ext = Path(f).suffix.lower()
            if ext in target_exts:
                all_matched.add(ext)
                # The '/' operator on a Path object safely joins folders and filenames using the OS separator ('\' on Windows).
                # Because 'found_files_log' is a defaultdict(list), appending works even if 'ext' hasn't been seen yet.
                found_files_log[ext].append(current_dir / f)

    return all_matched


def analyze_folders(
    root_dir: str,
    primary_exts: set[str],
    max_depth: int | None = None,  # 'int | None' means this parameter can be an integer OR None (optional).
    deep_exts: set[str] | None = None,
) -> tuple[list[Path], dict[Path, set[str]], dict[str, list[Path]]]:
    # '.resolve()' converts a relative path (like '.') into a full, absolute path (like 'C:\Users\Douglas\...').
    root_path = Path(root_dir).resolve()

    # Validate early: raise a clear error if the user passed a typo or a file instead of a folder.
    if not root_path.is_dir():
        raise ValueError(f"The path '{root_dir}' is not a valid directory.")

    missing_primary_folders: list[Path] = []
    deep_dive_hits: dict[Path, set[str]] = {}
    found_files_log: dict[str, list[Path]] = defaultdict(list)

    for current_dir, dirs, files in root_path.walk():
        # '.relative_to(root_path)' strips the root prefix, and '.parts' splits the remaining path into folder names.
        # Counting '.parts' tells us exact folder depth (0 = root folder, 1 = immediate subfolder, etc.).
        current_depth = len(current_dir.relative_to(root_path).parts)

        # If we reached the user's max_depth, '.clear()' empties 'dirs' in-place so '.walk()' stops going deeper.
        if max_depth is not None and current_depth >= max_depth:
            dirs.clear()
        else:
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")]

        # When a depth limit is set (e.g., --depth 1), skip checking the root folder itself (depth 0)
        # so we only inspect the folders inside it.
        if max_depth is not None and current_depth == 0:
            continue

        has_primary = False
        for f in files:
            ext = Path(f).suffix.lower()
            if ext in primary_exts:
                has_primary = True
                found_files_log[ext].append(current_dir / f)

        # If none of the primary extensions (like .sln or .slnx) were found in this folder:
        if not has_primary:
            missing_primary_folders.append(current_dir)

            # If the user supplied '--deep-ext', recursively search inside this folder for secondary files.
            if deep_exts:
                matched_deep = deep_scan_for_extensions(current_dir, deep_exts, found_files_log)
                if matched_deep:
                    deep_dive_hits[current_dir] = matched_deep

    # Return all three collected data structures together as a tuple.
    return missing_primary_folders, deep_dive_hits, found_files_log


def write_extension_logs(found_files_log: dict[str, list[Path]], output_dir: Path, timestamp: str) -> list[Path]:
    """Writes a separate <ext>-<timestamp>.log file for each extension type found."""
    created_logs: list[Path] = []

    # 'sorted(...)' ensures log files and file paths inside them are written in predictable alphabetical order.
    for ext, paths in sorted(found_files_log.items()):
        if not paths:
            continue

        # Remove the leading dot (e.g., '.csproj' -> 'csproj') for a clean filename.
        clean_ext = ext.lstrip(".")
        log_path = output_dir / f"{clean_ext}-{timestamp}.log"

        # 'with ... open(...)' is a context manager: it automatically closes and saves the file when the block ends,
        # even if an error happens while writing. Explicit 'utf-8' prevents character encoding issues on Windows.
        with log_path.open("w", encoding="utf-8") as f:
            f.write(f"# Files matching '{ext}' found on {timestamp}\n")
            f.write(f"# Total: {len(paths)}\n\n")
            for p in sorted(paths):
                f.write(f"{p}\n")

        created_logs.append(log_path)

    return created_logs


# Standard Python idiom: code inside this 'if' block only runs when the script is executed directly
# from the command line, NOT if another Python script imports functions from this file.
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Find folders missing specified file extensions, with optional deep-dive scanning and per-extension logging."
    )
    # 'nargs="?"' makes the positional 'directory' argument optional, falling back to '.' (current folder).
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
    # 'nargs="+"' accepts one or more space-separated values (e.g., '-e sln slnx').
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

    # Parse the command-line arguments passed by the user into the 'args' object.
    args = parser.parse_args()

    # 'try / except' catches errors cleanly so the user gets a readable message instead of a raw Python traceback.
    try:
        if args.depth is not None and args.depth < 1:
            raise ValueError("Depth must be 1 or greater.")

        primary_exts = normalize_extensions(args.extensions)
        # Ternary expression: normalize deep_ext if provided; otherwise keep it as None.
        deep_exts = normalize_extensions(args.deep_ext) if args.deep_ext else None
        log_dir = Path(args.log_dir).resolve()
        # 'parents=True' creates any missing parent folders; 'exist_ok=True' avoids an error if the folder already exists.
        log_dir.mkdir(parents=True, exist_ok=True)

        # Unpack the 3-item tuple returned by 'analyze_folders' into three separate variables.
        missing_folders, deep_hits, found_log = analyze_folders(
            args.directory, primary_exts, args.depth, deep_exts
        )

        # Format and print the summary report to the console (stdout).
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

        # Format the current date and time as 'YYYYMMDD-HHMMSS' and write the per-extension log files.
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        created_logs = write_extension_logs(found_log, log_dir, timestamp)

        if created_logs:
            print("\nExtension logs created:")
            for log_file in created_logs:
                print(f"  {log_file}")
        else:
            print("\nNo matching extension files were found, so no log files were created.")

    except ValueError as e:
        # Print errors to 'sys.stderr' (standard error stream) so they don't mix into redirected output files ('> result.txt').
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
