
from __future__ import annotations
"""
line_bot.py — LINE Messaging API webhook + conversation logic.

Design note: `process_event()` is a pure-ish function (its only side
effects are reading facility data / computing subsidy, both deterministic
given the same inputs) that takes the current session state and an
incoming event, and returns (new_state, list_of_reply_messages). This is
kept separate from the actual webhook route and LINE API calls so the
conversation logic itself can be unit-tested without touching the network
or a real LINE account -- same pattern used for the sync service's diff
logic.
"""

import os
from urllib.parse import parse_qs

from fastapi import APIRouter, Request, HTTPException, Header
from linebot.v3 import WebhookParser
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi, ReplyMessageRequest,
    TextMessage, QuickReply, QuickReplyItem, PostbackAction,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent, PostbackEvent, FollowEvent

from line_session import get_session, set_session, clear_session
from line_flex import build_subsidy_flex, build_facilities_flex
from subsidy_rules import CMS_LEVEL_QUOTA, HOUSEHOLD_COPAY_RATE, calculate_subsidy
from facilities_service import search_facilities

import logging

logger = logging.getLogger("line_bot")

router = APIRouter()

CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")

IDENTITY_OPTIONS = [
    ("elderly_65", "65歲以上長者"),
    ("aboriginal_55", "55歲以上原住民"),
    ("disabled", "領有身心障礙證明"),
    ("not_sure", "不確定/尚未評估"),
]

HOUSEHOLD_OPTIONS = [(key, val["label"]) for key, val in HOUSEHOLD_COPAY_RATE.items()]

DISTRICTS = ["桃園", "中壢", "八德", "楊梅", "平鎮", "龜山", "蘆竹", "大園", "龍潭", "大溪", "新屋", "觀音"]


# ---------- Quick reply message builders ----------

def _quick_reply_message(text: str, options: list[tuple[str, str]], step: str) -> TextMessage:
    items = [
        QuickReplyItem(
            action=PostbackAction(
                label=label,
                data=f"step={step}&value={value}",
                display_text=label,
            )
        )
        for value, label in options
    ]
    return TextMessage(text=text, quick_reply=QuickReply(items=items))


def build_identity_message() -> TextMessage:
    return _quick_reply_message("請問是為誰試算長照給付呢？", IDENTITY_OPTIONS, "identity")


def build_cms_message() -> TextMessage:
    options = [(str(level), f"第{level}級") for level in CMS_LEVEL_QUOTA]
    return _quick_reply_message(
        "失能需要等級（CMS）大約是幾級呢？\n"
        "（此等級由照顧管理專員到府評估後核定，若尚未評估可先選擇預估等級）",
        options, "cms",
    )


def build_household_message() -> TextMessage:
    return _quick_reply_message("家庭經濟狀況（身分別）是？", HOUSEHOLD_OPTIONS, "household")


def build_district_message() -> TextMessage:
    options = [(d, d) for d in DISTRICTS]
    return _quick_reply_message("您在桃園市的哪個行政區呢？", options, "district")


def build_result_messages(cms_level: int, household_type: str, district: str) -> list:
    result = calculate_subsidy(cms_level, household_type)
    messages = [build_subsidy_flex(result)]

    facilities = search_facilities(district=district, only_active=True, limit=10)
    if not facilities:
        messages.append(TextMessage(text=f"{district}區目前沒有符合條件的日照中心資料"))
    else:
        messages.append(build_facilities_flex(district, facilities))

    messages.append(TextMessage(text="輸入任意訊息可重新開始試算 🔄"))
    return messages


# ---------- Core state machine (testable without the network) ----------

def process_follow_or_text() -> tuple[dict, list[TextMessage]]:
    """A new follow, or any free-text message, resets and starts the flow."""
    new_state = {"step": "identity"}
    return new_state, [
        TextMessage(text="歡迎使用桃園長照導航！讓我們開始試算長照給付額度 🙂"),
        build_identity_message(),
    ]


def process_postback(data: str, state: dict) -> tuple[dict, list[TextMessage]]:
    parsed = parse_qs(data)
    step = parsed.get("step", [None])[0]
    value = parsed.get("value", [None])[0]

    if step == "identity" and value:
        new_state = {**state, "step": "cms", "identity": value}
        return new_state, [build_cms_message()]

    if step == "cms" and value:
        new_state = {**state, "step": "household", "cms_level": int(value)}
        return new_state, [build_household_message()]

    if step == "household" and value:
        new_state = {**state, "step": "district", "household_type": value}
        return new_state, [build_district_message()]

    if step == "district" and value:
        cms_level = state.get("cms_level")
        household_type = state.get("household_type")
        if cms_level is None or household_type is None:
            # Session got out of sync (e.g. server restarted mid-flow) --
            # restart cleanly rather than crashing on a KeyError.
            return process_follow_or_text()
        messages = build_result_messages(cms_level, household_type, value)
        return {}, messages

    # Unrecognized postback -- restart rather than silently doing nothing
    return process_follow_or_text()


# ---------- Webhook route ----------

@router.post("/line/webhook")
async def line_webhook(request: Request, x_line_signature: str = Header(None)):
    if not CHANNEL_SECRET or not CHANNEL_ACCESS_TOKEN:
        raise HTTPException(status_code=500, detail="LINE credentials not configured on server")

    body = (await request.body()).decode("utf-8")
    parser = WebhookParser(CHANNEL_SECRET)

    try:
        events = parser.parse(body, x_line_signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    config = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
    with ApiClient(config) as api_client:
        messaging_api = MessagingApi(api_client)

        for event in events:
            try:
                user_id = event.source.user_id
                reply_token = event.reply_token

                if isinstance(event, FollowEvent):
                    new_state, messages = process_follow_or_text()
                elif isinstance(event, MessageEvent) and isinstance(event.message, TextMessageContent):
                    new_state, messages = process_follow_or_text()
                elif isinstance(event, PostbackEvent):
                    current_state = get_session(user_id)
                    new_state, messages = process_postback(event.postback.data, current_state)
                else:
                    continue  # ignore event types we don't handle (stickers, images, etc.)

                set_session(user_id, new_state)
                messaging_api.reply_message(
                    ReplyMessageRequest(reply_token=reply_token, messages=messages)
                )
            except Exception:
                # LINE requires a 200 response regardless of what happens
                # processing an individual event -- e.g. the Developers
                # Console's "Verify" button sends test events with dummy
                # reply tokens that will always fail to actually reply to.
                # Repeated non-200 responses can cause LINE to disable the
                # webhook, so one bad event must never break the response
                # to the whole request.
                logger.exception("Failed to process LINE event, continuing")

    return {"status": "ok"}
