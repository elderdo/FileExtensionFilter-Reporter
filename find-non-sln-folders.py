import argparse
import sys
from pathlib import Path

# Folders to skip during traversal to avoid clutter and permission errors
IGNORED_DIRS = {".git", ".vs", ".vscode", "bin", "obj", "node_modules", "__pycache__"}

def find_folders_without_solutions(root_dir: str, max_depth: int | None = None) -> list[Path]:
    root_path = Path(root_dir).resolve()
    
    if not root_path.is_dir():
        raise ValueError(f"The path '{root_dir}' is not a valid directory.")

    folders_without_sln = []

    for current_dir, dirs, files in root_path.walk():
        # Calculate how many levels deep current_dir is from root_path
        current_depth = len(current_dir.relative_to(root_path).parts)

        # Stop descending deeper if we have reached max_depth
        if max_depth is not None and current_depth >= max_depth:
            dirs.clear()
        else:
            # Otherwise, filter out ignored or hidden folders before descending
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")]

        # When a depth limit is set (e.g., --depth 1), skip evaluating the root folder itself (depth 0)
        if max_depth is not None and current_depth == 0:
            continue

        # Check if any file in the current directory ends with .sln or .slnx (case-insensitive)
        has_solution = any(
            Path(f).suffix.lower() in {".sln", ".slnx"} for f in files
        )

        if not has_solution:
            folders_without_sln.append(current_dir)

    return folders_without_sln

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Find folders that do not contain a .sln or .slnx file."
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Root directory to search (defaults to current directory)."
    )
    parser.add_argument(
        "-d", "--depth",
        type=int,
        default=None,
        help="Maximum folder depth to search (e.g., 1 checks only immediate subfolders)."
    )

    args = parser.parse_args()

    try:
        if args.depth is not None and args.depth < 1:
            raise ValueError("Depth must be 1 or greater.")

        missing_sln_folders = find_folders_without_solutions(args.directory, args.depth)
        
        depth_label = f" (max depth: {args.depth})" if args.depth else ""
        print(f"Folders without .sln or .slnx files in '{Path(args.directory).resolve()}'{depth_label}:\n")
        
        for folder in missing_sln_folders:
            print(folder)
            
        print(f"\nTotal folders found: {len(missing_sln_folders)}")
        
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
