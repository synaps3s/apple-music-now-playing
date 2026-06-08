import os
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO  = os.getenv("GITHUB_REPO", "")   # format: "username/username"
SERVER_PORT  = int(os.getenv("SERVER_PORT", "8000"))
API_SECRET   = os.getenv("API_SECRET", "")
