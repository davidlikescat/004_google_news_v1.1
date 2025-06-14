import requests
from bs4 import BeautifulSoup
import time
import logging
from urllib.parse import urljoin, urlparse
import re
from config import Config

class ArticleCrawler:
    """기사 본문 크롤링 클래스"""
    
    def __init__(self):
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        
        # 세션 설정
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.config.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # 통계 정보
        self.stats = {
            'total_attempts': 0,
            'successful_crawls': 0,
            'failed_crawls': 0,
            'fallback_used': 0
        }
        
        # 사이트별 본문 선택자 (사이트 최적화)
        self.content_selectors = {
            'aitimes.com': ['.article-content', '.news-content', 'article'],
            'techcrunch.com': ['.entry-content', '.article-content'],
            'zdnet.co.kr': ['.view_con', '.article_view', '.news-content'],
            'chosun.com': ['.news_text', '.article_view', '.news-content'],
            'dt.co.kr': ['.article-content', '.view-con', '.news-content'],
            'etnews.com': ['.article_txt', '.news-content', '.article-content'],
            'hankyung.com': ['.article-content', '.news-content'],
            'mk.co.kr': ['.news_detail_text', '.article-content']
        }
        
        # 제거할 요소들
        self.remove_selectors = [
            'script', 'style', 'nav', 'header', 'footer', 'aside',
            '.advertisement', '.ad', '.ads', '.social-share',
            '.related-articles', '.comment', '.navigation',
            '.breadcrumb', '.tag', '.share', '.print'
        ]
    
    def crawl_articles(self, articles):
        """기사 목록 크롤링"""
        self.logger.info(f"기사 본문 크롤링 시작: {len(articles)}개")
        
        crawled_articles = []
        self.stats['total_attempts'] = len(articles)
        
        for i, article in enumerate(articles, 1):
            try:
                print(f"📄 기사 크롤링 중... ({i}/{len(articles)}) - {article['title'][:50]}...")
                
                content, images = self._extract_content(article['link'])
                
                # 크롤링 결과 저장
                article['content'] = content
                article['images'] = images
                article['content_length'] = len(content)
                article['crawl_status'] = 'success' if content else 'failed'
                article['crawled_at'] = time.time()
                
                crawled_articles.append(article)
                
                if content:
                    self.stats['successful_crawls'] += 1
                    self.logger.info(f"크롤링 성공: {article['title'][:50]}... ({len(content)}자)")
                else:
                    self.stats['failed_crawls'] += 1
                    self.logger.warning(f"크롤링 실패: {article['title'][:50]}...")
                
                # 요청 간격
                time.sleep(self.config.REQUEST_DELAY)
                
            except Exception as e:
                self.stats['failed_crawls'] += 1
                self.logger.error(f"크롤링 오류 - {article['title']}: {e}")
                
                # 실패시 요약으로 대체
                article['content'] = article.get('summary', '')
                article['images'] = []
                article['content_length'] = len(article['content'])
                article['crawl_status'] = 'error'
                article['crawled_at'] = time.time()
                
                crawled_articles.append(article)
        
        self._print_statistics()
        return crawled_articles
    
    def _extract_content(self, url):
        """웹페이지에서 본문 추출"""
        try:
            # HTTP 요청
            response = self.session.get(url, timeout=self.config.TIMEOUT)
            response.raise_for_status()
            
            # 인코딩 설정
            if response.encoding.lower() in ['iso-8859-1', 'ascii']:
                response.encoding = 'utf-8'
            
            # BeautifulSoup으로 파싱
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 본문 추출
            content = self._extract_main_content(soup, url)
            
            # 이미지 추출
            images = self._extract_images(soup, url)
            
            return content, images
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"HTTP 요청 실패 ({url}): {e}")
            return "", []
        except Exception as e:
            self.logger.error(f"컨텐츠 추출 실패 ({url}): {e}")
            return "", []
    
    def _extract_main_content(self, soup, url):
        """메인 컨텐츠 추출"""
        # 사이트별 최적화된 선택자 사용
        domain = urlparse(url).netloc.lower()
        
        selectors = []
        for site_domain, site_selectors in self.content_selectors.items():
            if site_domain in domain:
                selectors = site_selectors
                break
        
        # 기본 선택자 추가
        if not selectors:
            selectors = [
                'article', '.article-content', '.news-content', '.post-content',
                '.entry-content', '#content', '.article-body', '.news-body',
                '.content', '.main-content', '.article', '.post'
            ]
        
        # 선택자별로 컨텐츠 추출 시도
        for selector in selectors:
            content_element = soup.select_one(selector)
            if content_element:
                content = self._clean_content(content_element)
                if len(content) > 200:  # 최소 길이 체크
                    return content
        
        # 폴백: p 태그들 수집
        paragraphs = soup.find_all('p')
        if paragraphs:
            self.stats['fallback_used'] += 1
            content = ' '.join([p.get_text(strip=True) for p in paragraphs])
            return self._clean_text(content)
        
        # 최후의 수단: body 텍스트
        body = soup.find('body')
        if body:
            return self._clean_text(body.get_text()[:1000])
        
        return ""
    
    def _clean_content(self, element):
        """컨텐츠 정리"""
        # 불필요한 요소 제거
        for selector in self.remove_selectors:
            for tag in element.select(selector):
                tag.decompose()
        
        # 텍스트 추출
        text = element.get_text(separator=' ', strip=True)
        
        # 텍스트 정리
        return self._clean_text(text)
    
    def _clean_text(self, text):
        """텍스트 정리"""
        if not text:
            return ""
        
        # 연속된 공백 제거
        text = re.sub(r'\s+', ' ', text)
        
        # 특수 문자 정리
        text = text.replace('\u200b', '')  # Zero width space
        text = text.replace('\ufeff', '')  # BOM
        
        # HTML 엔티티 디코딩
        import html
        text = html.unescape(text)
        
        # 앞뒤 공백 제거
        text = text.strip()
        
        return text
    
    def _extract_images(self, soup, base_url):
        """이미지 URL 추출"""
        images = []
        
        # img 태그에서 이미지 추출
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src')
            if src:
                # 상대 URL을 절대 URL로 변환
                absolute_url = urljoin(base_url, src)
                
                # 기본적인 이미지 필터링
                if self._is_valid_image(absolute_url):
                    images.append({
                        'url': absolute_url,
                        'alt': img.get('alt', ''),
                        'title': img.get('title', '')
                    })
        
        return images[:5]  # 최대 5개만
    
    def _is_valid_image(self, url):
        """유효한 이미지인지 확인"""
        if not url:
            return False
        
        # 기본 확장자 체크
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        url_lower = url.lower()
        
        if any(ext in url_lower for ext in valid_extensions):
            return True
        
        # 너무 작은 이미지나 아이콘 제외
        exclude_keywords = ['icon', 'logo', 'avatar', 'thumbnail', '1x1', 'pixel']
        if any(keyword in url_lower for keyword in exclude_keywords):
            return False
        
        return True
    
    def _print_statistics(self):
        """크롤링 통계 출력"""
        success_rate = (self.stats['successful_crawls'] / self.stats['total_attempts'] * 100) if self.stats['total_attempts'] > 0 else 0
        
        print(f"\n📊 크롤링 통계:")
        print(f"  • 시도: {self.stats['total_attempts']}개")
        print(f"  • 성공: {self.stats['successful_crawls']}개 ({success_rate:.1f}%)")
        print(f"  • 실패: {self.stats['failed_crawls']}개")
        print(f"  • 폴백 사용: {self.stats['fallback_used']}개")
    
    def test_single_article(self, url):
        """단일 기사 크롤링 테스트"""
        print(f"🧪 단일 기사 크롤링 테스트: {url}")
        
        try:
            content, images = self._extract_content(url)
            
            print(f"✅ 크롤링 성공")
            print(f"  • 본문 길이: {len(content)}자")
            print(f"  • 이미지 수: {len(images)}개")
            print(f"  • 본문 미리보기: {content[:200]}...")
            
            if images:
                print(f"  • 첫 번째 이미지: {images[0]['url']}")
            
            return content, images
            
        except Exception as e:
            print(f"❌ 크롤링 실패: {e}")
            return "", []
    
    def get_statistics(self):
        """통계 정보 반환"""
        return self.stats.copy()
    
    def add_custom_selector(self, domain, selectors):
        """사이트별 커스텀 선택자 추가"""
        self.content_selectors[domain] = selectors
        self.logger.info(f"커스텀 선택자 추가: {domain} -> {selectors}")
    
    def get_content_preview(self, article):
        """기사 본문 미리보기"""
        content = article.get('content', '')
        if len(content) > 300:
            return content[:300] + "..."
        return content