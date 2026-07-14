from fastapi import APIRouter

router = APIRouter()


@router.get("/ping")
def ping():
    """
    Simplest possible endpoint. If this responds, your server,
    routing, and environment are all working correctly.
    Every future endpoint (ask a doubt, upload a PDF, etc.)
    gets added below this in the same file, or in new files
    under api/ as the project grows.
    """
    return {"status": "ok", "message": "pong"}
