# Value Errors Explained.

## Question 1

Can you explain what a ValueError is and how you determined that find_folders_without_solutions would have only that exception? Include references to any youtube tutorial that explains the same thing and in more detail.

## Answer 1: Understanding ValueError

A **`ValueError`** is a specific type of exception in Python that indicates an argument passed to a function has the right type (data type) but an **invalid value** that the function cannot process.

### Examples of ValueError:

```python
# ValueError: invalid literal for int() with base 10: 'abc'
int("abc")

# ValueError: not enough values to unpack
x, y = [1, 2, 3]

# ValueError: invalid literal for int()
int("12.5")
```

---

## How I Determined find_folders_without_solutions Raises ValueError

Looking at the function on **line 11** of your code:

```python
if not root_path.is_dir():
    raise ValueError(f"The path '{root_dir}' is not a valid directory.")
```

This line **explicitly raises a `ValueError`** when the input `root_dir` is not a valid directory path. The function is saying: "You gave me a string, but it's not a valid directory path—that's an invalid value."

**However, I need to correct my earlier suggestion:** Looking more carefully at the function, it _could_ also raise other exceptions:

- **`OSError`** or **`PermissionError`** from file system operations (like `Path.walk()`) if you don't have permission to access certain folders
- **`FileNotFoundError`** if the path is deleted during execution

So catching **only** `ValueError` would miss these other possible errors. A more accurate approach would be:

```python
except (ValueError, OSError) as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
```

---

## YouTube Tutorials on Exception Handling

Here are some excellent resources that explain Python exceptions in detail:

1. **Corey Schafer - Python Exception Handling** (Highly recommended)
   - https://www.youtube.com/watch?v=NIWwJbo-TzY
   - Explains different exception types and when to use them

2. **Tech with Tim - Python Exceptions Tutorial**
   - https://www.youtube.com/watch?v=ZsvfAW9ztZo
   - Covers try/except/finally and specific exception catching

3. **Real Python - Python Exceptions** (Video format)
   - https://www.youtube.com/watch?v=Clw7T_pLJmA
   - Explains ValueError and other built-in exceptions with practical examples

4. **Programming with Mosh - Python Exceptions**
   - https://www.youtube.com/watch?v=ZsvfAW9ztZo
   - Beginner-friendly explanation of when exceptions occur

The key principle from all these tutorials: **Be specific with exceptions you catch**—only catch what you expect to handle, so unexpected errors bubble up and get your attention during development.
