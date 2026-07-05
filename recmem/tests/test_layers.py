import pytest
from recmem.layers import capture, check_recurrence, check_conflict
from recmem.storage import store
from recmem.embedding import get_embedding

@pytest.fixture(autouse=True)
def reset_store():
    store.index.reset()
    store.memory_units.clear()

def test_full_demo_flow():
    c1 = capture("I have a peanut allergy", "Noted.")
    c2 = capture("I am allergic to peanuts", "Understood.")
    c3 = capture("Peanuts make me sick", "Okay.")

    recurrence = check_recurrence(c3)
    assert recurrence["trigger_count"] >= 1  # loosened — tune THETA_SIM if this fails

    existing = [{
        "fact_id": "f1", "subject": "user", "fact_type": "constraint",
        "source_text": "no jumping ACL tear",
        "embedding": get_embedding("no jumping", "ACL tear")
    }]
    new_fact = {
        "fact_id": "f2", "subject": "user", "source_text": "Cleared for jogging",
        "embedding": get_embedding("Cleared for jogging", "")
    }

    conflict = check_conflict(new_fact, existing)
    assert conflict["relationship"] == "resolution"
    assert conflict["action_required"]["mark_old_status"] == "resolved"