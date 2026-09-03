import sqlite3
from pathlib import Path

DB_PATH = "168hours.db"
SQL_DIR = Path("sql")
RESULTS_DIR = SQL_DIR / "results"
REPORT_PATH = Path("report.md")

QUERIES = [
    ("01_daily_temp_stats", "Daily temperature stats per city"),
    ("02_widest_temp_range", "Widest temperature range over 7 days"),
    ("03_highest_rain_chance_hour", "Highest rain-chance hour per city per day"),
    ("04_daily_avg_temp_delta", "Daily avg temp delta vs previous day"),
]


def to_markdown_table(columns, rows):
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    lines = [header, sep]
    for row in rows:
        cells = ["" if v is None else str(v) for v in row]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def main():
    conn = sqlite3.connect(DB_PATH)
    run_date = conn.execute("select max(ingested_at_utc) from hourly_forecast").fetchone()[0]

    RESULTS_DIR.mkdir(exist_ok=True)
    sections = []
    for stem, title in QUERIES:
        sql = (SQL_DIR / f"{stem}.sql").read_text()
        cursor = conn.execute(sql)
        columns = [d[0] for d in cursor.description]
        rows = cursor.fetchall()
        table = to_markdown_table(columns, rows)

        (RESULTS_DIR / f"{stem}.md").write_text(f"# {title}\n\nRun: {run_date}\n\n{table}\n")
        sections.append(f"## {title}\n\n{table}\n")

    conn.close()

    report = f"# 168 Hours - Weather Forecast Report\n\nRun: {run_date}\n\n" + "\n".join(sections)
    REPORT_PATH.write_text(report)
    print(f"wrote report.md and {len(QUERIES)} files under sql/results/ (run: {run_date})")


if __name__ == "__main__":
    main()
