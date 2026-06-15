"""광고 리포트 수집 — Meta Ads + (확장 가능: Google Ads)"""
import logging
from datetime import date, timedelta
import requests
from config import META_ACCESS_TOKEN, META_AD_ACCOUNT_ID

logger = logging.getLogger(__name__)
META_GRAPH_URL = "https://graph.facebook.com/v19.0"


# ─── Meta (Facebook / Instagram) ────────────────────────────────────────────

def _meta_get(endpoint: str, params: dict) -> dict:
    params["access_token"] = META_ACCESS_TOKEN
    resp = requests.get(f"{META_GRAPH_URL}/{endpoint}", params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def get_meta_campaign_insights(
    since: date | None = None,
    until: date | None = None,
    level: str = "campaign",        # campaign / adset / ad
) -> list[dict]:
    """Meta 광고 캠페인 성과 데이터 수집."""
    since = since or (date.today() - timedelta(days=7))
    until = until or date.today()

    params = {
        "fields": "campaign_name,adset_name,ad_name,impressions,clicks,spend,ctr,cpc,reach,frequency,actions",
        "level": level,
        "time_range": f'{{"since":"{since}","until":"{until}"}}',
        "limit": 500,
    }
    data = _meta_get(f"{META_AD_ACCOUNT_ID}/insights", params)
    rows = data.get("data", [])
    logger.info("Meta insights: %d rows (level=%s)", len(rows), level)
    return rows


def get_meta_summary(since: date | None = None, until: date | None = None) -> dict:
    """지출·노출·클릭·전환 합계 요약."""
    rows = get_meta_campaign_insights(since, until, level="account")
    if not rows:
        return {}
    row = rows[0]
    conversions = sum(
        int(a["value"])
        for a in row.get("actions", [])
        if a["action_type"] in ("purchase", "lead", "complete_registration")
    )
    return {
        "spend": float(row.get("spend", 0)),
        "impressions": int(row.get("impressions", 0)),
        "clicks": int(row.get("clicks", 0)),
        "ctr": float(row.get("ctr", 0)),
        "cpc": float(row.get("cpc", 0)),
        "reach": int(row.get("reach", 0)),
        "conversions": conversions,
        "since": str(since or date.today() - timedelta(days=7)),
        "until": str(until or date.today()),
    }


# ─── 통합 리포트 ─────────────────────────────────────────────────────────────

def build_weekly_report() -> dict:
    """지난 7일 통합 광고 리포트 딕셔너리 반환."""
    since = date.today() - timedelta(days=7)
    until = date.today()
    meta = get_meta_summary(since, until)
    return {
        "period": f"{since} ~ {until}",
        "meta": meta,
        # Google Ads 연동은 google-ads 라이브러리 설정 후 추가
    }
