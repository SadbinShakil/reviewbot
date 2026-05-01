from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from models.database import Base


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    comment_id = Column(Integer, ForeignKey("bot_comments.id"), nullable=False)
    outcome = Column(String(20), nullable=False)  # accepted, dismissed, modified
    logged_at = Column(DateTime, default=datetime.utcnow)

    comment = relationship("BotComment", back_populates="feedback")
