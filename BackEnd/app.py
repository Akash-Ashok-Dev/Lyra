# app.py
# ---------------------------------
# Flask backend that hides your Google API key and returns
# a clean JSON playlist for a public Google Drive folder.
#
# Env vars required:
#   GOOGLE_API_KEY = <your Google API key>
#   ALLOWED_ORIGIN = https://<your-gh-username>.github.io (or *)
#
# Run locally:
#   pip install -r requirements.txt
#   export GOOGLE_API_KEY=... (or use a .env file; see below)
#   python app.py
#
# Deploy anywhere (Render, Railway, Fly.io, etc.).
# Restrict your API key in Google Cloud to your server's IP/domain later.

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests

app = Flask(__name__)

ALLOWED_ORIGIN = os.getenv("ALLOWED_ORIGIN", "*")
CORS(app, resources={r"/api/*": {"origins": ALLOWED_ORIGIN}})

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
DRIVE_API = "https://www.googleapis.com/drive/v3/files"

if not GOOGLE_API_KEY:
    raise RuntimeError(
        "GOOGLE_API_KEY not set. Set it in your environment or .env file.")


def build_query(folder_id: str, audio_only: bool = True) -> str:
    # Folder children, not trashed. Optionally filter to audio mime types.
    base = f"'{folder_id}' in parents and trashed = false"
    if audio_only:
        # Matches audio/mpeg, audio/ogg, audio/wav, audio/x-m4a, etc.
        base += " and mimeType contains 'audio/'"
    return base


def make_direct_link(file_id: str) -> str:
    # Direct-ish download URL that streams fine in <audio>
    return f"https://drive.google.com/uc?export=download&id={file_id}"


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/files")
def list_files():
    """
    Query params:
      - folderId (required): Google Drive folder ID
      - audioOnly (optional, default true): 'true'|'false'
      - pageToken (optional): for manual pagination
    Returns: { files: [ {id, name, mimeType, size, modifiedTime, url, icon, thumbnail} ], nextPageToken }
    """
    folder_id = request.args.get("folderId")
    if not folder_id:
        return jsonify({"error": "Missing folderId query param"}), 400

    audio_only = request.args.get("audioOnly", "true").lower() != "false"
    page_token = request.args.get("pageToken")

    params = {
        "key": GOOGLE_API_KEY,
        "q": build_query(folder_id, audio_only),
        "pageSize": 1000,
        "fields": "nextPageToken, files(id,name,mimeType,size,modifiedTime,thumbnailLink,iconLink)",
        # Support both My Drive and Shared Drives if the folder lives there
        "supportsAllDrives": True,
        "includeItemsFromAllDrives": True,
        # Order newest first (optional):
        "orderBy": "modifiedTime desc",
    }

    if page_token:
        params["pageToken"] = page_token

    try:
        r = requests.get(DRIVE_API, params=params, timeout=20)
        r.raise_for_status()
    except requests.RequestException as e:
        return jsonify({"error": "Drive API request failed", "details": str(e)}), 502

    data = r.json()
    files = data.get("files", [])

    # Map into a frontend-friendly shape
    out = []
    for f in files:
        out.append({
            "id": f.get("id"),
            "name": f.get("name"),
            "mimeType": f.get("mimeType"),
            "size": f.get("size"),
            "modifiedTime": f.get("modifiedTime"),
            "thumbnail": f.get("thumbnailLink"),
            "icon": f.get("iconLink"),
            "url": make_direct_link(f.get("id")),
        })

    return jsonify({
        "files": out,
        "nextPageToken": data.get("nextPageToken")
    })


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
