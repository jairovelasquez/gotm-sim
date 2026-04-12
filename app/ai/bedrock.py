import json
import boto3
from botocore.exceptions import ClientError, BotoCoreError
from app.config import BEDROCK_MODEL
from app.models import InterpretedStrategy
from app.utils.fallback import fallback_interpret_strategy, fallback_executive_summary

def _invoke_model(prompt: str, system_prompt: str = None) -> str | None:
    """Low-level Bedrock invoke with error handling"""
    try:
        client = boto3.client("bedrock-runtime", region_name="us-east-1")
        
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 800,
            "temperature": 0.0,
            "top_p": 0.9,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        if system_prompt:
            body["system"] = system_prompt

        response = client.invoke_model(
            modelId=BEDROCK_MODEL,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(body)
        )
        
        response_body = json.loads(response["body"].read())
        return response_body["content"][0]["text"]
        
    except (ClientError, BotoCoreError, KeyError, json.JSONDecodeError) as e:
        print(f"⚠️ Bedrock invoke failed: {type(e).__name__} - {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error calling Bedrock: {e}")
        return None


def interpret_strategy(text: str) -> dict:
    """
    Uses Bedrock Claude 3 Haiku to interpret user strategy text.
    Falls back to deterministic keyword analysis if Bedrock fails.
    """
    if not text or len(text.strip()) < 10:
        return {**fallback_interpret_strategy(text or ""), "_fallback": True}

    system_prompt = "You are an expert Go-To-Market strategist for consumer wellness products."

    prompt = f"""Analyze this go-to-market strategy for VibeFuel (wellness beverage targeting Urban Gen Z):

{text}

Return **only** valid JSON with this exact structure:
{{
  "summary": "One clear sentence summarizing the strategy",
  "tags": ["tag1", "tag2", "tag3"],
  "alignment_score": 75
}}

Focus on awareness, pricing, channel, and segment alignment."""

    result = _invoke_model(prompt, system_prompt)

    if not result:
        print("⚠️ Using fallback strategy interpretation")
        return {**fallback_interpret_strategy(text), "_fallback": True}

    try:
        # Clean possible markdown code blocks
        cleaned = result.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        
        parsed = json.loads(cleaned.strip())
        validated = InterpretedStrategy(**parsed)
        return {**validated.model_dump(), "_fallback": False}
        
    except Exception as e:
        print(f"⚠️ JSON parsing failed from Bedrock: {e}")
        return {**fallback_interpret_strategy(text), "_fallback": True}


def generate_executive_summary(session_data: dict) -> str:
    """
    Generates final executive summary using Bedrock with fallback.
    """
    prompt = f"""Write a professional, concise 4-5 sentence executive summary for this VibeFuel product launch.

Strategy: {session_data.get('strategy_text', '')}
Decisions:
- Pricing: {session_data.get('decisions', {}).get('pricing', 'N/A')}
- Priority Segment: {session_data.get('decisions', {}).get('priority_segment', 'N/A')}
- Channel Mix: {session_data.get('decisions', {}).get('channel_mix', 'N/A')}

Final Score: {session_data.get('final_score', 0)}/100
Key Results: {json.dumps(session_data.get('kpis', {}), indent=2)}

Focus on strategic insights, strengths, and trade-offs. Write in a confident business tone."""

    result = _invoke_model(prompt)

    if not result:
        print("⚠️ Using fallback executive summary")
        return fallback_executive_summary(session_data)

    # Clean output
    cleaned = result.strip().replace("```", "").strip()
    return cleaned
