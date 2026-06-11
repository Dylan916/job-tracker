import typer
from job_tracker.db import init_db

app = typer.Typer(help="Track your job applications from the command line.")

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    init_db()
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())

@app.command()
def add():
    """Add a new job application."""
    print("add command")