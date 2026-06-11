import typer

app = typer.Typer(help="Track your job applications from the command line.")

@app.command()
def add():
    """Add a new job application."""
    print("add command")

def main():
    app()