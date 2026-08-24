
from __future__ import annotations
"""
line_flex.py — LINE Flex Message builders for the result display.

Visual language matches the website (frontend/src/components/EasyCard.jsx
etc): deep teal for trust/headers, warm amber for the key highlighted
number, sage-tinted neutrals for secondary text. Keeping this in one file
separate from line_bot.py's conversation logic so the visual design can be
iterated on independently of the state machine.
"""

from linebot.v3.messaging import (
    FlexMessage, FlexBubble, FlexBox, FlexText, FlexButton,
    FlexSeparator, FlexCarousel, URIAction,
)

TEAL = "#1B4B43"
AMBER = "#E8A33D"
INK = "#232323"
INK_MUTED = "#8A8A8A"
PAPER = "#FAF7F2"


def build_subsidy_flex(result: dict) -> FlexMessage:
    """The subsidy result as a single styled card, mirroring the
    website's EasyCard + ResultCard components."""
    bubble = FlexBubble(
        size="mega",
        header=FlexBox(
            layout="vertical",
            background_color=TEAL,
            padding_all="20px",
            contents=[
                FlexText(text="長照給付試算結果", color="#FFFFFF", weight="bold", size="md"),
                FlexText(text=f"身分別：{result['household_label']}", color="#FFFFFF", size="sm", margin="sm"),
            ],
        ),
        body=FlexBox(
            layout="vertical",
            background_color=PAPER,
            padding_all="20px",
            spacing="md",
            contents=[
                FlexText(text="每月給付額度上限", color=INK_MUTED, size="sm"),
                FlexText(
                    text=f"NT$ {result['quota']:,}",
                    color=AMBER, weight="bold", size="3xl",
                ),
                FlexSeparator(margin="md"),
                FlexBox(
                    layout="horizontal",
                    margin="md",
                    contents=[
                        FlexText(text="政府補助", color=INK, size="sm", flex=1),
                        FlexText(
                            text=f"NT$ {result['gov_pay']:,}",
                            color=TEAL, weight="bold", size="md", align="end", flex=1,
                        ),
                    ],
                ),
                FlexBox(
                    layout="horizontal",
                    contents=[
                        FlexText(text="家庭自付額（約）", color=INK, size="sm", flex=1),
                        FlexText(
                            text=f"NT$ {result['self_pay']:,}",
                            color=AMBER, weight="bold", size="md", align="end", flex=1,
                        ),
                    ],
                ),
                FlexSeparator(margin="md"),
                FlexText(
                    text="⚠️ 這只是試算，不是核定結果。實際額度由照顧管理專員評估後核定，"
                         "請撥打長照專線 1966（免費）預約評估。",
                    color=INK_MUTED, size="xs", wrap=True, margin="md",
                ),
            ],
        ),
    )
    return FlexMessage(alt_text=f"長照給付試算結果：每月額度 NT$ {result['quota']:,}", contents=bubble)


def _facility_bubble(facility: dict) -> FlexBubble:
    body_contents = [
        FlexText(text=facility["name"], weight="bold", size="md", color=INK, wrap=True),
        FlexText(text=facility["address"], color=INK_MUTED, size="sm", wrap=True, margin="sm"),
    ]
    if facility.get("geocode_precision") == "district":
        body_contents.append(
            FlexText(text="⚠ 約略位置，實際地點請以電話確認", color=AMBER, size="xxs", wrap=True, margin="sm")
        )

    footer = None
    phone = facility.get("phone")
    if phone:
        # Facility phone numbers sometimes include extensions like
        # "03-1234567#123" or multiple numbers separated by newlines --
        # only the first clean number is usable in a tel: link.
        clean_phone = phone.split("#")[0].split("\n")[0].strip()
        footer = FlexBox(
            layout="vertical",
            padding_all="12px",
            contents=[
                FlexButton(
                    action=URIAction(label=f"📞 撥打 {clean_phone}", uri=f"tel:{clean_phone}"),
                    style="primary",
                    color=TEAL,
                    height="sm",
                )
            ],
        )

    return FlexBubble(
        size="kilo",
        body=FlexBox(layout="vertical", padding_all="16px", contents=body_contents, background_color=PAPER),
        footer=footer,
    )


def build_facilities_flex(district: str, facilities: list[dict]) -> FlexMessage:
    """Facility results as a swipeable carousel -- LINE allows up to 12
    bubbles per carousel, which comfortably covers our top-10 result cap."""
    bubbles = [_facility_bubble(f) for f in facilities[:10]]
    carousel = FlexCarousel(contents=bubbles)
    return FlexMessage(alt_text=f"{district}區日間照顧中心，共 {len(facilities)} 筆", contents=carousel)
