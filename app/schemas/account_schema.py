"""
Account DTO & VO Schemas
"""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class AccountVO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    clientId: str
    stage: str
    createdDaysAgo: int
    commentKarma: int
    linkKarma: int
    dailySentCount: int
    dailyLimit: int
    proxyUrl: Optional[str] = None
    isCoolingDown: bool
    cooldownRemainingSeconds: int = 0
    status: str


class AccountStageUpdateDTO(BaseModel):
    stage: str = Field(..., pattern="^(STAGE_1|STAGE_2|STAGE_3|STAGE_4)$")


class AccountCreateDTO(BaseModel):
    username: str = Field(..., min_length=2, max_length=64, description="Reddit 用户名 (如 u/your_name)")
    clientId: Optional[str] = Field(default="semi_auto_client", max_length=128, description="Reddit Script OAuth Client ID")
    clientSecret: Optional[str] = Field(default="semi_auto_secret", max_length=128, description="OAuth Client Secret 密钥")
    password: Optional[str] = Field(None, max_length=128, description="账号登录密码 (可选)")
    createdDaysAgo: int = Field(default=5, ge=0, le=3650, description="账号注册天数")
    proxyUrl: Optional[str] = Field(None, max_length=255, description="专属住宅代理 (如 socks5://127.0.0.1:10808)")


class AccountHandshakeVO(BaseModel):
    username: str
    commentKarma: int
    linkKarma: int
    isSuspended: bool
    hasVerifiedEmail: bool
    latencyMs: int
    message: str
    createdDaysAgo: Optional[int] = None
