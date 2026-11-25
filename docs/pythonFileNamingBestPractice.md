# Python scripts file names

## Question

Is it a best practice to use snake file names for python scripts?

## Answer

## Snake_Case for Python Filenames: Yes, It's Best Practice

**Yes, absolutely!** Using `snake_case` (lowercase with underscores) for Python filenames is the officially recommended convention.

### Official Standards

1. **PEP 8 - Python Enhancement Proposal 8** (The official Python style guide)
   - Recommends: lowercase filenames with underscores separating words
   - Example: `find_non_sln_folders.py` ✅ (what you're already doing)
   - **Not recommended:** `FindNonSlnFolders.py` ❌ or `findNonSlnFolders.py` ❌

2. **Python Naming Conventions Summary:**
   - **Filenames:** `snake_case` (e.g., `my_script.py`, `data_processor.py`)
   - **Functions:** `snake_case` (e.g., `def calculate_total()`)
   - **Variables:** `snake_case` (e.g., `user_name = "John"`)
   - **Classes:** `PascalCase` (e.g., `class DataProcessor:`)
   - **Constants:** `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES = 5`)

### Why Snake_Case for Filenames?

1. **Consistency:** Matches Python's naming convention for functions and variables
2. **Readability:** Easier to read than camelCase on command line and in imports
3. **Avoid Conflicts:** Some systems treat filenames case-insensitively, causing issues
4. **Professional Standard:** Followed by major Python projects and organizations

### Your File:

Your filename `find-non-sln-folders.py` uses **hyphens** (kebab-case), which is actually **not standard for Python files**. The Python convention would be:

```python
find_non_sln_folders.py  ✅ (recommended)
```

This is a minor style issue—it won't break anything, but following `snake_case` keeps your project aligned with Python community standards.

---

**Reference:** You can read the full PEP 8 style guide at https://pep8.org/ (or the official version at https://www.python.org/dev/peps/pep-0008/)
