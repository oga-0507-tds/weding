from typing import List, Optional
import streamlit as st

from service.venue_scraper_service import VenueScraperService
from service.cost_analyzer_service import CostAnalyzerService
from dto.wedding_dto import VenueDTO, CostSummaryDTO

class WeddingController:
    def __init__(self):
        self.venue_service = VenueScraperService()
        self.cost_service = CostAnalyzerService()

    def get_all_venues(self) -> List[VenueDTO]:
        """千葉県の式場一覧を取得する（Controller側で結果をキャッシュ）"""
        @st.cache_data(show_spinner="千葉県の結婚式場一覧を取得中...")
        def _cached_fetch():
            return self.venue_service.fetch_chiba_venues()
        
        return _cached_fetch()

    def analyze_venue_costs(
        self, 
        detail_url: str, 
        min_guests: int,  # target_people から min_guests に変更
        max_guests: int,  # max_guests を追加
        since_date: str, 
        cost_type: str
    ) -> CostSummaryDTO:
        """指定された式場と条件で費用明細を解析する"""
        @st.cache_data(show_spinner="費用明細を巡回・解析中（数分かかる場合があります）...")
        def _cached_analyze(url: str, min_g: int, max_g: int, date_str: str, type_str: str):
            # Service側の引数名に合わせてマッピング
            return self.cost_service.analyze_costs(
                detail_url=url,
                guests=None,          # 単一ピンポイントではなく範囲指定にするためNone
                min_guests=min_g,
                max_guests=max_g,
                date_str=date_str,
                visit_type=type_str   # Service側が visit_type という引数名になっているため合わせる
            )
            
        return _cached_analyze(detail_url, min_guests, max_guests, since_date, cost_type)