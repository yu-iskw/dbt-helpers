import yaml
from jinja2 import Environment, PackageLoader, select_autoescape


class BaseRenderer:
    """Base class for dbt resource renderers with shared Jinja2 environment."""

    def __init__(self, env: Environment | None = None) -> None:
        if env:
            self.env = env
        else:
            self.env = Environment(
                loader=PackageLoader("dbt_helpers_schema_dbt", "templates"),
                autoescape=select_autoescape(),
                extensions=["jinja2.ext.do"],
            )
            self.env.filters["to_yaml"] = lambda d: yaml.dump(
                d, sort_keys=False, default_flow_style=False
            )
