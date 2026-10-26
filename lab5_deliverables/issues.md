# Issues found in `scheduler_system.py`

Line numbers refer to the **original** file. Reports are in `reports/before/`
and `reports/after/`.

| Tool | Before | After |
|------|--------|-------|
| Pylint | 5.60/10 (22 messages) | 10.00/10 |
| Bandit | 2 issues (1 High, 1 Low) | 0 |
| Flake8 | 13 issues | 0 |

Ordered by severity: security first, then bugs, then design and style.

| Issue | Type | Line(s) | Description | Fix Approach |
|-------|------|---------|-------------|--------------|
| Shell command built from a string (Bandit B605, **High**) | Security | 43 | `os.system("cat " + file)` starts a shell and concatenates the filename into the command, so a filename like `x; rm -rf ~` would run arbitrary commands. It also ran before the log file was closed, so the buffered conflict lines never appeared in the output. | Removed `os.system` and the `import os`. The file is now read and printed in Python after the write handle is closed (`with open(...)`). |
| Bare `except` with `pass` (Bandit B110 Low, Pylint W0702, Flake8 E722) | Bug / Security | 27-28 | `cancel_reservation` swallowed every exception, including typos and `KeyboardInterrupt`. Cancelling a non-existent id (77) silently did nothing, and a failure half way through left equipment un-returned. | Replaced try/except with `reservations.pop(id, None)`. A missing id prints a clear message; equipment is returned only after the reservation is found. |
| Mutable default argument (Pylint W0102) | Bug | 11 | `equipment_list=[]` is created once and shared by every call that omits it, so every default booking points at the same list object. | Default changed to `None`; a fresh list is created per call. |
| Files opened without `with` / encoding (Pylint R1732, W1514) | Resource leak | 35-37, 40-43 | `export_schedule` and `logConflicts` opened files manually. `logConflicts` never closed its handle at all, and neither specified an encoding. | Used `with open(..., encoding="utf-8")` everywhere so files are always flushed and closed. |
| Invalid time slots accepted (not flagged by any tool) | Logic bug | 30-32, 48-49 | `"14-12"` gave a slot length of **-2** hours, and the integer `1530` was stored as a slot even though `slot_hours` expects a string. Typing garbage such as `"abc"` at the prompt was stored as a slot, and only crashed later if `slot_hours` was called on it. | Added `parse_slot()` that requires a string `HH-HH` with `0 <= start < end <= 24`, used by both `schedule_room` and `slot_hours`. Invalid input is rejected with a message instead of a crash. |
| Equipment can go negative / unknown item corrupts state (not flagged) | Logic bug | 16-17 | Booking a second webcam took stock to **-1**. An unknown item raised `KeyError` after earlier items had already been deducted, leaving the pool wrong. | Requests are validated up front (known item, enough stock) and rejected with `ValueError` before anything is changed. |
| Only identical slots count as double-booking (not flagged) | Logic bug | 13-15 | `09-11` and `10-12` in the same room overlap, but were not reported because the check was `slot == slot`. | Compare parsed start/end hours for overlap. Back-to-back slots (`09-11`, `11-12`) are correctly not a conflict. |
| Conflicts re-logged on every call (not flagged) | Logic bug | 41-42 | `logConflicts` appended the whole `conflicts` list each time it ran, so a second call duplicated every earlier entry in the log. | Conflicts are cleared once they are written. |
| `global` statement and bad constant name (Pylint W0603, C0103) | Design | 9, 12, 19-20 | Mutating a rebound module global `next_reservation` makes the function harder to reason about and test. | Replaced with `itertools.count(1)` (`_RESERVATION_IDS`), so no `global` is needed. |
| Function name `logConflicts` (Pylint C0103) | Style | 39 | camelCase breaks PEP 8 snake_case naming. | Renamed to `log_conflicts`. |
| Missing docstrings (Pylint C0114, C0116) | Documentation | 1, 11, 22, 30, 34, 39, 45 | Module and all six functions had no docstring. | Added concise docstrings, including the exception and return contract on `schedule_room`. |
| Unused variables (Pylint W0612, Flake8 F841) | Code smell | 46, 47, 49 | `a`, `a_more` and `c` were assigned and never used. | Removed the assignments; the calls are kept for their side effects. |
| `%` formatting and index iteration (Pylint C0209, C0206) | Style | 13-15 | String built with `%` and dict iterated by key then indexed. | Used an f-string and `reservations.values()`. |
| Formatting (Flake8 E302, E305, E501) | Style | 11, 14, 18, 22, 30, 34, 39, 45, 59 | Single blank lines between functions, no blank lines before the end-of-file call, and two lines over 79 characters. | Two blank lines around top-level definitions; long lines wrapped. |
| `main()` runs on import (not flagged) | Design | 59 | Importing the module started the program and prompted for input, which makes it untestable. | Wrapped in `if __name__ == "__main__":`. |
