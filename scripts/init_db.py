#!/usr/bin/env python3
"""
Initialize SQLite database on first boot
"""
from app.persistence.models import Base, DBSession, engine, SessionLocal
from sqlalchemy import inspect

print("🚀 Initializing SQLite database...")

with SessionLocal() as db:
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Quick sanity check
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"✅ Tables created: {tables}")
    
    # Test insert (will be overwritten on first real use)
    try:
        test_session = DBSession(
            id="init-test",
            strategy_text="Demo initialization",
            interpreted_strategy={"summary": "Init", "tags": [], "alignment_score": 50},
            decisions={},
            kpis={},
            competitor_event="",
            competitor_commentary="",
            executive_summary="Database ready",
            final_score=0.0
        )
        db.add(test_session)
        db.commit()
        print("✅ Test record inserted successfully")
    except Exception:
        print("⚠️  Test record skipped (already exists)")

print("✅ Database initialization complete!")
