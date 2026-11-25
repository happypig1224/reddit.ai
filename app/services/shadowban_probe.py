"""
Shadowban Probe Service (Anonymous Public Endpoint Checker)
Compliant with reddit-karma-pilot skill standards
"""

import httpx
from typing import Tuple


class ShadowbanProbeService:
    """使用未登录匿名独立请求探测发出的评论是否对公众真实可见"""

    @classmethod
    async def probe_comment(cls, subreddit: str, post_id: str, comment_id: str) -> Tuple[str, str]:
        """
        Returns: (status: VERIFIED_PUBLIC | SHADOWBANNED | DELETED | PENDING, message: str)
        """
        if not comment_id:
            return "PENDING", "无评论ID，无法探测"

        clean_sub = subreddit.replace("r/", "").strip()
        clean_post = post_id.replace("t3_", "").strip()
        clean_comment = comment_id.replace("t1_", "").strip()

        # 如果是本地 Mock 评论 ID
        if clean_comment.startswith("m89") or "test" in clean_comment.lower():
            return "VERIFIED_PUBLIC", "[Mock 存活探测] 评论已公开收录，AutoModerator 未拦截"

        url = f"https://www.reddit.com/r/{clean_sub}/comments/{clean_post}/_/{clean_comment}.json"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        }

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 404:
                    return "SHADOWBANNED", "公开接口返回 404，评论或账号处于隐形封禁 (Shadowban) 状态！"

                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, list) and len(data) > 1:
                        comments = data[1].get("data", {}).get("children", [])
                        if not comments:
                            return "DELETED", "评论列表为空，可能已被版主机器人删除"
                        body = comments[0].get("data", {}).get("body", "")
                        if body in ["[removed]", "[deleted]"]:
                            return "DELETED", f"评论已被标记为 {body}，触发版主过滤规则"
                        return "VERIFIED_PUBLIC", "评论公开可见且处于存活状态"
                
                return "PENDING", f"探测响应状态码: {resp.status_code}"
        except Exception as e:
            return "PENDING", f"匿名探测网络波动: {str(e)}"

