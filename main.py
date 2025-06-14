#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google News 간단 수집 시스템 - OpenAI 제외 버전
기사 수집 → Notion 저장 → Telegram 전송
"""

import time
from datetime import datetime
import logging
import sys
import os

# 로컬 모듈 import
try:
    from config import Config
    from google_news_collector import GoogleNewsCollector
    from article_crawler import ArticleCrawler
    
    # Notion 모듈
    try:
        from notion_saver import NotionSaver
    except ImportError:
        from simple_notion import NotionSaver
        print("💡 기존 notion_saver가 없어서 simple_notion을 사용합니다")
    
    # 텔레그램 모듈
    from telegram_sender import TelegramSender
    
except ImportError as e:
    print(f"❌ 모듈 import 오류: {e}")
    print("💡 필요한 모듈들이 있는지 확인하세요")
    print("📋 필요 모듈: google_news_collector, article_crawler")
    print("📋 선택 모듈: notion_saver/simple_notion, telegram_sender/simple_telegram")
    sys.exit(1)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('simple_news_collector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def create_simple_summary(articles):
    """OpenAI 없이 간단한 요약 데이터 생성"""
    
    # 기사들을 시간순으로 정렬
    sorted_articles = sorted(articles, key=lambda x: x.get('published', datetime.now()), reverse=True)
    
    # 간단한 메타데이터 생성
    summary_data = {
        'total_articles': len(articles),
        'collection_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'articles': [],
        'sources': set(),
        'keywords_found': set(),
        'date_range': {
            'latest': None,
            'earliest': None
        }
    }
    
    # 각 기사 처리
    for i, article in enumerate(sorted_articles, 1):
        # 기본 정보 추출
        article_data = {
            'rank': i,
            'title': article.get('title', 'No Title'),
            'source': article.get('source', 'Unknown Source'),
            'published': article.get('published', datetime.now()).strftime('%Y-%m-%d %H:%M:%S'),
            'url': article.get('url', ''),
            'content': article.get('content', '')[:500] + '...' if article.get('content') else 'No Content',
            'content_length': len(article.get('content', '')),
            'summary': None  # AI 요약 없음
        }
        
        # 소스 추가
        summary_data['sources'].add(article_data['source'])
        
        # 키워드 찾기 (제목과 내용에서)
        text_to_check = (article_data['title'] + ' ' + article.get('content', '')).lower()
        for keyword in Config.get_search_keywords():
            if keyword.lower() in text_to_check:
                summary_data['keywords_found'].add(keyword)
        
        summary_data['articles'].append(article_data)
    
    # 날짜 범위 설정
    if summary_data['articles']:
        summary_data['date_range']['latest'] = summary_data['articles'][0]['published']
        summary_data['date_range']['earliest'] = summary_data['articles'][-1]['published']
    
    # set을 list로 변환
    summary_data['sources'] = list(summary_data['sources'])
    summary_data['keywords_found'] = list(summary_data['keywords_found'])
    
    # 간단한 통계 생성
    summary_data['stats'] = {
        'total_sources': len(summary_data['sources']),
        'keywords_found_count': len(summary_data['keywords_found']),
        'avg_content_length': sum(a['content_length'] for a in summary_data['articles']) // len(summary_data['articles']) if summary_data['articles'] else 0
    }
    
    return summary_data

def send_success_notification(summary_data, notion_url):
    """성공 알림 전송 - telegram_sender.py의 send_summary_message 사용"""
    try:
        telegram = TelegramSender()
        return telegram.send_summary_message(summary_data, notion_url)
        
    except Exception as e:
        logger.error(f"성공 알림 전송 실패: {e}")
        print(f"❌ 텔레그램 성공 알림 전송 실패: {e}")
        return False

def send_error_notification(error_message):
    """에러 알림 전송 - telegram_sender.py의 send_error_notification 사용"""
    try:
        telegram = TelegramSender()
        return telegram.send_error_notification(error_message)
    except Exception as e:
        logger.error(f"에러 알림 전송 실패: {e}")
        return False

def create_simple_html_report(summary_data):
    """간단한 HTML 리포트 생성 (OpenAI 없는 버전)"""
    
    html_content = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Google News 수집 리포트 - {summary_data['collection_time']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; border-bottom: 2px solid #4CAF50; padding-bottom: 20px; margin-bottom: 20px; }}
        .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
        .stat-box {{ text-align: center; padding: 15px; background: #f8f9fa; border-radius: 8px; }}
        .article {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 8px; background: white; }}
        .article-title {{ font-size: 18px; font-weight: bold; color: #333; margin-bottom: 10px; }}
        .article-meta {{ color: #666; font-size: 14px; margin-bottom: 10px; }}
        .article-content {{ color: #444; line-height: 1.6; }}
        .keywords {{ margin: 20px 0; }}
        .keyword-tag {{ background: #e3f2fd; color: #1976d2; padding: 4px 8px; margin: 2px; border-radius: 4px; display: inline-block; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Google News AI 수집 리포트</h1>
            <p>수집 시간: {summary_data['collection_time']}</p>
            <p><strong>💡 AI 요약 없이 원문 기사 직접 수집</strong></p>
        </div>
        
        <div class="stats">
            <div class="stat-box">
                <h3>{summary_data['total_articles']}</h3>
                <p>수집된 기사</p>
            </div>
            <div class="stat-box">
                <h3>{summary_data['stats']['total_sources']}</h3>
                <p>언론사</p>
            </div>
            <div class="stat-box">
                <h3>{summary_data['stats']['keywords_found_count']}</h3>
                <p>발견된 키워드</p>
            </div>
            <div class="stat-box">
                <h3>{summary_data['stats']['avg_content_length']}</h3>
                <p>평균 본문 길이</p>
            </div>
        </div>
        
        <div class="keywords">
            <h3>🏷️ 발견된 키워드</h3>
            {' '.join([f'<span class="keyword-tag">#{kw}</span>' for kw in summary_data['keywords_found']])}
        </div>
        
        <h3>📰 수집된 기사들</h3>
"""
    
    # 각 기사 추가
    for article in summary_data['articles']:
        html_content += f"""
        <div class="article">
            <div class="article-title">{article['rank']}. {article['title']}</div>
            <div class="article-meta">
                📰 {article['source']} | ⏰ {article['published']} | 📝 {article['content_length']}자
            </div>
            <div class="article-content">
                {article['content']}
            </div>
            <div style="margin-top: 10px;">
                <a href="{article['url']}" target="_blank" style="color: #1976d2;">🔗 원문 보기</a>
            </div>
        </div>
        """
    
    html_content += """
        <div style="text-align: center; margin-top: 30px; color: #666;">
            <p>🤖 Google News Simple Collector by David Lee</p>
            <p>💰 OpenAI API 비용 없이 수집된 뉴스입니다</p>
        </div>
    </div>
</body>
</html>
    """
    
    return html_content

