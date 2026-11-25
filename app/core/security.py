"""
Anti-Ban Static Defense & Risk Control Filters
Standards:
- Intercept any external URLs (http/https/domain suffixes)
- Intercept private contact info (wechat/whatsapp/telegram)
- Enforce length boundaries to avoid low-effort spam detection
- Dynamic custom blacklist verification
"""

import re
from typing import Tuple, List, Optional

# 严禁任何外部 URL
URL_PATTERN = re.compile(
    r'(https?://|www\.|(?:\w+\.)+(?:com|org|net|io|xyz|app|ai|me|top|cc|cn|co|uk|de|jp)\b)',
    re.IGNORECASE
)

# 严禁任何私域联系方式
CONTACT_PATTERN = re.compile(
    r'(t\.me|wa\.me|wechat|微信|whatsapp|telegram|v信|加v|vx|qq群|公众号|扫码|私聊我|pm me for link)',
    re.IGNORECASE
)

# 典型 AI 味公文套话模式
AI_CLICHE_PATTERN = re.compile(
    r'(in conclusion|it is worth noting|as an ai|as a large language model|hope this helps! feel free to|here are \d+ key points)',
    re.IGNORECASE
)


def validate_comment_safety(
    text: str, 
    custom_blacklist: Optional[List[str]] = None
) -> Tuple[bool, str]:
    """
    静态风控校验：坚决阻断外链、联系方式及违规营销词
    Returns: (is_safe: bool, reason: str)
    """
    if not text or len(text.strip()) == 0:
        return False, "评论内容不能为空"

    cleaned_text = text.strip()

    # 1. 外链阻断 (Anti-Ban 物理铁律 #1)
    if URL_PATTERN.search(cleaned_text):
        return False, "拦截原因：评论内容严禁包含任何外部链接 (URL)！"

    # 2. 私域导流阻断 (Anti-Ban 物理铁律 #2)
    if CONTACT_PATTERN.search(cleaned_text):
        return False, "拦截原因：评论内容严禁包含私域联系方式 (微信/Telegram/WhatsApp/QQ)！"

    # 3. 极短内容拦截 (防止被 Reddit 判定为 Low Effort Spam)
    if len(cleaned_text) < 8:
        return False, "拦截原因：评论过短 (少于8字)，极易被 Reddit 垃圾过滤器标记！"

    # 4. 动态黑名单词库校验
    if custom_blacklist:
        lower_text = cleaned_text.lower()
        for kw in custom_blacklist:
            if kw and kw.lower() in lower_text:
                return False, f"拦截原因：命中了风控黑名单关键词 '{kw}'"

    # 5. 典型 AI 腔调检查（软性警告，不直接阻断但建议去AI味）
    if AI_CLICHE_PATTERN.search(cleaned_text):
        return False, "拦截原因：检测到明显的 AI 模板套话特征 (如 As an AI / In conclusion)，不符合拟真人口吻标准！"

    return True, "安全合规"

