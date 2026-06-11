import typer
from job_tracker.db import init_db, get_conn
from datetime import date, datetime
from rich.console import Console
from rich.table import Table
from rich import box
from datetime import date, datetime, timedelta

app = typer.Typer(help="Track your job applications from the command line.")

console = Console()

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

    
    table = Table(box=box.SIMPLE_HEAVY)
    table.add_column("ID", style="dim", width=4)
    table.add_column("Company")
    table.add_column("Role")
    table.add_column("Location")
    table.add_column("Status")
    table.add_column("Date")
    table.add_column("Notes")

    for row in rows:
        table.add_row(
            str(row["id"]),
            row["company"],
            row["role"],
            row["location"] or "—",
            row["status"],
            row["date"],
            (row["notes"] or "")[:40],
        )

    console.print(table)
    console.print(f"[dim]{len(rows)} application(s)[/dim]")

@app.command()
def update(
    app_id: int = typer.Argument(..., help="Application ID to update"),
    status: str = typer.Option(None, "--status", "-s", help="New status"),
    notes: str = typer.Option(None, "--notes", "-n", help="Update notes"),
    url: str = typer.Option(None, "--url", "-u", help="Update URL"),
) -> None:
    """Update an existing application by ID."""
    fields = ["updated_at = ?"]
    params = [datetime.now().isoformat(timespec="seconds")]

    if status:
        fields.append("status = ?")
        params.append(status)
    if notes:
        fields.append("notes = ?")
        params.append(notes)
    if url:
        fields.append("url = ?")
        params.append(url)

    if len(fields) == 1:
        typer.echo("Nothing to update. Pass --status, --notes, or --url.")
        raise typer.Exit(1)

    params.append(app_id)

    with get_conn() as conn:
        result = conn.execute(
            f"UPDATE applications SET {', '.join(fields)} WHERE id = ?", params
        )
        conn.commit()

    if result.rowcount == 0:
        typer.echo(f"No application found with ID {app_id}.")
        raise typer.Exit(1)

    typer.echo(f"Updated #{app_id}")

@app.command()
def delete(
    app_id: int = typer.Argument(..., help="Application ID to delete"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
) -> None:
    """Delete an application by ID."""
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM applications WHERE id = ?", (app_id,)).fetchone()

    if not row:
        typer.echo(f"No application found with ID {app_id}.")
        raise typer.Exit(1)

    if not yes:
        typer.confirm(f"Delete #{app_id}: {row['company']} — {row['role']}?", abort=True)

    with get_conn() as conn:
        conn.execute("DELETE FROM applications WHERE id = ?", (app_id,))
        conn.commit()

    typer.echo(f"Deleted #{app_id}")

@app.command()
def stats() -> None:
    """Show a summary of applications by status."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT status, COUNT(*) as count FROM applications GROUP BY status ORDER BY count DESC"
        ).fetchall()
        total = conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0]

    if total == 0:
        typer.echo("No applications yet.")
        return

    table = Table(box=box.SIMPLE_HEAVY)
    table.add_column("Status")
    table.add_column("Count", justify="right")
    table.add_column("Share", justify="right")

    for row in rows:
        pct = f"{row['count'] / total * 100:.0f}%"
        table.add_row(row["status"], str(row["count"]), pct)

    table.add_section()
    table.add_row("[bold]Total[/bold]", f"[bold]{total}[/bold]", "")

    console.print(table)

@app.command()
def remind(
    days: int = typer.Option(7, "--days", "-d", help="Flag apps with no update in this many days"),
) -> None:
    """List applications that haven't been updated recently."""
    cutoff = (datetime.now() - timedelta(days=days)).isoformat(timespec="seconds")

    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT * FROM applications
            WHERE status NOT IN ('offer', 'rejected', 'withdrawn')
            AND updated_at < ?
            ORDER BY updated_at ASC
            """,
            (cutoff,),
        ).fetchall()

    if not rows:
        typer.echo(f"No stale applications (nothing older than {days} days).")
        return

    console.print(f"[yellow]{len(rows)} application(s) with no update in {days}+ days:[/yellow]\n")

    table = Table(box=box.SIMPLE_HEAVY)
    table.add_column("ID", style="dim", width=4)
    table.add_column("Company")
    table.add_column("Role")
    table.add_column("Status")
    table.add_column("Last Updated")

    for row in rows:
        table.add_row(
            str(row["id"]),
            row["company"],
            row["role"],
            row["status"],
            row["updated_at"][:10],
        )

    console.print(table)