from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from models.database import Base


class PullRequest(Base):
    __tablename__ = "pull_requests"

    id = Column(Integer, primary_key=True, index=True)
    repo_full_name = Column(Text, nullable=False)
    pr_number = Column(Integer, nullable=False)
    title = Column(Text)
    author = Column(Text)
    status = Column(String(50), default="pending")
    head_sha = Column(Text)
    base_sha = Column(Text)
    pr_url = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)

    comments = relationship("BotComment", back_populates="pull_request")
