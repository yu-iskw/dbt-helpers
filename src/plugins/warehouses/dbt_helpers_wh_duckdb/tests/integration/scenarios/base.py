from pathlib import Path

from dbt_helpers_sdk.testing import DirectoryScenario, Scenario, ScenarioRegistry

# Global registry instance
registry = ScenarioRegistry()

# Default profiles config for DuckDB
DUCKDB_DEFAULT_PROFILE = {"path": "dev.duckdb"}

# Define the default sample_project scenario
sample_project = Scenario(
    name="sample_project",
    models={
        "users": "select 1 as id, 'Alice' as name union all select 2 as id, 'Bob' as name",
        "orders": "select 1 as id, 1 as user_id, 100 as amount union all select 2 as id, 2 as user_id, 200 as amount",
    },
    project_vars={"my_var": "default_value"},
    adapter_type="duckdb",
    profiles_config=DUCKDB_DEFAULT_PROFILE,
)

registry.register(sample_project)


# Scenario for testing description sync
sync_description = Scenario(
    name="sync_description",
    models={
        "users": "select 1 as id, 'Alice' as name",
    },
    adapter_type="duckdb",
    profiles_config=DUCKDB_DEFAULT_PROFILE,
)

# Scenario for testing column addition
add_column = Scenario(
    name="add_column",
    models={
        "users": "select 1 as id, 'Alice' as name",
    },
    adapter_type="duckdb",
    profiles_config=DUCKDB_DEFAULT_PROFILE,
)

# Scenario for complex DuckDB types
complex_types = Scenario(
    name="complex_types",
    models={
        "complex_model": """
            SELECT
                1 as id,
                {'name': 'Alice', 'age': 30} as person_struct,
                [1, 2, 3] as int_list,
                ['apple', 'banana'] as string_list,
                map(['key1', 'key2'], [10, 20]) as string_int_map,
                'RED'::ENUM('RED', 'GREEN', 'BLUE') as color_enum,
                TIMESTAMP '2022-01-01 10:00:00' as ts,
                DATE '2022-01-01' as dt,
                INTERVAL '1 day' as inv
        """
    },
    adapter_type="duckdb",
    profiles_config=DUCKDB_DEFAULT_PROFILE,
)

# Scenario for multiple schemas
multi_schema = Scenario(
    name="multi_schema",
    models={
        "stg_users": "{{ config(schema='staging') }} SELECT 1 as id, 'Alice' as name",
        "int_users": "{{ config(schema='intermediate') }} SELECT 1 as id, 'Alice' as name",
        "dim_users": "SELECT 1 as id, 'Alice' as name", # Default schema (main)
    },
    adapter_type="duckdb",
    profiles_config=DUCKDB_DEFAULT_PROFILE,
)

registry.register(sync_description)
registry.register(add_column)
registry.register(complex_types)
registry.register(multi_schema)


# Realistic jaffle_shop project
jaffle_shop = DirectoryScenario(
    name="jaffle_shop",
    base_path=Path(__file__).parent.parent / "fixtures" / "jaffle_shop",
    adapter_type="duckdb",
    profiles_config=DUCKDB_DEFAULT_PROFILE,
)

registry.register(jaffle_shop)
