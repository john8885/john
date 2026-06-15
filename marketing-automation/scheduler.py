"""APScheduler 기반 자동화 스케줄러"""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from config import TIMEZONE

logger = logging.getLogger(__name__)


def task_weekly_ad_report():
    """매주 월요일 오전 9시 — 광고 리포트 수집 후 이메일 발송."""
    from automation.ad_report import build_weekly_report
    from automation.email_sender import send_email
    try:
        report = build_weekly_report()
        meta = report.get("meta", {})
        body = f"""
        <h2>주간 광고 리포트 ({report['period']})</h2>
        <h3>Meta (인스타그램/페이스북)</h3>
        <ul>
          <li>지출: ₩{meta.get('spend', 0):,.0f}</li>
          <li>노출: {meta.get('impressions', 0):,}</li>
          <li>클릭: {meta.get('clicks', 0):,}</li>
          <li>CTR: {meta.get('ctr', 0):.2f}%</li>
          <li>전환: {meta.get('conversions', 0)}</li>
        </ul>
        """
        send_email(
            to=["report@yourcompany.com"],   # 수신자 설정
            subject=f"[광고 리포트] {report['period']}",
            body_html=body,
        )
        logger.info("Weekly ad report sent")
    except Exception as e:
        logger.error("Weekly ad report failed: %s", e)


def task_crawl_trends():
    """매일 오전 8시 — 네이버 트렌드 키워드 수집."""
    from automation.crawler import crawl_naver_trending
    try:
        keywords = crawl_naver_trending()
        logger.info("Trend keywords: %s", keywords[:5])
        # 필요 시 DB 저장 또는 슬랙/이메일 알림 추가
    except Exception as e:
        logger.error("Trend crawl failed: %s", e)


def create_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone=TIMEZONE)

    # 매주 월요일 09:00 — 광고 리포트
    scheduler.add_job(
        task_weekly_ad_report,
        CronTrigger(day_of_week="mon", hour=9, minute=0, timezone=TIMEZONE),
        id="weekly_ad_report",
        replace_existing=True,
    )

    # 매일 08:00 — 트렌드 크롤링
    scheduler.add_job(
        task_crawl_trends,
        CronTrigger(hour=8, minute=0, timezone=TIMEZONE),
        id="daily_trend_crawl",
        replace_existing=True,
    )

    return scheduler
