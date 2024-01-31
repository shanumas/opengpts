import uvicorn
from pathlib import Path
from pydantic import BaseModel

import orjson
from fastapi import FastAPI, Form, UploadFile
from fastapi.staticfiles import StaticFiles
from gizmo_agent import ingest_runnable
from flask import jsonify
from webhook import handle
from starlette.responses import JSONResponse

from app.api import router as api_router
import os

app = FastAPI(title="OpenGPTs API")

class WhatsAppMessage(BaseModel):
    object: str
    entry: list


# Get root of app, used to point to directory containing static files
ROOT = Path(__file__).parent.parent


app.include_router(api_router)


@app.post("/ingest", description="Upload files to the given assistant.")
def ingest_files(files: list[UploadFile], config: str = Form(...)) -> None:
    """Ingest a list of files."""
    config = orjson.loads(config)
    return ingest_runnable.batch([file.file for file in files], config)

@app.route("/webhook")
async def verify_webhook(request):
    """
    Handles the verification request for setting up the webhook.
    """
    print('Webhook get request received from meta')

    mode = request.query_params.get('hub.mode', None)
    token = request.query_params.get('hub.verify_token', None)
    challenge = request.query_params.get('hub.challenge', None)

    # Check if a token and mode were sent
    if mode and token:
        # Check the mode and token sent are correct
        if (token == "voiceflow"):
            # Respond with 200 OK and challenge token from the request
            print('WEBHOOK_VERIFIED')
            response_body = {"message": challenge}
            return JSONResponse(content=int(challenge), status_code=200)
        else:
            # Responds with '403 Forbidden' if verify tokens do not match
            raise HTTPException(status_code=403, detail="Forbidden: Verify tokens do not match")
    else:
        raise HTTPException(status_code=400, detail="Bad Request: Missing mode or token parameters")

@app.route("/webhook", methods=["POST"])
async def handle_webhook(request):
    return await handle(request)


#app.mount("", StaticFiles(directory=str(ROOT / "ui"), html=True), name="ui")
app.mount("", StaticFiles(directory=str(ROOT / "ui"), html=True), name="ui")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8100)
