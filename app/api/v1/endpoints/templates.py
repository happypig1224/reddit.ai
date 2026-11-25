"""
Templates Endpoints
"""

from typing import List
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import now_utc
from app.db.session import get_db
from app.models.comment_template import CommentTemplate
from app.models.risk_setting import RiskSetting
from app.schemas.response import ApiResponse
from app.schemas.template_schema import TemplateVO, TemplateCreateDTO
from app.core.security import validate_comment_safety

router = APIRouter()


@router.get("", response_model=ApiResponse[List[TemplateVO]])
async def get_templates(db: AsyncSession = Depends(get_db)):
    """获取所有评论模板（附带24小时去重冷却标记）"""
    result = await db.execute(select(CommentTemplate).order_by(CommentTemplate.id.asc()))
    templates = result.scalars().all()

    now = now_utc()
    twenty_four_hours_ago = now - timedelta(hours=24)

    vo_list = []
    for t in templates:
        is_cooling = False
        if t.last_used_at and t.last_used_at > twenty_four_hours_ago:
            is_cooling = True

        vo_list.append(TemplateVO(
            id=t.id,
            tone=t.tone,
            templateText=t.template_text,
            isActive=t.is_active,
            usageCount=t.usage_count,
            lastUsedAt=t.last_used_at.isoformat() if t.last_used_at else None,
            isCoolingDown=is_cooling
        ))
    return ApiResponse.success(data=vo_list)


@router.post("", response_model=ApiResponse[TemplateVO])
async def create_template(dto: TemplateCreateDTO, db: AsyncSession = Depends(get_db)):
    """新增评论模板 (强制校验外链与私域导流违禁词)"""
    risk_res = await db.execute(select(RiskSetting).where(RiskSetting.id == 1))
    risk_setting = risk_res.scalar_one_or_none()
    custom_blacklist = risk_setting.sensitive_keywords if risk_setting else []

    is_safe, reason = validate_comment_safety(dto.templateText, custom_blacklist)
    if not is_safe:
        raise HTTPException(status_code=400, detail=reason)

    new_tmpl = CommentTemplate(
        tone=dto.tone,
        template_text=dto.templateText.strip(),
        is_active=True
    )
    db.add(new_tmpl)
    await db.commit()
    await db.refresh(new_tmpl)

    return ApiResponse.success(
        data=TemplateVO(
            id=new_tmpl.id,
            tone=new_tmpl.tone,
            templateText=new_tmpl.template_text,
            isActive=new_tmpl.is_active,
            usageCount=new_tmpl.usage_count,
            lastUsedAt=None,
            isCoolingDown=False
        ),
        message="新模板已通过风控合规校验并入库"
    )


@router.delete("/{id}", response_model=ApiResponse[None])
async def delete_template(id: int, db: AsyncSession = Depends(get_db)):
    """删除停用模板"""
    res = await db.execute(select(CommentTemplate).where(CommentTemplate.id == id))
    tmpl = res.scalar_one_or_none()
    if not tmpl:
        raise HTTPException(status_code=404, detail="模板不存在")

    await db.delete(tmpl)
    await db.commit()
    return ApiResponse.success(message="模板已删除")
