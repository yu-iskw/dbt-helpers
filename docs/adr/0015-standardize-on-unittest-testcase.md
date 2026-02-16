# 15. Standardize on unittest.TestCase for Unit Tests

Date: 2026-02-16

## Status

Accepted

## Context

The project currently uses `pytest` style tests (standalone functions using `assert`). While efficient, this approach can sometimes lack the structural rigidity and explicit lifecycle management (setup/teardown) found in xUnit-style frameworks.

There is a desire to standardize on Python's built-in `unittest.TestCase` to:

1. Reduce dependency on external test runners for _defining_ tests (tests become valid Python scripts).
2. Enforce a class-based structure for grouping related tests.
3. Utilize explicit `setUp` and `tearDown` methods for state management.
4. Align with standard xUnit patterns familiar to developers coming from other languages.

## Decision

We will standardize all unit tests to use the `unittest.TestCase` class from the Python standard library.

1. **Inheritance**: All unit test classes must inherit from `unittest.TestCase`.
2. **Assertions**: Use `self.assert*` methods (e.g., `self.assertEqual`, `self.assertTrue`) instead of bare `assert`.
3. **Lifecycle**: Use `setUp` and `tearDown` for test fixture management.
4. **Runner**: We will continue to use `pytest` as the test runner, as it fully supports `unittest.TestCase` and offers superior output formatting and reporting.

## Consequences

- **Standardization**: All tests will follow a consistent class-based structure.
- **Portability**: Tests can be run by standard `python -m unittest` without strictly requiring `pytest` for execution (though `pytest` remains the primary runner).
- **Explicit State**: Setup and teardown logic is explicitly defined in the class, avoiding implicit fixture injection.
- **Migration Effort**: Existing unit tests need to be refactored from functional to class-based style.
- **Fixture Limitations**: We lose the ability to easily use modular `pytest` fixtures (like `tmp_path`) directly in test method signatures; they must be accessed via other means or replaced with standard library equivalents (e.g., `tempfile`).
