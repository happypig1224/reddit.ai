"""
De-AI Reddit Comment Generator
Implements strict lieflat-less-ai-tone standards:
- Eliminates AI contrast formulas (Not A but B)
- Eliminates colon conclusion announcements (Here is why:)
- Eliminates robotic corporate preambles
- Produces 3 distinct high-karma native Reddit comment personas
"""

import json
import re
from typing import List, Dict, Any, Optional

DE_AI_SYSTEM_PROMPT = """You are an experienced native Reddit user writing authentic, high-karma comments.
STRICT ANTI-AI GUIDELINES (FAILURE TO FOLLOW WILL RUIN THE ACCOUNT):
1. NO "Not X, but Y" or "It's not just about A, it's about B" framing.
2. NO colon conclusions or announcement phrases (e.g. "Here's the thing:", "The key takeaway:").
3. NO generic AI preambles (e.g. "To be fair,", "Honestly,", "At the end of the day,").
4. NO numbered lectures, no bullet lists, no corporate jargon.
5. Max 1-3 natural, punchy sentences per comment. Sound like a real person typing on a phone.

Return a JSON array of 3 distinct perspectives:
[
  {"tone": "生活经验", "text": "A personal, relatable experience or first-hand anecdote."},
  {"tone": "实用建议", "text": "A direct, pragmatic, actionable insight or contrarian tip."},
  {"tone": "幽默风趣", "text": "A witty, concise observation with high community resonance."}
]"""


class DeAIEngine:

    @classmethod
    def clean_ai_flavor(cls, text: str) -> str:
        """Post-process text to remove common AI residual markers"""
        # Remove "Not A, but B" in English
        text = re.sub(r"^(It'?s\s+not\s+(?:just\s+)?about\s+[^,]+,\s*(?:it'?s\s+about\s+)?)(.*)$", r"\2", text, flags=re.IGNORECASE)
        # Remove colon announcement starters
        text = re.sub(r"^(Here'?s\s+(?:the\s+thing|why|the\s+catch):\s*)", "", text, flags=re.IGNORECASE)
        text = re.sub(r"^(The\s+(?:key|bottom\s+line|truth)\s+is:\s*)", "", text, flags=re.IGNORECASE)
        text = re.sub(r"^(To\s+be\s+honest,\s*|Honestly,\s*|Frankly,\s*)", "", text, flags=re.IGNORECASE)
        # Remove quotes around entire comment
        text = text.strip().strip('"').strip("'")
        return text

    @classmethod
    def generate_contextual_drafts(cls, title: str, subreddit: str = "AskReddit") -> List[Dict[str, str]]:
        """
        Intelligent context-driven comment synthesizer
        Generates 3 top-tier native comments when LLM is offline or for instant responsiveness.
        """
        lower = title.lower()
        sub = subreddit.lower().replace("r/", "")

        # 1. Cooking / Food / Diet
        if any(w in lower for w in ["cook", "eat", "food", "kitchen", "meal", "grocery", "egg", "store"]):
            if "egg" in lower or "carton" in lower:
                return [
                    {"tone": "生活经验", "text": "I do this every single time, plus give each egg a slight wiggle. If it doesn't move, it's stuck to a cracked bottom."},
                    {"tone": "实用建议", "text": "It only takes one cracked egg glued to the cardboard ruining your groceries to make you check every carton for the rest of your life."},
                    {"tone": "幽默风趣", "text": "I open the carton, inspect them intently like a certified poultry inspector, and then buy the same carton anyway."}
                ]
            return [
                {"tone": "生活经验", "text": "Rotisserie chicken from Costco and bagged salad have unironically carried my household through the busiest weeks. Shred the meat, toss it in, dinner done in 5 minutes."},
                {"tone": "实用建议", "text": "An air fryer and a rice cooker are the actual cheat code here. Drop in seasoned sausages or chicken thighs for 15 minutes, cleanup is just one basket."},
                {"tone": "幽默风趣", "text": "A lot of 'snack plates' that are basically toddler charcuterie boards disguised as balanced nutrition."}
            ]

        # 2. Marriage / Relationship / Family
        if any(w in lower for w in ["husband", "wife", "marriage", "married", "relationship", "dating", "partner", "kid", "child"]):
            return [
                {"tone": "生活经验", "text": "Learning that 'listening' and 'fixing' are two completely different modes took me about five years of marriage to finally understand."},
                {"tone": "实用建议", "text": "Never assume silence means agreement or peace. A simple 'how was your headspace today' saves more headaches than any grand gesture."},
                {"tone": "幽默风趣", "text": "Deciding what to eat for dinner every single night for the next 50 years with zero hesitation."}
            ]

        # 3. Disappearing / Nostalgia / Society / Future
        if any(w in lower for w in ["disappear", "nostalgia", "miss", "future", "past", "2026", "opinion", "thoughts", "decade"]):
            return [
                {"tone": "生活经验", "text": "I genuinely miss being completely unreachable once you left the front door. Having a miniature office in your pocket at all times burned everyone out."},
                {"tone": "实用建议", "text": "Physical buttons in cars and home appliances. Touchscreens look futuristic in marketing photos but are an absolute hazard while driving 70 mph."},
                {"tone": "幽默风趣", "text": "Websites that let you read an article without demanding your email, cookie consent, and firstborn child."}
            ]

        # 4. Tech / Tools / Workflow / Programming
        if any(w in lower for w in ["tech", "tool", "workflow", "software", "code", "dev", "app", "linux", "ai"]):
            return [
                {"tone": "生活经验", "text": "Every time I tried building a complex custom setup, I ended up spending more time maintaining the tooling than doing actual work. Boring, proven tech always wins."},
                {"tone": "实用建议", "text": "Keep the initial architecture as lightweight as possible. Adding complexity when you actually need it is ten times easier than stripping out premature abstractions."},
                {"tone": "幽默风趣", "text": "The fastest code in production is the code you convinced your product manager not to build."}
            ]

        # 5. General AskReddit / Curiosity
        return [
            {"tone": "生活经验", "text": "Ran into this exact situation a few years back. The simplest fix turned out to be stepping back and doing nothing for 24 hours before making a call."},
            {"tone": "实用建议", "text": "Always look at the incentives behind why people behave this way. Once you see the payoff, the whole picture immediately makes sense."},
            {"tone": "幽默风趣", "text": "Nothing unites people faster than a mutual mild inconvenience that everyone quietly deals with."}
        ]

    @classmethod
    def parse_drafts(cls, raw: Optional[str], title: str = "") -> List[Dict[str, str]]:
        """Parses stored JSON drafts or falls back to clean contextual drafts"""
        if raw:
            try:
                data = json.loads(raw)
                if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict) and "text" in data[0]:
                    for d in data:
                        d["text"] = cls.clean_ai_flavor(d.get("text", ""))
                    return data
            except Exception:
                pass
            # If raw is a plain string, wrap it
            clean = cls.clean_ai_flavor(raw)
            if clean:
                return [{"tone": "推荐建议", "text": clean}]

        # Generate fresh drafts
        return cls.generate_contextual_drafts(title)
