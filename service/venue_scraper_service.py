import time
import logging
from typing import List, Optional
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from dataclasses import dataclass

@dataclass(frozen=True)
class VenueDTO:
    name: str
    detail_url: str  # 詳細URL（例: https://www.mwed.jp/hall/11674/）


class VenueScraperService:
    """みんなのウェディングから式場一覧を精密に取得・パースするサービス"""

    BASE_URL = "https://www.mwed.jp"
    CHIBA_VENUES_URL = f"{BASE_URL}/shikijo/shutoken/chiba/"

    def __init__(self, interval_seconds: float = 1.0):
        self.interval_seconds = interval_seconds
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # ブロック対策: ブラウザからのアクセスに見せかけるヘッダー
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def fetch_chiba_venues(self, max_pages: int = 50) -> List[VenueDTO]:
        """千葉県の結婚式場一覧を全ページ巡回して取得するメインメソッド"""
        all_venues: List[VenueDTO] = []
        seen_urls = set()  # 重複URLを完全にスキップするためのセット

        self.logger.info("件数のズレを修正した精密版で抽出中（重複は自動スキップ）...")

        for page in range(1, max_pages + 1):
            # 1ページ目はpageなし、2ページ目以降は /page2/ の形式
            url = self.CHIBA_VENUES_URL if page == 1 else f"{self.CHIBA_VENUES_URL}page{page}/"
            self.logger.info(f"{page}ページ目を読み込み中: {url}")

            # 1. HTMLの取得
            html = self._fetch_html(url)
            if not html:
                self.logger.warning(f"{page}ページ目が存在しないか、アクセスできませんでした。巡回を終了します。")
                break

            # 2. 1ページ分のパース処理
            soup = BeautifulSoup(html, "html.parser")
            # 広告枠やおすすめ枠を巻き込まないよう、本物の式場カード（liタグ）だけを厳密に指定
            cards = soup.select("li.renewal-2023-place-card")
            
            page_items_count = 0

            # 3. 各カードからデータを抽出
            for card in cards:
                # ① 広告・おすすめ枠（recommend）が混ざっていたらスキップ
                if "recommend" in "".join(card.get("class", [])):
                    continue

                venue_dto = self._extract_venue_data(card)
                if not venue_dto:
                    continue

                # ② すでに全ページを通して取得済みのURLなら完全にスキップ
                if venue_dto.detail_url in seen_urls:
                    continue

                # リストと重複チェック用セットに保存
                all_venues.append(venue_dto)
                seen_urls.add(venue_dto.detail_url)
                page_items_count += 1

            self.logger.info(f"-> {page}ページ目から {page_items_count} 件の新しい式場を追加しました。")

            # 4. 終了判定（新しいデータが1件も取れなくなったら最後のページと判断）
            if page_items_count == 0:
                self.logger.info("新しいデータが見つからなくなったため、抽出を終了します。")
                break

            time.sleep(self.interval_seconds)

        self.logger.info(f"\n【成功】重複を除いた 合計 {len(all_venues)} 件の式場データを取得しました！")
        return all_venues

    def _fetch_html(self, url: str) -> Optional[str]:
        """指定されたURLからHTMLテキストを取得する"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                return response.text
            return None
        except Exception as e:
            self.logger.error(f"リクエスト中にエラーが発生しました: {e}")
            return None

    def _extract_venue_data(self, card) -> Optional[VenueDTO]:
        """単一のカード要素（li）から式場名とURLを抽出し、VenueDTOを生成する"""
        try:
            # 1. 式場名が書かれているspanタグを精密に探す
            name_element = card.select_one(".renewal-2023-place-card-header-place-name__link, .renewal-2023-place-card-hpdl-header-place-name__link")
            if not name_element:
                return None
            name = name_element.text.strip()

            # 2. 詳細リンクが書かれているaタグを精密に探す
            link_element = card.select_one("a.renewal-2023-place-card-hpdl-header__link, a.renewal-2023-place-card-link-area")
            if not link_element:
                # バックアップとしてhallを含むaタグを探す
                link_element = card.select_one("a[href^='/hall/']")

            if not link_element:
                return None

            href = link_element.get("href", "").strip()
            if not name or not href:
                return None

            # 絶対URLに変換
            detail_url = urljoin(self.BASE_URL, href)

            return VenueDTO(name=name, detail_url=detail_url)

        except Exception as e:
            self.logger.debug(f"要素の抽出スキップ: {e}")
            return None