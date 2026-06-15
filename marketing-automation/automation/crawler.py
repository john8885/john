"""데이터 수집 / 크롤링"""
import logging
import time
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def fetch_html(url: str, retries: int = 3, delay: float = 1.5) -> BeautifulSoup | None:
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            return BeautifulSoup(resp.text, "html.parser")
        except Exception as e:
            logger.warning("fetch_html attempt %d failed for %s: %s", attempt + 1, url, e)
            time.sleep(delay * (attempt + 1))
    return None


def crawl_competitor_prices(urls: list[str]) -> list[dict]:
    """경쟁사 상품 URL 목록에서 이름·가격을 추출."""
    results = []
    for url in urls:
        soup = fetch_html(url)
        if soup is None:
            results.append({"url": url, "error": "fetch_failed"})
            continue
        # 범용 추출 — 사이트마다 셀렉터 조정 필요
        name_tag = soup.select_one("h1") or soup.select_one('[class*="product-title"]')
        price_tag = (
            soup.select_one('[class*="price"]')
            or soup.select_one('[itemprop="price"]')
        )
        results.append({
            "url": url,
            "name": name_tag.get_text(strip=True) if name_tag else None,
            "price": price_tag.get_text(strip=True) if price_tag else None,
        })
        time.sleep(1)
    logger.info("Crawled %d URLs", len(results))
    return results


def crawl_keywords(keyword: str, pages: int = 2) -> list[dict]:
    """네이버 쇼핑 키워드 검색 결과 수집."""
    items: list[dict] = []
    for page in range(1, pages + 1):
        url = f"https://search.shopping.naver.com/search/all?query={keyword}&pagingIndex={page}"
        soup = fetch_html(url)
        if soup is None:
            break
        for tag in soup.select('[class*="product_title"]'):
            items.append({"keyword": keyword, "title": tag.get_text(strip=True)})
        time.sleep(1.5)
    logger.info("Keyword '%s': collected %d items", keyword, len(items))
    return items


def crawl_naver_trending() -> list[str]:
    """네이버 실시간 트렌드 키워드 수집."""
    url = "https://datalab.naver.com/keyword/realtimeList.naver"
    soup = fetch_html(url)
    if soup is None:
        return []
    keywords = [tag.get_text(strip=True) for tag in soup.select(".item_title")]
    return keywords[:20]
