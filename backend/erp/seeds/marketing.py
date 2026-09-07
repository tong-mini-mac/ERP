"""Marketing campaigns: pre / present / post (present is mock for demo)."""

from __future__ import annotations

from typing import Any

CHANNELS = ["facebook", "line", "instagram", "tiktok", "email", "google"]


def build_marketing() -> dict[str, Any]:
    pre = []
    present = []
    post = []
    for i in range(50):
        ch = CHANNELS[i % len(CHANNELS)]
        pre.append(
            {
                "id": f"camp-pre-{i + 1:02d}",
                "name": f"Pre campaign #{i + 1:02d}",
                "product_name": f"Product line {i + 1}",
                "status": ["draft", "ready", "running"][i % 3],
                "channel": ch,
                "target_audience": "general consumers",
                "campaign_goal": "brand awareness",
                "budget": 5000 + i * 250,
            }
        )
        present.append(
            {
                "id": f"camp-present-{i + 1:02d}",
                "name": f"Live campaign #{i + 1:02d}",
                "status": ["live", "paused", "live"][i % 3],
                "channel": ch,
                "impressions": 1000 + i * 137,
                "clicks": 40 + i * 3,
                "spend": 800 + i * 45,
                "ctr": round(0.02 + (i % 10) * 0.002, 4),
            }
        )
        post.append(
            {
                "id": f"camp-post-{i + 1:02d}",
                "name": f"Post campaign review #{i + 1:02d}",
                "status": ["scheduled", "done", "review"][i % 3],
                "channel": ch,
                "sentiment": ["positive", "neutral", "mixed"][i % 3],
                "nps": 30 + (i % 50),
            }
        )
    return {
        "CAMPAIGNS_PRE": pre,
        "CAMPAIGNS_PRESENT": present,
        "CAMPAIGNS_POST": post,
        "ONBOARDING": {
            "completed": True,
            "items": [
                {"key": "shop", "label": "Configure ThaiTrade company", "done": True},
                {"key": "sku", "label": "Load 50 synthetic SKUs", "done": True},
                {"key": "warehouse", "label": "HQ + Asok warehouses", "done": True},
                {"key": "finance", "label": "Invoices + overdue scenarios", "done": True},
                {"key": "resto", "label": "Resto menus + ingredients", "done": True},
            ],
        },
    }
