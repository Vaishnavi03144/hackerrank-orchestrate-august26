import os
import pandas as pd
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel
from openai import OpenAI

class ActionEnum(str, Enum):
    NOTIFY = "notify"
    DIGEST = "digest"
    MUTE = "mute"

class PredictionOutput(BaseModel):
    action: ActionEnum
    message_type: str
    reason: str
    confidence: float
    evidence_message_ids: Optional[List[str]] = []

def apply_hard_rules(row) -> Optional[dict]:
    """Deterministically handles obvious scams or immediate safety risks."""
    text = str(row.get("text", "")).lower()
    
    scam_keywords = ["congratulations you won", "claim reward", "send otp immediately", "wire transfer money"]
    if any(k in text for k in scam_keywords):
        return {
            "action": "mute",
            "message_type": "scam",
            "reason": "High risk of scam or phishing detected.",
            "confidence": 0.99,
            "evidence_message_ids": [str(row.get("message_id"))]
        }
    return None

def route_message_llm(row, client=None) -> dict:
    if client is None:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    msg_id = str(row.get("message_id", ""))
    msg_text = row.get("text", "")
    conv_type = row.get("conversation_type", "personal")
    
    media_info = f"Media Type: {row.get('media_type', 'None')}"
    if 'ocr_text' in row and pd.notna(row['ocr_text']):
        media_info += f" | OCR Text: {row['ocr_text']}"
    if 'transcript' in row and pd.notna(row['transcript']):
        media_info += f" | Transcript: {row['transcript']}"

    prompt = f"""
    You are an intelligent WhatsApp Notification Router.

    Categorize this message into:
    - notify: Urgent time-sensitive alerts, personal/work direct questions, security OTPs.
    - digest: Useful non-urgent updates, group announcements, event notices, receipts, newsletters.
    - mute: Unsolicited marketing, repetitive ads, low-value automated notifications, spam, scams.

    Context:
    Message ID: {msg_id}
    Conversation Type: {conv_type}
    Text: {msg_text}
    Media Info: {media_info}
    """

    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format=PredictionOutput
    )

    result = response.choices[0].message.parsed
    return {
        "action": result.action.value,
        "message_type": result.message_type,
        "reason": result.reason,
        "confidence": result.confidence,
        "evidence_message_ids": result.evidence_message_ids if result.evidence_message_ids else []
    }