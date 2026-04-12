from pydantic import BaseModel
from typing import Dict, List, Literal, Optional
from datetime import datetime
from enum import Enum

class Pricing(str, Enum):
    premium = "premium"
    competitive = "competitive"
    intro_offer = "intro_offer"
    value_led = "value_led"

class PrioritySegment(str, Enum):
    genz_trend_seekers = "genz_trend_seekers"
    value_buyers = "value_buyers"
    premium_lifestyle = "premium_lifestyle"
    early_adopters = "early_adopters"

class ChannelMix(str, Enum):
    social_first = "social_first"
    influencer_led = "influencer_led"
    retail_activation = "retail_activation"
    balanced_mix = "balanced_mix"

class Decisions(BaseModel):
    pricing: Pricing
    priority_segment: PrioritySegment
    channel_mix: ChannelMix

class StrategyInput(BaseModel):
    strategy_text: str

class InterpretedStrategy(BaseModel):
    summary: str
    tags: List[str]
    alignment_score: int

class KPIResult(BaseModel):
    awareness: float
    cac: float
    conversion: float
    sales: float
    roas: float
    marketShare: float
    launchEfficiency: float
    final_score: float

class SimulationStage(BaseModel):
    stage: int
    stage_name: str
    kpis: Dict[str, float]
    narrative: str
    competitor: Optional[Dict] = None

class SessionDB(BaseModel):
    id: str
    created_at: datetime
    strategy_text: str
    interpreted_strategy: Dict
    decisions: Dict
    kpis: Dict
    competitor_event: str
    competitor_commentary: str
    executive_summary: str
    final_score: float
    report_md: Optional[str] = None
    report_html: Optional[str] = None
    ai_fallback: bool = False
