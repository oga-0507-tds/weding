import re
import time
from datetime import datetime
from typing import List, Optional, Set
import requests
from bs4 import BeautifulSoup
from dto.wedding_dto import CostSummaryDTO, CostDetailDTO


class CostAnalyzerService:

    def __init__(self):
        self.base_url = "https://www.mwed.jp"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def analyze_costs(
        self,
        detail_url: str,
        guests: Optional[int] = None,
        visit_type: str = "すべて",
        date_str: Optional[str] = None,
        min_guests: Optional[int] = None,
        max_guests: Optional[int] = None,
    ) -> CostSummaryDTO:
        """指定された式場の費用明細ページを巡回し、条件（人数・開始時期・区分）に合う明細を集計します。

        :param guests: 固定人数で絞り込む場合の人数（Noneなら制限なし）
        :param min_guests: 最小人数（Noneなら下限なし）
        :param max_guests: 最大人数（Noneなら上限なし）
        :param date_str: 絞り込みたい開始時期（例: "2025年3月" / "2026年"、Noneなら制限なし）
        :param visit_type: 区分（"本番" / "下見" / "すべて"）
        """
        if guests is not None and min_guests is None and max_guests is None:
            min_guests = guests
            max_guests = guests

        cost_base_url = self._normalize_to_cost_url(detail_url)

        # 基準となる日付をdatetime型に変換
        since_date = None
        if date_str:
            for fmt in ("%Y年%m月", "%Y年"):
                try:
                    since_date = datetime.strptime(date_str, fmt)
                    break
                except ValueError:
                    continue
            if since_date is None:
                print(
                    f"⚠️ 日付のパースに失敗しました: {date_str} (フォーマットは '2025年3月' または '2026年' 等にしてください)"
                )

        page = 1
        total_cost = 0
        match_count = 0
        details: List[CostDetailDTO] = []
        previous_page_urls: Set[str] = set()

        while True:
            soup = self._fetch_page_soup(cost_base_url, page)
            if not soup:
                break

            cost_items = soup.find_all("li", class_="clearfix")
            if not cost_items:
                break

            current_page_urls = self._extract_item_urls(cost_items)
            current_page_urls_set = set(current_page_urls)

            if (
                not current_page_urls_set
                or current_page_urls_set == previous_page_urls
            ):
                break

            for item in cost_items:
                # 修正：新条件（人数範囲・時期）に対応したパーサーを呼び出し
                cost_detail = self._parse_and_match_item(
                    item, min_guests, max_guests, since_date, visit_type
                )
                if cost_detail:
                    total_cost += cost_detail.amount
                    match_count += 1
                    details.append(cost_detail)

            previous_page_urls = current_page_urls_set
            page += 1
            time.sleep(1)

        average_cost = float(total_cost / match_count) if match_count > 0 else 0.0
        return CostSummaryDTO(
            average_cost=average_cost,
            matched_count=match_count,
            details=details,
        )

    def _normalize_to_cost_url(self, url: str) -> str:
        if not url.startswith("http"):
            url = f"{self.base_url.rstrip('/')}/{url.lstrip('/')}"
        if not url.endswith("/cost/") and not url.endswith("/cost"):
            url = url.rstrip("/") + "/cost/"
        if not url.endswith("/"):
            url += "/"
        return url

    def _fetch_page_soup(
        self, base_url: str, page: int
    ) -> Optional[BeautifulSoup]:
        if page == 1:
            target_url = base_url
        else:
            target_url = f"{base_url}?page={page}"

        try:
            response = requests.get(
                target_url, headers=self.headers, timeout=10
            )
            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.text, "html.parser")
            if "費用明細はまだ投稿されていません" in soup.get_text():
                return None

            return soup
        except requests.RequestException:
            return None

    def _get_item_url(self, item: BeautifulSoup) -> Optional[str]:
        item_link_tag = item.find("a", class_="js_place-activity-click")
        if not item_link_tag or not item_link_tag.get("href"):
            return None
        href = item_link_tag.get("href")
        return (
            f"{self.base_url}{href}" if not href.startswith("http") else href
        )

    def _extract_item_urls(self, cost_items: List[BeautifulSoup]) -> List[str]:
        urls = []
        for item in cost_items:
            if item.find("a", class_="js_place-activity-click") is None:
                continue
            url = self._get_item_url(item)
            if url:
                urls.append(url)
        return urls

    def _parse_and_match_item(
        self,
        item: BeautifulSoup,
        min_guests: Optional[int],
        max_guests: Optional[int],
        since_date: Optional[datetime],
        target_visit_type: str,
    ) -> Optional[CostDetailDTO]:
        """明細1件をパースし、指定された条件に合致すれば CostDetailDTO を返します。"""
        price_link_tag = item.find("a", class_="js_place-activity-click")
        if not price_link_tag:
            return None

        item_url = self._get_item_url(item)
        if not item_url:
            return None

        # 1. 区分の判定
        type_tag = item.find("div", class_="place-list-label-set__label")
        item_visit_type = type_tag.text.strip() if type_tag else ""
        if target_visit_type != "すべて" and target_visit_type != item_visit_type:
            return None

        # 2. 人数（範囲指定）の判定
        people_tag = price_link_tag.find_all(
            "span", class_="os1-symbol-numerical"
        )
        item_guests = None
        if len(people_tag) > 1:
            people_text = people_tag[1].text.strip()
            people_match = re.search(r"\d+", people_text)
            if people_match:
                item_guests = int(people_match.group())

        if item_guests is not None:
            if min_guests is not None and item_guests < min_guests:
                return None
            if max_guests is not None and item_guests > max_guests:
                return None
        else:
            if min_guests is not None or max_guests is not None:
                return None

        # 3. 時期（◯◯年◯月 以降）の判定
        date_tag = item.find("div", class_="fltR")
        item_date = None
        date_text = ""
        if date_tag:
            raw_text = date_tag.get_text(strip=True)
            date_match = re.search(r"(\d{4}年\d{1,2}月)", raw_text)
            if date_match:
                date_text = date_match.group(1)
                try:
                    item_date = datetime.strptime(date_text, "%Y年%m月")
                except ValueError:
                    pass

        if since_date:
            if item_date:
                if item_date < since_date:
                    return None
            else:
                return None

        # 4. 金額のパース
        price_tag = price_link_tag.find("span", class_="fontLL")
        if not price_tag:
            return None

        price_text = price_tag.text.strip()
        price_value = (
            int(re.sub(r"[^\d]", "", price_text))
            if re.sub(r"[^\d]", "", price_text)
            else 0
        )
        if price_value <= 0:
            return None

        return CostDetailDTO(
            amount=price_value,
            people_count=item_guests or 0,
            wedding_date=date_text,
            cost_type=item_visit_type,
            detail_url=item_url,
        )