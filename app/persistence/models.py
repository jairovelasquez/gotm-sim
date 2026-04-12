from sqlalchemy import create_engine, Column, String, Text, JSON, Float, Boolean, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from app.config import DB_PATH

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
Base = declarative_base()

class DBSession(Base):
    __tablename__ = "sessions"
    id = Column(String, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    strategy_text = Column(Text)
    interpreted_strategy = Column(JSON)
    decisions = Column(JSON)
    kpis = Column(JSON)
    competitor_event = Column(String)
    competitor_commentary = Column(Text)
    executive_summary = Column(Text)
    final_score = Column(Float)
    report_md = Column(String)
    report_html = Column(String)
    ai_fallback = Column(Boolean, default=False)

Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)