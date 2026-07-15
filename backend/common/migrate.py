import logging
from pathlib import Path

from common.database import engine

logger = logging.getLogger(__name__)

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def run_migrations() -> None:
    with engine.begin() as conn:
        for sql_file in sorted(MIGRATIONS_DIR.glob("*.sql")):
            conn.exec_driver_sql(sql_file.read_text())
            logger.info(f"Applied migration: {sql_file.name}")
