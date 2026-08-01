import logging

def apply_hard_rules(row):
    """
    Evaluates deterministically hard rules prior to heuristic classification.
    Returns a dict or None.
    """
    if hasattr(row, 'to_dict'):
        data = row.to_dict()
    elif isinstance(row, dict):
        data = row
    else:
        data = {}
        
    full_text = " ".join([str(v) for v in data.values() if v is not None]).lower()
    
    if 'security alert' in full_text or 'unauthorized' in full_text or 'prod outage' in full_text:
        return {
            "action": "notify",
            "message_type": "security",
            "reason": "Critical security or production alert detected.",
            "confidence": 1.0,
            "evidence_message_ids": None
        }
        
    return None

def route_message_llm(row, context_data=None):
    """
    Robust rule-based local router.
    """
    try:
        if hasattr(row, 'to_dict'):
            data = row.to_dict()
        elif isinstance(row, dict):
            data = row
        else:
            data = {}
            
        full_text = " ".join([str(v) for v in data.values() if v is not None]).lower()
        
        # Keyword triggers
        urgent_keywords = [
            'urgent', 'asap', 'error', 'critical', 'failed', 'action required', 
            'immediately', 'deadline', 'bug', 'prod', 'outage', 'issue', 'help', 
            'review', 'deploy', 'blocker', 'alert', 'important', 'p0', 'p1', 
            'escalat', 'break', 'down', 'fail', 'fix', 'today', 'meeting', 'reminder'
        ]
        
        mute_keywords = [
            'thanks', 'thank you', 'ok', 'okay', 'cool', 'haha', 'lol', 
            'thumbs up', 'gm', 'gn', 'nice', 'got it', 'k', 'yep', 'great', 'sounds good'
        ]
        
        is_urgent = any(kw in full_text for kw in urgent_keywords)
        is_mute = any(kw in full_text for kw in mute_keywords)
        
        if is_urgent:
            action = 'notify'
            msg_type = 'urgent'
            confidence = 0.90
            reason = "High priority operational terms or urgent keywords detected."
        elif is_mute:
            action = 'mute'
            msg_type = 'low_priority'
            confidence = 0.85
            reason = "Casual acknowledgment or low priority chat message."
        else:
            action = 'digest'
            msg_type = 'general'
            confidence = 0.80
            reason = "Informational message scheduled for summary digest."

        return {
            "action": action,
            "message_type": msg_type,
            "reason": reason,
            "confidence": confidence,
            "evidence_message_ids": None
        }
    except Exception as e:
        logging.error(f"Error during classification: {e}")
        return {
            "action": "digest",
            "message_type": "general",
            "reason": f"Fallback error: {e}",
            "confidence": 0.5,
            "evidence_message_ids": None
        }