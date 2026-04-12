from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from app.models import StrategyInput, Decisions
from app.services.db import get_db
from app.persistence.models import DBSession
from app.simulation.engine import get_staged_updates
from app.ai.bedrock import interpret_strategy, generate_executive_summary
from app.reports.generator import generate_report
from app.scenarios.default import SCENARIO
import uuid
import asyncio
import json
from datetime import datetime

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def welcome(request: Request):
    return templates.TemplateResponse("welcome.html", {"request": request, "scenario": SCENARIO})

@router.post("/api/strategy")
async def submit_strategy(text: str = Form(...), db=Depends(get_db)):
    session_id = str(uuid.uuid4())
    interpreted = interpret_strategy(text)
    ai_fallback = interpreted.pop("_fallback", True)
    session = DBSession(
        id=session_id,
        strategy_text=text,
        interpreted_strategy=interpreted,
        decisions={},
        kpis={},
        competitor_event="",
        competitor_commentary="",
        executive_summary="",
        final_score=0.0,
        ai_fallback=ai_fallback
    )
    db.add(session)
    db.commit()
    return {"session_id": session_id, "interpreted": interpreted}

@router.post("/api/decisions")
async def submit_decisions(session_id: str = Form(...), pricing: str = Form(...), segment: str = Form(...), channel: str = Form(...), db=Depends(get_db)):
    session = db.query(DBSession).filter(DBSession.id == session_id).first()
    if not session:
        raise HTTPException(404)
    session.decisions = {"pricing": pricing, "priority_segment": segment, "channel_mix": channel}
    db.commit()
    return {"status": "ok"}

@router.get("/simulation", response_class=HTMLResponse)
async def simulation_page(request: Request, session: str):
    return templates.TemplateResponse("simulation.html", {"request": request, "session_id": session})

@router.get("/decisions", response_class=HTMLResponse)
async def decisions_page(request: Request, session: str):
    return templates.TemplateResponse("decisions.html", {"request": request, "session_id": session})

@router.get("/api/simulation/stream/{session_id}")
async def simulation_stream(session_id: str, db=Depends(get_db)):
    async def event_generator():
        session = db.query(DBSession).filter(DBSession.id == session_id).first()
        if not session or not session.decisions:
            yield 'data: {"error": "no session"}\n\n'
            return
        decisions = Decisions(**session.decisions)
        staged = get_staged_updates(decisions, session.interpreted_strategy.get("tags", []), "")
        for stage in staged:
            yield f"data: {json.dumps(stage)}\n\n"
            # simulate real-time
            await asyncio.sleep(1.8)  # realistic delay
        # save final
        final_stage = staged[-1]
        final_kpis = final_stage["kpis"]
        final_kpis["final_score"] = final_kpis.pop("final_score", 0)  # already there
        session.kpis = final_kpis
        competitor = next((s.get("competitor") for s in staged if s.get("competitor")), {})
        session.competitor_event = competitor.get("event", "")
        session.competitor_commentary = competitor.get("commentary", "")
        session.executive_summary = generate_executive_summary(session.__dict__)
        session.final_score = final_kpis["final_score"]
        # generate report
        md_rel, html_rel = generate_report(session.__dict__)
        session.report_md = md_rel
        session.report_html = html_rel
        db.commit()
        yield 'data: {"complete": true}\n\n'
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.get("/results", response_class=HTMLResponse)
async def results_page(request: Request, session: str, db=Depends(get_db)):
    sess = db.query(DBSession).filter(DBSession.id == session).first()
    if not sess:
        raise HTTPException(404)
    return templates.TemplateResponse("results.html", {"request": request, "session": sess.__dict__})

@router.get("/report/{session_id}/download")
async def download_report(session_id: str, format: str = "html", db=Depends(get_db)):
    sess = db.query(DBSession).filter(DBSession.id == session_id).first()
    if not sess or not sess.report_html:
        raise HTTPException(404)
    if format == "md":
        return FileResponse(f"reports/{session_id}.md", media_type="text/markdown", filename=f"vibefuel-report-{session_id[:8]}.md")
    return FileResponse(f"reports/{session_id}.html", media_type="text/html", filename=f"vibefuel-report-{session_id[:8]}.html")

@router.get("/strategy", response_class=HTMLResponse)
async def strategy_page(request: Request):
    return templates.TemplateResponse("strategy.html", {"request": request})

@router.get("/reports", response_class=HTMLResponse)
async def reports_page(request: Request, db=Depends(get_db)):
    sessions = (
        db.query(DBSession)
        .filter(DBSession.report_html.isnot(None))
        .order_by(DBSession.created_at.desc())
        .all()
    )
    return templates.TemplateResponse(
        "reports.html",
        {
            "request": request,
            "sessions": sessions,
        },
    )
