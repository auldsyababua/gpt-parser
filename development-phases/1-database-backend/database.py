"""Database connection and session management."""

import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost/gpt_parser"
)

# For Supabase, the URL format is:
# postgresql://postgres.[project-ref]:[password]@[region].pooler.supabase.com:6543/postgres
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if SUPABASE_URL:
    # Extract database URL from Supabase URL if provided
    # Supabase provides the database URL separately
    DATABASE_URL = os.getenv("SUPABASE_DB_URL", DATABASE_URL)

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,  # Verify connections before using
    echo=False,  # Set to True for SQL query logging
)

# Create session factory
SessionLocal = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)


class DatabaseManager:
    """Database manager for handling connections and transactions."""

    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal

    @contextmanager
    def get_session(self):
        """Provide a transactional scope for database operations."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def create_tables(self):
        """Create all tables in the database."""
        from models import Base

        Base.metadata.create_all(bind=self.engine)

    def drop_tables(self):
        """Drop all tables in the database."""
        from models import Base

        Base.metadata.drop_all(bind=self.engine)

    def init_db(self):
        """Initialize database with tables and seed data."""
        self.create_tables()
        self._seed_initial_data()

    def _seed_initial_data(self):
        """Seed initial data for users and sites."""
        from models import User, Site

        with self.get_session() as session:
            # Check if data already exists
            if session.query(User).count() > 0:
                return

            # Create default users
            users = [
                User(
                    telegram_id="123456789",
                    telegram_username="colin_10netzero",
                    display_name="Colin",
                    timezone="America/Los_Angeles",
                    role="admin",
                ),
                User(
                    telegram_id="987654321",
                    telegram_username="bryan_10netzero",
                    display_name="Bryan",
                    timezone="America/Chicago",
                    role="operator",
                ),
                User(
                    telegram_id="456789123",
                    telegram_username="joel_10netzero",
                    display_name="Joel",
                    timezone="America/Chicago",
                    role="operator",
                ),
            ]

            # Create default sites
            sites = [
                Site(name="Site A", location="Location A"),
                Site(name="Site B", location="Location B"),
                Site(name="Site C", location="Location C"),
                Site(name="Site D", location="Location D"),
            ]

            session.add_all(users)
            session.add_all(sites)
            session.commit()
            print("Initial data seeded successfully.")


# Global database manager instance
db_manager = DatabaseManager()


# Dependency for FastAPI or other frameworks
def get_db():
    """Dependency to get database session."""
    with db_manager.get_session() as session:
        yield session
