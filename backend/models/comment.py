from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from models.database import Base


class BotComment(Base):
    __tablename__ = "bot_comments"

    id = Column(Integer, primary_key=True, index=True)
    pr_id = Column(Integer, ForeignKey("pull_requests.id"), nullable=False)
    github_comment_id = Column(BigInteger, unique=True, nullable=True)
    file_path = Column(Text, nullable=False)
    line_number = Column(Integer, nullable=False)
    severity = Column(String(20), nullable=False)  # critical, warning, suggestion
    category = Column(String(30), nullable=False)  # bug, security, performance, style, testing
    comment_text = Column(Text, nullable=False)
    suggestion = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    pull_request = relationship("PullRequest", back_populates="comments")
    feedback = relationship("Feedback", back_populates="comment", uselist=False)
