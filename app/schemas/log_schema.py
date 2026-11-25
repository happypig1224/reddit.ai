"""
Audit Log DTO & VO Schemas
"""

from typing import Optional
from pydantic import BaseModel, ConfigDict


class AuditLogVO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    accountUsername: str
    subreddit: str
    redditPostId: str
    postTitle: str
    redditCommentId: Optional[str] = None
    commentSnippet: str
    delaySeconds: int
    status: str
    shadowbanStatus: str
    shadowbanCheckedAt: Optional[str] = None
    createdAt: str


class ProbeResultVO(BaseModel):
    logId: int
    redditCommentId: Optional[str] = None
    previousStatus: str
    newStatus: str
    message: str
