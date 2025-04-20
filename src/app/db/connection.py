from sqlalchemy import create_engine, text
from app.config import DATABASE_URL


def get_engine():
    """Create and return a SQLAlchemy engine connected to the PostgreSQL database"""
    return create_engine(DATABASE_URL)


def verify_extensions():
    """Verify that required PostgreSQL extensions (vector and AGE) are available and enabled"""
    engine = get_engine()
    with engine.connect() as conn:
        # Check vector extension
        vector_result = conn.execute(
            text("SELECT * FROM pg_extension WHERE extname = 'vector'")
        ).fetchone()
        # Check AGE extension
        age_result = conn.execute(
            text("SELECT * FROM pg_extension WHERE extname = 'age'")
        ).fetchone()

        extensions_status = {"vector": bool(vector_result), "age": bool(age_result)}

        if not vector_result or not age_result:
            missing = []
            if not vector_result:
                missing.append("vector")
            if not age_result:
                missing.append("age")
            raise RuntimeError(
                f"Required PostgreSQL extensions are not enabled: {', '.join(missing)}"
            )

        return extensions_status
