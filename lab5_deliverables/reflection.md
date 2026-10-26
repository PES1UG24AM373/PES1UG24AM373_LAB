# Reflection

The handout refers to reflection questions but does not print them, so these
are the four standard questions for this lab.

## 1. Which issues were the easiest and which were the hardest to fix?

The easiest were the mechanical ones: Flake8 spacing and line length, unused
variables, missing docstrings, renaming `logConflicts` and swapping `%` for an
f-string. Each had a clear message and a one-line fix. The hardest were the
ones where the right fix was a decision rather than an edit. Removing the
`global` statement meant choosing a different way to hand out ids
(`itertools.count`). Replacing the bare `except: pass` meant deciding what
cancelling a missing reservation should do. The `os.system("cat ...")` fix
needed care too, because I then noticed the old code printed the log before the
file was flushed, so conflicts were never shown. The bugs the tools did not
flag (slot validation, overlap detection, equipment stock) took the most
thought because I had to design the rules myself.

## 2. Did the static analysis tools report any false positives?

None that were outright wrong. Every Bandit and Flake8 finding pointed at a
real problem. Pylint was occasionally opinionated rather than wrong: the
missing-docstring warnings on tiny helpers and the `global` warning are style
and design advice, and the line-length limits disagree between tools (Pylint
100, Flake8 79). The tools also overlap, so one line often produced several
reports (the bare `except` appeared as Bandit B110, Pylint W0702 and Flake8
E722; the unused variables as Pylint W0612 and Flake8 F841). Fixing the line
once cleared all of them, which is worth knowing so the raw message count is
not mistaken for the number of separate problems.

## 3. How would you integrate static analysis into a real workflow?

Run all three tools automatically so nobody has to remember. A pre-commit hook
would catch formatting and obvious security problems before code is committed.
A CI job on every pull request would fail the build on any Bandit High finding,
on any Flake8 error, and on a Pylint score below a threshold (for example
`pylint --fail-under=9.5`). Shared configuration in `pyproject.toml` or
`.pylintrc` keeps the rules consistent across the team and lets a justified
exception be recorded with a comment rather than ignored. Editor integration
gives the earliest feedback while writing code. Reports from CI can be kept as
artifacts so score trends are visible over time.

## 4. What tangible improvements did you see after the fixes?

The numbers moved clearly: Pylint went from 5.60 to 10.00, Bandit from one High
and one Low issue to none, and Flake8 from 13 issues to none. The program also
behaves better. There is no shell call, so the filename cannot inject commands.
Files are always closed, which is why the double-booking now appears in the
log output. Invalid slots such as `14-12` and `1530` are rejected instead of
producing a -2 hour booking, equipment stock can no longer go negative,
overlapping bookings are detected, and the conflict log no longer repeats
itself. One lesson is that a perfect score does not mean correct code: the
tools never flagged the negative duration, the overlap bug or the stock bug.
Those only showed up by running the program and reading its output carefully,
so static analysis complements testing rather than replacing it.
