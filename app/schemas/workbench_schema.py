"""
Workbench DTO & VO Schemas
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class CandidatePostVO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    redditPostId: str
    subreddit: str
    title: str
    content: Optional[str] = None
    permalink: Optional[str] = None
    score: int
    numComments: int
    upvoteRatio: float
    matchKeyword: str
    recommendedScore: int
    recommendedReason: str
    draftComment: Optional[str] = None
    drafts: Optional[List[Dict[str, Any]]] = None
    createdAgo: str
    status: str


class WorkbenchActionDTO(BaseModel):
    action: str = Field(..., description="APPROVE | SKIP | MANUAL_SENT")
    accountId: Optional[int] = Field(None, description="批复执行的账号ID")
    finalComment: Optional[str] = Field(None, description="人工确认的外发评论正文")
    customDelayMinutes: Optional[int] = Field(None, ge=1, le=120, description="自定义延迟(分钟)")


class WorkbenchActionResultVO(BaseModel):
    taskId: Optional[str] = None
    accountId: Optional[int] = None
    delaySeconds: Optional[int] = None
    scheduledAt: Optional[str] = None
    todaySentAfter: Optional[int] = None
    todayLimit: Optional[int] = None
    actionResult: str
