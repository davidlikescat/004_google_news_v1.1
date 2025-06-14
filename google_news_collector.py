# google_news_collector.py - Google News 최신 AI 기사 수집
import requests
from datetime import datetime, timedelta
import time
import re
from urllib.parse import quote
from bs4 import BeautifulSoup
import feedparser
import logging

logger = logging.getLogger(__name__)

class GoogleNewsCollector:
    """Google News에서 최신 AI 기사를 수집하는 클래스"""
    
    def __init__(self, max_articles=5):
        self.max_articles = max_articles
        self.base_url = "https://news.google.com/rss/search"
        self.session = requests.Session()
        
        # User-Agent 설정 (Google News 접근용)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/rss+xml,application/xml,text/xml,*/*',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        })
    
    def build_search_query(self, keywords):
        """키워드 기반 검색 쿼리 생성"""
        # 핵심 AI 키워드만 사용 (최신성 우선)
        core_keywords = [
            '인공지능', 'AI', '생성형AI', 'ChatGPT', 'LLM', 
            '머신러닝', '딥러닝', 'GPT', '자율주행', 'AI반도체'
        ]
        
        # OR 연산자로 키워드 연결
        query_parts = []
        for keyword in core_keywords[:5]:  # 상위 5개만 사용
            query_parts.append(f'"{keyword}"')
        
        search_query = ' OR '.join(query_parts)
        
        # 한국 기사 우선, 최근 24시간 이내
        search_query += ' when:1d'  # 최근 1일 이내
        
        return search_query
    
    def collect_latest_news(self, keywords):
        """Google News에서 최신 AI 뉴스 수집"""
        print(f"🔍 Google News에서 최신 AI 뉴스 검색 중...")
        
        search_query = self.build_search_query(keywords)
        encoded_query = quote(search_query)
        
        # Google News RSS URL 구성
        rss_url = f"{self.base_url}?q={encoded_query}&hl=ko&gl=KR&ceid=KR:ko"
        
        print(f"📡 검색 URL: {rss_url}")
        
        try:
            # RSS 피드 파싱
            response = self.session.get(rss_url, timeout=30)
            response.raise_for_status()
            
            # feedparser로 RSS 파싱
            feed = feedparser.parse(response.content)
            
            if not feed.entries:
                print("⚠️ Google News에서 검색 결과가 없습니다.")
                return []
            
            articles = []
            processed_count = 0
            
            print(f"📰 {len(feed.entries)}개 기사 발견, 최대 {self.max_articles}개 수집...")
            
            for entry in feed.entries:
                if processed_count >= self.max_articles:
                    break
                
                try:
                    # 기사 정보 추출
                    article = self.extract_article_info(entry)
                    
                    if article and self.is_ai_related(article, keywords):
                        articles.append(article)
                        processed_count += 1
                        print(f"✅ [{processed_count}] {article['title'][:50]}...")
                    
                    # 요청 간 딜레이
                    time.sleep(0.5)
                    
                except Exception as e:
                    logger.warning(f"기사 처리 중 오류: {e}")
                    continue
            
            print(f"🎯 총 {len(articles)}개 AI 관련 최신 기사 수집 완료")
            return articles
            
        except Exception as e:
            logger.error(f"Google News 수집 실패: {e}")
            print(f"❌ Google News 수집 실패: {e}")
            return []
    
    def extract_article_info(self, entry):
        """RSS entry에서 기사 정보 추출"""
        try:
            # Google News URL에서 실제 기사 URL 추출
            original_url = self.extract_original_url(entry.link)
            
            # 발행 시간 파싱
            published_time = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published_time = datetime(*entry.published_parsed[:6])
            else:
                published_time = datetime.now()
            
            # 출처 추출
            source = "Unknown"
            if hasattr(entry, 'source') and entry.source:
                source = entry.source.get('title', 'Unknown')
            
            article = {
                'title': entry.title,
                'url': original_url or entry.link,
                'published': published_time,
                'source': source,
                'summary': getattr(entry, 'summary', '')[:200],
                'content': '',  # 나중에 크롤링으로 채움
                'keywords': [],
                'category': '최신 AI 뉴스'
            }
            
            return article
            
        except Exception as e:
            logger.warning(f"기사 정보 추출 실패: {e}")
            return None
    
    def extract_original_url(self, google_news_url):
        """Google News URL에서 원본 기사 URL 추출"""
        try:
            # Google News 리다이렉트 URL 처리
            if 'news.google.com' in google_news_url:
                # URL 파라미터에서 실제 URL 찾기
                if 'url=' in google_news_url:
                    import urllib.parse as urlparse
                    parsed = urlparse.urlparse(google_news_url)
                    params = urlparse.parse_qs(parsed.query)
                    if 'url' in params:
                        return params['url'][0]
                
                # 다른 방법으로 실제 URL 추출 시도
                response = self.session.head(google_news_url, allow_redirects=True, timeout=10)
                return response.url
            
            return google_news_url
            
        except Exception as e:
            logger.warning(f"원본 URL 추출 실패: {e}")
            return google_news_url
    
    def is_ai_related(self, article, keywords):
        """기사가 AI 관련인지 확인"""
        text_to_check = f"{article['title']} {article['summary']}".lower()
        
        # 핵심 AI 키워드 체크
        ai_keywords = [
            '인공지능', 'ai', '생성형ai', 'chatgpt', 'gpt', 'llm',
            '머신러닝', '딥러닝', '신경망', '자율주행', 'ai반도체',
            '네이버', '카카오', '삼성ai', '클로바'
        ]
        
        for keyword in ai_keywords:
            if keyword.lower() in text_to_check:
                return True
        
        return False
    
    def filter_recent_articles(self, articles, hours=24):
        """최근 시간 내 기사만 필터링"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_articles = []
        
        for article in articles:
            if article['published'] >= cutoff_time:
                recent_articles.append(article)
        
        # 최신순으로 정렬
        recent_articles.sort(key=lambda x: x['published'], reverse=True)
        
        print(f"📅 최근 {hours}시간 이내 기사: {len(recent_articles)}개")
        return recent_articles[:self.max_articles]

def test_google_news_collector():
    """Google News 수집기 테스트"""
    print("🧪 Google News 수집기 테스트")
    print("=" * 40)
    
    from config import Config
    
    collector = GoogleNewsCollector(max_articles=3)
    articles = collector.collect_latest_news(Config.AI_KEYWORDS)
    
    if articles:
        print(f"\n✅ {len(articles)}개 기사 수집 성공:")
        for i, article in enumerate(articles, 1):
            print(f"{i}. {article['title']}")
            print(f"   출처: {article['source']}")
            print(f"   발행: {article['published'].strftime('%Y-%m-%d %H:%M')}")
            print(f"   URL: {article['url']}")
            print()
    else:
        print("❌ 기사 수집 실패")

if __name__ == "__main__":
    test_google_news_collector()