def main():
    """Google News 간단 수집 메인 함수 (OpenAI 제외)"""
    start_time = time.time()
    
    print("\n🤖 Google News 간단 수집 시스템 (OpenAI 제외)")
    print("=" * 70)
    print(f"🔧 프로젝트: {Config.PROJECT_CODE}")
    print(f"⚙️ 시스템: {Config.SYSTEM_NAME} {Config.SYSTEM_VERSION}")
    print(f"📊 목표: 최신 {Config.MAX_ARTICLES}개 AI 뉴스 수집")
    print(f"💰 특징: OpenAI API 비용 없음!")
    print(f"🕐 실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # 1단계: 설정 검증 (OpenAI 제외)
        print(f"\n🔍 1단계: 설정 검증 중...")
        Config.validate_config()
        print("✅ 설정 검증 완료 (OpenAI API 불필요)")

        # 2단계: Google News 검색
        print(f"\n🔍 2단계: Google News에서 AI 뉴스 검색 중...")
        print(f"🎯 검색 키워드: {', '.join(Config.get_search_keywords()[:5])}...")
        
        collector = GoogleNewsCollector(max_articles=Config.MAX_ARTICLES)
        articles = collector.collect_latest_news(Config.get_all_keywords())
        
        if not articles:
            error_msg = "Google News에서 AI 관련 최신 기사를 찾을 수 없습니다."
            print(f"❌ {error_msg}")
            send_error_notification(error_msg)
            return False

        print(f"✅ {len(articles)}개 기사 수집 완료")

        # 3단계: 기사 본문 크롤링
        print(f"\n📄 3단계: 기사 본문 크롤링 중...")
        
        crawler = ArticleCrawler()
        crawled_articles = crawler.crawl_articles(articles)
        
        if not crawled_articles:
            error_msg = "기사 본문 크롤링에 실패했습니다."
            print(f"❌ {error_msg}")
            send_error_notification(error_msg)
            return False
            
        print(f"✅ {len(crawled_articles)}개 기사 크롤링 완료")

        # 4단계: 간단한 요약 데이터 생성 (OpenAI 없이)
        print(f"\n📊 4단계: 데이터 정리 중 (AI 요약 없음)...")
        
        summary_data = create_simple_summary(crawled_articles)
        print("✅ 데이터 정리 완료")

        # 5단계: HTML 리포트 생성
        print(f"\n📋 5단계: 리포트 생성 중...")
        
        html_content = create_simple_html_report(summary_data)
        print("✅ 리포트 생성 완료")

        # 6단계: Notion 저장
        print(f"\n💾 6단계: Notion 저장 중...")
        
        notion_saver = NotionSaver()
        notion_url = notion_saver.save_to_notion(summary_data, html_content)
        
        if not notion_url:
            error_msg = "Notion 저장에 실패했습니다."
            print(f"❌ {error_msg}")
            send_error_notification(error_msg)
            return False
            
        print(f"✅ Notion 저장 완료")
        logger.info(f"Notion URL: {notion_url}")

        # 7단계: Telegram 전송
        print(f"\n📱 7단계: Telegram 전송 중...")
        
        telegram_success = send_success_notification(summary_data, notion_url)

        # 실행 완료 요약
        end_time = time.time()
        duration = round(end_time - start_time, 2)

        print("\n" + "=" * 70)
        print(f"🎉 Google News 간단 수집 완료!")
        print(f"📊 처리 결과:")
        print(f"   • 수집된 기사: {len(summary_data['articles'])}개")
        print(f"   • 언론사: {summary_data['stats']['total_sources']}곳")
        print(f"   • 발견된 키워드: {summary_data['stats']['keywords_found_count']}개")
        print(f"   • 소요시간: {duration}초")
        print(f"   • Notion 저장: ✅")
        print(f"   • Telegram 전송: {'✅' if telegram_success else '❌'}")
        print(f"   • 완료시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   • 💰 OpenAI API 비용: $0.00")

        # 주요 뉴스 헤드라인
        print(f"\n📰 수집된 AI 뉴스 TOP {min(5, len(summary_data['articles']))}:")
        for i, article in enumerate(summary_data['articles'][:5], 1):
            print(f"  {i}. {article['title']}")
            print(f"     📰 {article['source']} | 🕐 {article['published']}")

        # 주요 키워드
        if summary_data['keywords_found']:
            keywords = summary_data['keywords_found'][:8]
            print(f"\n🏷️ 발견된 키워드: {' '.join([f'#{keyword}' for keyword in keywords])}")

        # 성공 로그
        logger.info(f"Google News 간단 수집 완료 - {len(summary_data['articles'])}개 기사, {duration}초, OpenAI 비용 없음")

        return True

    except Exception as e:
        error_msg = f"시스템 실행 중 오류 발생: {str(e)}"
        logger.error(f"❌ {error_msg}")
        print(f"❌ {error_msg}")
        
        # 에러 알림 전송
        send_error_notification(error_msg)
        
        return False

def test_system():
    """시스템 간단 테스트"""
    print("🧪 Google News 간단 수집 시스템 테스트")
    print("=" * 50)
    
    try:
        # 설정 테스트
        print("1. 설정 검증...")
        Config.validate_config()
        print("   ✅ 설정 검증 통과 (OpenAI 불필요)")
        
        # Google News 테스트
        print("2. Google News 연결 테스트...")
        collector = GoogleNewsCollector(max_articles=3)
        test_articles = collector.collect_latest_news(['AI', 'artificial intelligence'])
        
        if test_articles:
            print(f"   ✅ Google News 테스트 통과 ({len(test_articles)}개 기사)")
            for article in test_articles:
                print(f"      • {article['title'][:50]}...")
        else:
            print("   ⚠️ Google News 테스트 - 기사 없음")
        
        print("\n🎯 테스트 완료! (OpenAI API 비용 없음)")
        return True
        
    except Exception as e:
        print(f"   ❌ 테스트 실패: {e}")
        return False

def print_help():
    """도움말 출력"""
    print("Google News 간단 수집 시스템 (OpenAI 제외)")
    print("=" * 60)
    print("사용법:")
    print("  python3 main.py        # 메인 실행")
    print("  python3 main.py test   # 시스템 테스트") 
    print("  python3 main.py config # 설정 정보")
    print("  python3 main.py help   # 도움말")
    print("\n💰 특징:")
    print("  • OpenAI API 비용 없음!")
    print("  • Google News에서 AI 관련 최신 뉴스 수집")
    print("  • 기사 원문 직접 크롤링")
    print("  • Notion 데이터베이스에 자동 저장")
    print("  • Telegram으로 결과 알림 전송")
    print("\n🔗 필요한 API:")
    print("  • Notion API (무료)")
    print("  • Telegram Bot API (무료)")
    print("\n스케줄 실행:")
    print("  python3 simple_scheduler.py  # 정기 스케줄러 시작")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "test":
            test_system()
        elif command == "config":
            Config.print_config()
        elif command == "help":
            print_help()
        else:
            print(f"❌ 알 수 없는 명령어: {command}")
            print("도움말: python3 main.py help")
    else:
        # 메인 실행
        success = main()
        sys.exit(0 if success else 1)