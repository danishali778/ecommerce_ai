import os

from app.core.settings import get_settings


os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://user:pass@localhost:5432/postgres")
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "anon")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "service")

get_settings.cache_clear()
