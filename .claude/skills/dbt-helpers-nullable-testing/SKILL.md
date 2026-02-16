---
name: dbt-helpers-nullable-testing
description: Implement and use Nullable Infrastructure adapters for mock-free testing. Use when writing unit tests for core logic, implementing infrastructure adapters, or setting up test fixtures.
---

# dbt-helpers-nullable-testing

## Purpose

To ensure fast, deterministic, and reliable testing without the brittleness of standard mocking libraries. This skill implements the "Functional Core, Imperative Shell" philosophy using the Nullable Infrastructure pattern.

## Core Principles

1. **No standard mocks**: Avoid `unittest.mock` for infrastructure (I/O, DB, CLI).
2. **Nullable Adapters**: Real implementations with an "off switch" or in-memory substitute.
3. **Internal State Tracking**: Adapters should track their output/actions for state-based assertions.

## Implementation Patterns

### 1. In-memory Substitutes

- Use DuckDB in-memory for catalog clients.
- Use a dictionary-based `MemoryFileSystem` for file I/O.
- Use a list-based `BufferEmitter` for CLI output.

### 2. Nullable Constructor

Each infrastructure class should provide a `.create_null()` factory method:

```python
class CatalogClient(ABC):
    @classmethod
    def create_null(cls, metadata: dict = None):
        return NullCatalogClient(metadata)
```

## Instructions

### When writing unit tests

1. Use the `.create_null()` version of the adapter.
2. Provide pre-configured state to the nullable adapter (e.g., `CatalogClient.create_null(tables=[...])`).
3. Assert on the results of the logic, or check the adapter's internal state if necessary.

### When implementing a new adapter

1. Define the interface (Protocol/ABC) in the SDK.
2. Implement the production version.
3. Implement the Nullable version (usually in the same file or a `testing.py` module).

## References

- [ADR 0006: Nullable Infrastructure Testing Strategy](../../../docs/adr/0006-nullable-infrastructure-testing-strategy.md)
- [Testing Without Mocks (James Shore)](https://www.jamesshore.com/v2/blog/2018/testing-without-mocks)
