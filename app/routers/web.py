from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from app.models import StrategyInput, Decisions
from app.config import BASE_DIR
from app.services.db import get_db
from app.persistence.models import DBSession
from app.simulation.engine import get_staged_updates, calculate_final_kpis
from app.ai.bedrock import interpret_strategy, generate_executive_summary
from app.reports.generator import generate_report
from app.scenarios.default import SCENARIO
import uuid
import asyncio
import json
from datetime import datetime

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _session_payload(session: DBSession) -> dict:
    return {
        "id": session.id,
        "created_at": session.created_at,
        "strategy_text": session.strategy_text,
        "interpreted_strategy": session.interpreted_strategy or {},
        "decisions": session.decisions or {},
        "kpis": session.kpis or {},
        "competitor_event": session.competitor_event or "",
        "competitor_commentary": session.competitor_commentary or "",
        "executive_summary": session.executive_summary or "",
        "final_score": session.final_score or 0.0,
    }

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
        final_kpis = calculate_final_kpis(decisions, session.interpreted_strategy.get("tags", []))
        session.kpis = final_kpis
        competitor = next((s.get("competitor") for s in staged if s.get("competitor")), {})
        session.competitor_event = competitor.get("event", "")
        session.competitor_commentary = competitor.get("commentary", "")
        session.executive_summary = generate_executive_summary(_session_payload(session))
        session.final_score = final_kpis["final_score"]
        try:
            md_rel, html_rel = generate_report(_session_payload(session))
            session.report_md = md_rel
            session.report_html = html_rel
        except Exception as e:
            print(f"⚠️ Report generation failed for {session_id}: {e}")
        db.commit()
        yield 'data: {"complete": true}\n\n'
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.get("/results", response_class=HTMLResponse)
async def results_page(request: Request, session: str, db=Depends(get_db)):
    sess = db.query(DBSession).filter(DBSession.id == session).first()
    if not sess:
        raise HTTPException(404)
    return templates.TemplateResponse("results.html", {"request": request, "session": _session_payload(sess)})

@router.get("/report/{session_id}/download")
async def download_report(session_id: str, format: str = "html", db=Depends(get_db)):
    sess = db.query(DBSession).filter(DBSession.id == session_id).first()
    if not sess:
        raise HTTPException(404)

    if format not in {"html", "md"}:
        raise HTTPException(400, "Unsupported report format")

    if not sess.report_html or not sess.report_md:
        try:
            md_rel, html_rel = generate_report(_session_payload(sess))
            sess.report_md = md_rel
            sess.report_html = html_rel
            db.commit()
        except Exception as e:
            raise HTTPException(500, f"Report generation failed: {e}")

    if format == "md":
        return FileResponse(BASE_DIR / sess.report_md, media_type="text/markdown", filename=f"vibefuel-report-{session_id[:8]}.md")
    return FileResponse(BASE_DIR / sess.report_html, media_type="text/html", filename=f"vibefuel-report-{session_id[:8]}.html")

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
