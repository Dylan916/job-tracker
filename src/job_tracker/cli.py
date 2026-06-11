import typer
from job_tracker.db import init_db, get_conn
from datetime import date, datetime

app = typer.Typer(help="Track your job applications from the command line.")

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    init_db()
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


@app.command()
def add(
    company: str = typer.Option(..., "--company", "-c", help="Company name"),
    role: str = typer.Option(..., "--role", "-r", help="Role or position title"),
    location: str = typer.Option(None, "--location", "-l", help="Job location"),
    status: str = typer.Option("applied", "--status", "-s", help="Application status"),
    date_applied: str = typer.Option(None, "--date", "-d", help="Date applied (YYYY-MM-DD). Defaults to today."),
    url: str = typer.Option(None, "--url", "-u", help="Link to job posting"),
    notes: str = typer.Option(None, "--notes", "-n", help="Any notes"),
) -> None:
    """Add a new job application."""
    applied_date = date_applied or date.today().isoformat()

    with get_conn() as conn:
        cursor = conn.execute(
            """
            INSERT INTO applications (company, role, location, status, date, url, notes, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (company, role, location, status, applied_date, url, notes, datetime.now().isoformat(timespec="seconds")),
        )
        conn.commit()

    typer.echo(f"Added #{cursor.lastrowid}: {company} — {role}")

@app.command(name="list")
def list_apps(
    status: str = typer.Option(None, "--status", "-s", help="Filter by status"),
    company: str = typer.Option(None, "--company", "-c", help="Filter by company (partial match)"),
) -> None:
    """List job applications."""
    query = "SELECT * FROM applications WHERE 1=1"
    params = []

    if status:
        query += " AND status = ?"
        params.append(status)

    if company:
        query += " AND company LIKE ?"
        params.append(f"%{company}%")

    query += " ORDER BY date DESC"

    with get_conn() as conn:
        rows = conn.execute(query, params).fetchall()

    if not rows:
        typer.echo("No applications found.")
        return

    for row in rows:
        typer.echo(f"#{row['id']} {row['company']} — {row['role']} [{row['status']}] {row['date']}") 