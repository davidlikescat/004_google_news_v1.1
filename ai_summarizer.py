# ai_summarizer.py - datetime 오류 수정 버전

import openai
from datetime import datetime
import re
from collections import Counter
import logging

logger = logging.getLogger(__name__)

class AISummarizer:
    """AI를 활용한 기사 요약 생성기"""
    
    def __init__(self):
        from config import Config
        openai.api_key = Config.OPENAI_API_KEY
        self.model = Config.AI_MODEL
        self.max_tokens = Config.OPENAI_MAX_TOKENS
        self.temperature = Config.OPENAI_TEMPERATURE
    
    def generate_summary(self, articles):
        """기사들을 AI로 요약"""
        if not articles:
            return {"articles": [], "top_keywords": [], "summary": ""}
        
        print(f"🤖 {len(articles)}개 기사 AI 요약 중...")
        
        summarized_articles = []
        all_keywords = []
        
        for i, article in enumerate(articles, 1):
            try:
                print(f"   [{i}/{len(articles)}] {article['title'][:30]}...")
                
                # AI 요약 생성
                summary = self._generate_ai_summary(article)
                
                # 키워드 추출
                keywords = self._extract_keywords(article, summary)
                
                # 🔧 datetime 객체 처리 수정
                published_str = self._format_published_date(article.get('published'))
                
                summarized_article = {
                    'title': article['title'],
                    'summary': summary,
                    'url': article['url'],
                    'published': published_str,  # 문자열로 변환된 날짜
                    'source': article.get('source', 'Unknown'),
                    'keywords': keywords,
                    'category': self._categorize_article(article, summary)
                }
                
                summarized_articles.append(summarized_article)
                all_keywords.extend(keywords)
                
            except Exception as e:
                logger.warning(f"기사 요약 실패: {e}")
                # 실패한 경우 기본 정보로 추가
                summarized_article = {
                    'title': article['title'],
                    'summary': article.get('summary', '')[:200] + '...',
                    'url': article['url'],
                    'published': self._format_published_date(article.get('published')),
                    'source': article.get('source', 'Unknown'),
                    'keywords': [],
                    'category': 'AI 뉴스'
                }
                summarized_articles.append(summarized_article)
        
        # 상위 키워드 추출
        top_keywords = self._get_top_keywords(all_keywords)
        
        # 전체 요약 생성
        overall_summary = self._generate_overall_summary(summarized_articles)
        
        result = {
            'articles': summarized_articles,
            'top_keywords': top_keywords,
            'summary': overall_summary,
            'total_count': len(summarized_articles),
            'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        print(f"✅ AI 요약 완료: {len(summarized_articles)}개 기사")
        return result
    
    def _format_published_date(self, published):
        """발행 날짜를 문자열로 안전하게 변환"""
        try:
            if published is None:
                return "날짜 미상"
            
            # datetime 객체인 경우
            if isinstance(published, datetime):
                return published.strftime('%Y-%m-%d %H:%M')
            
            # 이미 문자열인 경우
            if isinstance(published, str):
                return published
            
            # 기타 타입인 경우 문자열로 변환
            return str(published)
            
        except Exception as e:
            logger.warning(f"날짜 포맷팅 실패: {e}")
            return "날짜 미상"
    
    def _generate_ai_summary(self, article):
        """단일 기사에 대한 AI 요약 생성"""
        try:
            # OpenAI client 초기화
            from openai import OpenAI
            client = OpenAI(api_key=openai.api_key)
            
            # 프롬프트 생성
            prompt = f"""
다음 AI 관련 뉴스 기사를 한국어로 간결하게 요약해주세요 (150자 이내):

제목: {article['title']}
내용: {article.get('content', article.get('summary', ''))[:1000]}

요약 조건:
- 핵심 내용만 간결하게
- 기술적 용어는 이해하기 쉽게
- 한국어로 자연스럽게
- 150자 이내로 제한
"""
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "당신은 AI 뉴스 전문 요약가입니다."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            summary = response.choices[0].message.content.strip()
            return summary[:200]  # 최대 200자로 제한
            
        except Exception as e:
            logger.warning(f"AI 요약 생성 실패: {e}")
            # AI 요약 실패 시 원본 요약 사용
            return article.get('summary', '')[:150] + '...'
    
    def _extract_keywords(self, article, summary):
        """기사와 요약에서 키워드 추출"""
        from config import Config
        
        text = f"{article['title']} {summary}".lower()
        found_keywords = []
        
        for keyword in Config.AI_KEYWORDS:
            if keyword.lower() in text:
                found_keywords.append(keyword)
        
        return found_keywords[:5]  # 최대 5개
    
    def _categorize_article(self, article, summary):
        """기사 카테고리 분류"""
        from config import Config
        
        text = f"{article['title']} {summary}".lower()
        
        for category, keywords in Config.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    return category
        
        return "AI 뉴스"
    
    def _get_top_keywords(self, all_keywords):
        """상위 키워드 추출"""
        if not all_keywords:
            return ["인공지능", "AI", "기술", "뉴스", "혁신"]
        
        # 키워드 빈도 계산
        keyword_counts = Counter(all_keywords)
        
        # 상위 10개 키워드
        top_keywords = [keyword for keyword, count in keyword_counts.most_common(10)]
        
        return top_keywords
    
    def _generate_overall_summary(self, articles):
        """전체 기사에 대한 종합 요약"""
        if not articles:
            return "오늘 수집된 AI 뉴스가 없습니다."
        
        try:
            # OpenAI client 초기화
            from openai import OpenAI
            client = OpenAI(api_key=openai.api_key)
            
            # 모든 기사 제목 수집
            titles = [article['title'] for article in articles]
            titles_text = '\n'.join([f"- {title}" for title in titles])
            
            prompt = f"""
다음 {len(articles)}개의 AI 뉴스 제목들을 바탕으로 오늘의 AI 뉴스 트렌드를 한 문장으로 요약해주세요:

{titles_text}

조건:
- 한국어로 작성
- 50자 내외로 간결하게
- 주요 트렌드나 키워드 포함
"""
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "당신은 AI 뉴스 트렌드 분석가입니다."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.5
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.warning(f"전체 요약 생성 실패: {e}")
            return f"오늘 {len(articles)}개의 AI 관련 뉴스가 발표되었습니다."
    
    def _generate_daily_report(self, summarized_articles):
        """일일 리포트 생성"""
        if not summarized_articles:
            return "오늘 수집된 기사가 없습니다."
        
        report_parts = []
        report_parts.append(f"📰 오늘의 AI 뉴스 {len(summarized_articles)}선")
        report_parts.append("")
        
        for i, article in enumerate(summarized_articles, 1):
            # 🔧 발행 시간 안전하게 처리
            published_display = article.get('published', '시간 미상')
            if isinstance(published_display, datetime):
                published_display = published_display.strftime('%H:%M')
            elif isinstance(published_display, str) and len(published_display) > 10:
                published_display = published_display[11:16]  # 'HH:MM' 부분만 추출
            
            report_parts.append(f"{i}. {article['title']}")
            report_parts.append(f"   📍 {article['source']} | ⏰ {published_display}")
            report_parts.append(f"   💡 {article['summary']}")
            if article['keywords']:
                keywords_str = ', '.join(article['keywords'][:3])
                report_parts.append(f"   🏷️ {keywords_str}")
            report_parts.append("")
        
        return '\n'.join(report_parts)

def test_summarizer():
    """AI 요약기 테스트"""
    print("🧪 AI 요약기 테스트")
    
    # 테스트 기사 데이터
    test_articles = [
        {
            'title': '삼성전자, 새로운 AI 반도체 개발 발표',
            'content': '삼성전자가 차세대 인공지능 반도체를 개발했다고 발표했습니다.',
            'url': 'https://example.com/1',
            'published': datetime.now(),
            'source': '테스트 뉴스',
            'summary': '삼성전자 AI 반도체 관련 뉴스'
        }
    ]
    
    summarizer = AISummarizer()
    result = summarizer.generate_summary(test_articles)
    
    print(f"✅ 테스트 완료: {len(result['articles'])}개 기사 요약")
    for article in result['articles']:
        print(f"   • {article['title']}")
        print(f"     발행: {article['published']}")

if __name__ == "__main__":
    test_summarizer()