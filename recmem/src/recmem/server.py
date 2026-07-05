from flask import Flask, jsonify, send_from_directory
from .events import event_log
from .storage import fact_store

app = Flask(__name__, static_folder='static')

cognee_call_counts = {"remember": 0, "recall": 0, "improve": 0, "forget": 0}

@app.route('/api/events')
def get_events():
    all_facts = list(fact_store.values())
    constraints = [f for f in all_facts if f.get("fact_type") == "constraint"]

    return jsonify({
        "events": event_log,
        "constraints": constraints,
        "facts_health": [{"id": f["fact_id"], "score": f.get("health_score", 0)} for f in all_facts],
        "cognee_calls": cognee_call_counts
    })

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)