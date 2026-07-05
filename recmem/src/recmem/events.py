event_log = []

def log_event(event_type: str, summary: str, details: dict, layer_source: str):
    event_log.append({
        "event_type": event_type,
        "summary": summary,
        "details": details,
        "layer_source": layer_source
    })