"""
subsidy_rules.py — Python port of frontend/src/data/subsidyRules.js.

⚠️ Keep this in sync with the frontend file manually -- there are two
independent copies (JS for the website, Python for the LINE bot) rather
than sharing one source, since they run in different languages. If you
update the subsidy numbers in one place (e.g. when 長照3.0 phases in),
update both.

最後查證日期 (last verified): 2026-07-26
"""

RULES_LAST_VERIFIED = "2026-07-26"

CMS_LEVEL_QUOTA = {
    2: 10020,
    3: 15460,
    4: 18580,
    5: 24100,
    6: 28070,
    7: 32090,
    8: 36180,
}

HOUSEHOLD_COPAY_RATE = {
    "low_income": {"label": "低收入戶", "rate": 0.0},
    "mid_low_income": {"label": "中低收入戶", "rate": 0.05},
    "general": {"label": "一般戶", "rate": 0.16},
}


def calculate_subsidy(cms_level: int, household_type: str):
    quota = CMS_LEVEL_QUOTA.get(cms_level)
    household = HOUSEHOLD_COPAY_RATE.get(household_type)
    if quota is None or household is None:
        return None

    self_pay = round(quota * household["rate"])
    gov_pay = quota - self_pay

    return {
        "quota": quota,
        "self_pay": self_pay,
        "gov_pay": gov_pay,
        "rate": household["rate"],
        "household_label": household["label"],
    }
