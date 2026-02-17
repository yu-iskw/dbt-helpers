import typer

from .commands.model import app as model_app
from .commands.snapshot import app as snapshot_app
from .commands.source import app as source_app

app = typer.Typer()

app.add_typer(source_app, name="source")
app.add_typer(model_app, name="model")
app.add_typer(snapshot_app, name="snapshot")

if __name__ == "__main__":
    app()
