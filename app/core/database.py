import json

from sqlalchemy import create_engine
from sqlalchemy import inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.constants import ENV


DATABASE_URL = ENV.DATABASE_URL

# postgres:// -> postgresql:// fix
DATABASE_URL = DATABASE_URL.replace(
    "postgres://",
    "postgresql://",
    1
)

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300
    )

# print(f"Connected to database: {DATABASE_URL}")

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

# Models import
import app.model  # loads ALL models 

# ✅ Create all tables in DB
Base.metadata.create_all(bind=engine)


def migrate_sqlite_schema():
    if engine.dialect.name != "sqlite":
        return

    inspector = inspect(engine)
    if "user_settings" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("user_settings")}

    with engine.begin() as connection:
        if "two_factor" not in columns:
            connection.execute(text("ALTER TABLE user_settings ADD COLUMN two_factor JSON"))

        if "totp_secret" in columns:
            rows = connection.execute(
                text(
                    """
                    SELECT user_id, totp_secret
                    FROM user_settings
                    WHERE totp_secret IS NOT NULL
                      AND totp_secret != ''
                      AND two_factor IS NULL
                    """
                )
            ).mappings().all()

            for row in rows:
                connection.execute(
                    text("UPDATE user_settings SET two_factor = :two_factor WHERE user_id = :user_id"),
                    {
                        "two_factor": json.dumps({"totp": row["totp_secret"]}),
                        "user_id": row["user_id"]
                    }
                )


migrate_sqlite_schema()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
