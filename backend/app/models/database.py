from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    Float,
    ForeignKey,
    DateTime,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime

from app.config import settings

Base = declarative_base()
engine = create_engine(settings.database_url, echo=settings.debug)
SessionLocal = sessionmaker(bind=engine)


def init_db():
    """Create all tables."""
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(engine)


def get_db():
    """Dependency for FastAPI routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Models ──────────────────────────────────────────────


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dept = Column(String(10), nullable=False)
    number = Column(String(20), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    prerequisites = Column(Text)
    instructors = Column(Text)
    quarters = Column(String(50))
    units = Column(String(10))

    mentions = relationship("CourseMention", back_populates="course")


class Major(Base):
    __tablename__ = "majors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    department = Column(String(100))
    type = Column(String(10))  # 'major' or 'minor'
    description = Column(Text)

    requirements = relationship("MajorRequirement", back_populates="major")


class MajorRequirement(Base):
    __tablename__ = "major_requirements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    major_id = Column(Integer, ForeignKey("majors.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"))
    requirement_type = Column(String(20))  # 'core', 'elective'
    sequence_order = Column(Integer)
    description = Column(Text)

    major = relationship("Major", back_populates="requirements")
    course = relationship("Course")


class RedditPost(Base):
    __tablename__ = "reddit_posts"

    id = Column(String(20), primary_key=True)
    subreddit = Column(String(50), nullable=False)
    title = Column(String(500))
    body = Column(Text)
    score = Column(Integer, default=0)
    date = Column(DateTime, default=datetime.utcnow)
    url = Column(String(500))

    comments = relationship("RedditComment", back_populates="post")


class RedditComment(Base):
    __tablename__ = "reddit_comments"

    id = Column(String(20), primary_key=True)
    post_id = Column(String(20), ForeignKey("reddit_posts.id"), nullable=False)
    body = Column(Text)
    score = Column(Integer, default=0)
    date = Column(DateTime, default=datetime.utcnow)

    post = relationship("RedditPost", back_populates="comments")


class CourseMention(Base):
    __tablename__ = "course_mentions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    reddit_id = Column(String(20), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"))
    sentiment = Column(Float)

    course = relationship("Course", back_populates="mentions")


class ProfessorMention(Base):
    __tablename__ = "professor_mentions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    reddit_id = Column(String(20), nullable=False)
    professor_name = Column(String(200))
    sentiment = Column(Float)


class CareerListing(Base):
    __tablename__ = "career_listings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    employer = Column(String(200))
    type = Column(String(20))  # 'job', 'internship', 'grad_school'
    description = Column(Text)
    url = Column(String(500))
    date = Column(DateTime, default=datetime.utcnow)
