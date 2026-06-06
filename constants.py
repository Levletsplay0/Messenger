import os
from pathlib import Path

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://myuser:mypass@localhost:5432/mydb")
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
MAX_FILE_SIZE = 5_242_880  # 5 МБ в байтах
USER_AVATARS_DIR = Path("static/avatars/users")
GROUP_AVATARS_DIR = Path("static/avatars/groups")
MESSAGE_FILES_DIR = Path("static/files/messages")