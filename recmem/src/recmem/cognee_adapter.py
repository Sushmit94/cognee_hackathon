import cognee
from .config import COGNEE_DATASET
from .events import log_event

async def cognee_remember(text: str) -> dict:
    try:
        await cognee.add(text)
        await cognee.cognify()
        log_event("cognee_api_call", "remember() called", {"text_preview": text[:50]}, "layer_12")
        return {"success": True, "error": None}
    except Exception as e:
        log_event("cognee_api_call", "remember() FAILED", {"error": str(e)}, "layer_12")
        return {"success": False, "error": str(e)}


async def cognee_recall(query: str, mode: str = "GRAPH_COMPLETION") -> dict:
    try:
        result = await cognee.search(query_text=query, query_type=mode)
        log_event("cognee_api_call", "recall() called", {"query": query}, "layer_12")
        return {"success": True, "results": result, "error": None}
    except Exception as e:
        log_event("cognee_api_call", "recall() FAILED", {"error": str(e)}, "layer_12")
        return {"success": False, "results": [], "error": str(e)}