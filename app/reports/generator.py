import json
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from app.config import REPORTS_DIR, BASE_DIR

env = Environment(loader=FileSystemLoader(BASE_DIR / "app/templates"))

def generate_report(session: dict) -> tuple[str, str]:
    md_path = REPORTS_DIR / f"{session['id']}.md"
    html_path = REPORTS_DIR / f"{session['id']}.html"

    # Markdown
    md_content = f"""# VibeFuel Go-To-Market Report
**Session:** {session['id']}
**Date:** {session['created_at']}

## Strategy
{session['strategy_text']}

## Decisions
- Pricing: {session['decisions']['pricing']}
- Segment: {session['decisions']['priority_segment']}
- Channel: {session['decisions']['channel_mix']}

## Final KPIs
{json.dumps(session['kpis'], indent=2)}

**Final Score: {session['final_score']} / 100**

## Executive Summary
{session['executive_summary']}
"""
    md_path.write_text(md_content)

    # HTML (beautiful printable)
    template = env.get_template("report.html")
    html_content = template.render(session=session)
    html_path.write_text(html_content)

    return str(md_path.relative_to(BASE_DIR)), str(html_path.relative_to(BASE_DIR))
