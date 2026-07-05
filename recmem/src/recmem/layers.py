import uuid
import numpy as np
from .embedding import get_embedding
from .storage import store, fact_store
from .utils import call_llm
from .config import (
    THETA_SIM, THETA_COUNT, K_NEIGHBORS,
    SIMILARITY_WINDOW_MIN, SIMILARITY_WINDOW_MAX,
    RESOLUTION_TRIGGERS, HEALTH_PENALTY_CONFLICT, HEALTH_REPAIR_THRESHOLD
)
from .events import log_event


def capture(user_msg: str, assistant_msg: str) -> dict:
    if store.memory_units:
        last_id = list(store.memory_units.keys())[-1]
        last = store.memory_units[last_id]
        if last["user_msg"] == user_msg and last["assistant_msg"] == assistant_msg:
            return last

    unit_id = str(uuid.uuid4())
    embedding = get_embedding(user_msg, assistant_msg)
    unit = {"id": unit_id, "user_msg": user_msg, "assistant_msg": assistant_msg, "embedding": embedding}
    store.add(unit_id, embedding, unit)
    log_event("memory_captured", f"Captured: {user_msg[:50]}", {"id": unit_id}, "layer_1")
    return unit


def check_recurrence(unit: dict) -> dict:
    neighbors = store.query(unit["embedding"], k=K_NEIGHBORS)
    similar = [n for n in neighbors if n["id"] != unit["id"] and n["similarity"] >= THETA_SIM]
    result = {
        "should_consolidate": len(similar) >= THETA_COUNT,
        "similar_units": similar,
        "trigger_count": len(similar),
        "unit_id": unit["id"]
    }
    if result["should_consolidate"]:
        log_event("recurrence_triggered", f"{len(similar)} similar mentions found", {}, "layer_2")
    return result


def cosine_sim(a, b):
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def check_conflict(new_fact: dict, existing_facts: list[dict]) -> dict:
    candidates = []
    for f in existing_facts:
        if f["subject"] == new_fact["subject"] and f["fact_id"] != new_fact["fact_id"]:
            sim = cosine_sim(new_fact["embedding"], f["embedding"])
            if SIMILARITY_WINDOW_MIN <= sim <= SIMILARITY_WINDOW_MAX:
                candidates.append({**f, "similarity": sim})

    candidates.sort(key=lambda x: x.get("timestamp", 0), reverse=True)

    relationship, method, conflicting_fact_id = "independent", "none", None

    if candidates:
        candidate = candidates[0]
        if any(t in new_fact.get("source_text", "").lower() for t in RESOLUTION_TRIGGERS) \
           and candidate["fact_type"] == "constraint":
            relationship, method, conflicting_fact_id = "resolution", "keyword_fastpath", candidate["fact_id"]
        else:
            prompt = (
                f"Existing fact: {candidate.get('source_text','')}\n"
                f"New fact: {new_fact.get('source_text','')}\n"
                f"Classify relationship as CONTRADICTION, RESOLUTION, or INDEPENDENT. Output ONLY one word."
            )
            llm_response = call_llm(prompt)
            relationship = llm_response.strip().lower()
            method, conflicting_fact_id = "llm_classification", candidate["fact_id"]

    result = {
        "relationship": relationship,
        "conflicting_fact_id": conflicting_fact_id,
        "method": method,
        "action_required": {
            "mark_old_status": "stale" if relationship == "contradiction"
            else ("resolved" if relationship == "resolution" else None)
        }
    }
    if relationship != "independent":
        log_event("conflict_detected", f"Detected: {relationship}", {"method": method}, "layer_6")
    return result


def compute_health(fact_id: str, worth: float, retention: float, conflict_result: dict = None) -> dict:
    penalty = HEALTH_PENALTY_CONFLICT if conflict_result and conflict_result["relationship"] in ("contradiction", "resolution") else 0
    health = (0.5 * worth) + (0.5 * retention) - penalty
    score = max(0, min(100, health * 100))

    if conflict_result:
        rel = conflict_result.get("relationship")
        repair_action = "mark_stale" if rel == "contradiction" else ("mark_resolved" if rel == "resolution" else "none")
    else:
        repair_action = "mark_archived" if score < HEALTH_REPAIR_THRESHOLD else "none"

    return {
        "fact_id": fact_id,
        "health_score": score,
        "needs_repair": repair_action != "none",
        "repair_action": repair_action
    }


def apply_repair(fact_id: str, repair_action: str, resolved_by_unit_id: str = None) -> dict:
    if repair_action == "none":
        return fact_store[fact_id]
    if repair_action not in ["mark_stale", "mark_resolved", "mark_archived"]:
        raise ValueError(f"Unknown repair_action: {repair_action}")

    fact = fact_store[fact_id]
    if repair_action == "mark_stale":
        fact["status"] = "stale"
    elif repair_action == "mark_resolved":
        fact["status"] = "resolved"
        fact["resolved_by_unit_id"] = resolved_by_unit_id
    elif repair_action == "mark_archived":
        fact["status"] = "archived"

    log_event("repair_applied", f"Action: {repair_action}", {"fact_id": fact_id}, "layer_7")
    return fact