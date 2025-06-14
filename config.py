#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google News AI 자동화 시스템 설정 (구글시트 연동 + 시간대 개선)
기사 수집 → Notion 저장 → Telegram 전송
"""

import os
import pytz
from datetime import datetime
from dotenv import load_dotenv

# .env 파일 로드 (GCP 환경 고려)
env_path = os.path.join(os.getcwd(), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    print("⚠️ .env 파일을 찾을 수 없습니다. 환경 변수를 직접 확인합니다.")

class Config:
    """Google News AI 자동화 시스템 설정 (구글시트 연동 버전)"""
    
    # 프로젝트 정보
    PROJECT_CODE = "004_google_news_ai"
    SYSTEM_NAME = "Google News 자동화 에이전트"
    SYSTEM_VERSION = "v1.4"
    DEVELOPER_NAME = "양준모"
    DEVELOPER_EMAIL = "davidlikescat@icloud.com"
    
    # 뉴스 수집 설정
    MAX_ARTICLES = 10
    SEARCH_HOURS = 24
    
    # 🆕 구글시트 설정
    GOOGLE_SHEETS_CREDENTIALS_FILE = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE')
    GOOGLE_SHEETS_SPREADSHEET_ID = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')
    GOOGLE_SHEETS_WORKSHEET_NAME = os.getenv('GOOGLE_SHEETS_WORKSHEET_NAME', 'keywords')
    
    # 기본 검색 키워드 (Fallback용)
    AI_KEYWORDS = [
        "artificial intelligence",
        "AI",
        "machine learning",
        "deep learning", 
        "neural network",
        "ChatGPT",
        "OpenAI",
        "Google AI",
        "인공지능",
        "머신러닝",
        "딥러닝",
        "생성형 AI",
        "AI 기술",
        "LLM",
        "GPT"
    ]
    
    TECH_KEYWORDS = [
        "technology",
        "tech",
        "software",
        "programming",
        "developer",
        "기술",
        "소프트웨어", 
        "개발자",
        "IT",
        "스타트업",
        "네이버",
        "카카오",
        "삼성",
        "자율주행",
        "블록체인"
    ]
    
    # OpenAI API 설정
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
    OPENAI_MAX_TOKENS = int(os.getenv('OPENAI_MAX_TOKENS', '1500'))
    OPENAI_TEMPERATURE = float(os.getenv('OPENAI_TEMPERATURE', '0.3'))
    
    # Notion API 설정
    NOTION_API_KEY = os.getenv('NOTION_API_KEY')
    NOTION_TOKEN = NOTION_API_KEY  # 호환성을 위한 별칭
    NOTION_DATABASE_ID = os.getenv('NOTION_DATABASE_ID')
    NOTION_PAGE_ID = os.getenv('NOTION_PAGE_ID')
    
    # Telegram 설정
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    
    # 🆕 시간대 및 스케줄 설정
    TIMEZONE = os.getenv('TIMEZONE', 'Asia/Seoul')
    SCHEDULE_TIME = os.getenv('SCHEDULE_TIME', '07:30')  # 한국시간 기준
    
    # Discord 설정 (선택사항)
    DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
    DISCORD_CHANNEL_ID = os.getenv('DISCORD_CHANNEL_ID')
    
    # 크롤링 설정
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    REQUEST_TIMEOUT = 30
    MAX_RETRIES = 3
    REQUEST_DELAY = 1.0  # 요청 간 딜레이 (초)
    
    # Google News 설정
    GOOGLE_NEWS_URL = "https://news.google.com/rss"
    NEWS_LANGUAGE = "ko"
    NEWS_COUNTRY = "KR"
    
    # 필터링 설정
    MIN_ARTICLE_LENGTH = 100
    MAX_ARTICLE_LENGTH = 10000
    
    # 로그 설정
    LOG_LEVEL = "INFO"
    LOG_FILE = "google_news_ai.log"
    
    # 기타 설정
    DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
    SAVE_RAW_DATA = False
    
    # 페이지 설정
    NOTION_PAGE_TITLE_PREFIX = "Google News AI"
    NOTION_PAGE_ICON = "🤖"
    
    # 알림 설정
    TELEGRAM_PARSE_MODE = "HTML"
    TELEGRAM_DISABLE_WEB_PAGE_PREVIEW = True
    
    @classmethod
    def get_korea_time(cls):
        """현재 한국시간 반환"""
        try:
            korea_tz = pytz.timezone(cls.TIMEZONE)
            return datetime.now(korea_tz)
        except Exception:
            # Fallback to UTC+9
            import pytz
            korea_tz = pytz.timezone('Asia/Seoul')
            return datetime.now(korea_tz)
    
    @classmethod
    def get_search_keywords(cls):
        """검색 키워드 반환 (동적 로딩 지원)"""
        try:
            # 키워드 관리자 사용 시도
            from keyword_manager import KeywordManager
            keyword_manager = KeywordManager()
            keywords = keyword_manager.get_search_keywords()
            return keywords
        except Exception:
            # Fallback: 기본 키워드 사용
            return cls.AI_KEYWORDS
    
    @classmethod
    def get_ai_keywords(cls):
        """AI 관련 키워드만 반환"""
        try:
            from keyword_manager import KeywordManager
            keyword_manager = KeywordManager()
            return keyword_manager.get_ai_keywords_only()
        except Exception:
            return cls.AI_KEYWORDS
    
    @classmethod
    def get_tech_keywords(cls):
        """기술 관련 키워드만 반환"""
        try:
            from keyword_manager import KeywordManager
            keyword_manager = KeywordManager()
            return keyword_manager.get_tech_keywords_only()
        except Exception:
            return cls.TECH_KEYWORDS
    
    @classmethod
    def get_all_keywords(cls):
        """모든 검색 키워드 반환"""
        try:
            from keyword_manager import KeywordManager
            keyword_manager = KeywordManager()
            return keyword_manager.get_combined_keywords()
        except Exception:
            return cls.AI_KEYWORDS + cls.TECH_KEYWORDS
    
    @classmethod
    def get_priority_keywords(cls, max_count=5):
        """우선순위 높은 키워드만 반환"""
        try:
            from keyword_manager import KeywordManager
            keyword_manager = KeywordManager()
            return keyword_manager.get_priority_keywords_only(max_count)
        except Exception:
            # Fallback: 기본 우선순위 키워드
            priority_keywords = ["AI", "인공지능", "ChatGPT", "생성형AI", "머신러닝"]
            return priority_keywords[:max_count]
    
    @classmethod
    def get_headers(cls):
        """HTTP 요청 헤더 반환"""
        return {
            'User-Agent': cls.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
    
    @classmethod
    def validate_config(cls):
        """필수 설정 검증"""
        required_settings = {
            'OPENAI_API_KEY': cls.OPENAI_API_KEY,
            'NOTION_API_KEY': cls.NOTION_API_KEY, 
            'NOTION_DATABASE_ID': cls.NOTION_DATABASE_ID,
            'TELEGRAM_BOT_TOKEN': cls.TELEGRAM_BOT_TOKEN,
            'TELEGRAM_CHAT_ID': cls.TELEGRAM_CHAT_ID
        }
        
        missing = []
        for key, value in required_settings.items():
            if not value:
                missing.append(key)
        
        if missing:
            error_msg = f"필수 환경변수가 설정되지 않았습니다: {', '.join(missing)}"
            print(f"❌ {error_msg}")
            raise ValueError(error_msg)
        
        # 🆕 구글시트 설정 확인 (선택사항)
        sheets_settings = {
            'GOOGLE_SHEETS_CREDENTIALS_FILE': cls.GOOGLE_SHEETS_CREDENTIALS_FILE,
            'GOOGLE_SHEETS_SPREADSHEET_ID': cls.GOOGLE_SHEETS_SPREADSHEET_ID
        }
        
        sheets_missing = []
        for key, value in sheets_settings.items():
            if not value:
                sheets_missing.append(key)
        
        if sheets_missing:
            print(f"⚠️ 구글시트 설정이 없습니다: {', '.join(sheets_missing)}")
            print("💡 구글시트 없이도 기본 키워드로 동작합니다")
        else:
            # 구글시트 파일 존재 확인
            if cls.GOOGLE_SHEETS_CREDENTIALS_FILE and not os.path.exists(cls.GOOGLE_SHEETS_CREDENTIALS_FILE):
                print(f"⚠️ 구글시트 인증 파일을 찾을 수 없습니다: {cls.GOOGLE_SHEETS_CREDENTIALS_FILE}")
                print("💡 기본 키워드로 동작합니다")
            else:
                print("✅ 구글시트 설정 완료")
        
        print("✅ 필수 설정 검증 완료")
        return True
    
    @classmethod
    def validate_google_sheets_config(cls):
        """구글시트 설정 개별 검증"""
        if not cls.GOOGLE_SHEETS_CREDENTIALS_FILE:
            return False, "GOOGLE_SHEETS_CREDENTIALS_FILE이 설정되지 않았습니다"
        
        if not cls.GOOGLE_SHEETS_SPREADSHEET_ID:
            return False, "GOOGLE_SHEETS_SPREADSHEET_ID가 설정되지 않았습니다"
        
        if not os.path.exists(cls.GOOGLE_SHEETS_CREDENTIALS_FILE):
            return False, f"인증 파일을 찾을 수 없습니다: {cls.GOOGLE_SHEETS_CREDENTIALS_FILE}"
        
        return True, "구글시트 설정이 완료되었습니다"
    
    @classmethod
    def print_config(cls):
        """설정 정보 출력"""
        korea_time = cls.get_korea_time()
        
        print(f"🔧 프로젝트: {cls.PROJECT_CODE}")
        print(f"⚙️ 시스템: {cls.SYSTEM_NAME} {cls.SYSTEM_VERSION}")
        print(f"👤 개발자: {cls.DEVELOPER_NAME}")
        print(f"🕐 현재 한국시간: {korea_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"⏰ 스케줄 시간: 매일 {cls.SCHEDULE_TIME} ({cls.TIMEZONE})")
        print(f"📊 수집 기사 수: {cls.MAX_ARTICLES}개")
        print(f"⏱️ 수집 범위: 최근 {cls.SEARCH_HOURS}시간")
        
        # API 설정 상태
        apis = {
            'OpenAI': bool(cls.OPENAI_API_KEY),
            'Notion': bool(cls.NOTION_API_KEY and cls.NOTION_DATABASE_ID), 
            'Telegram': bool(cls.TELEGRAM_BOT_TOKEN and cls.TELEGRAM_CHAT_ID),
            'Discord': bool(cls.DISCORD_BOT_TOKEN and cls.DISCORD_CHANNEL_ID)
        }
        
        print("🔗 API 설정 상태:")
        for api, status in apis.items():
            status_icon = "✅" if status else "❌"
            print(f"   {status_icon} {api}")
        
        # 🆕 구글시트 설정 상태
        sheets_valid, sheets_msg = cls.validate_google_sheets_config()
        sheets_icon = "✅" if sheets_valid else "⚠️"
        print(f"   {sheets_icon} Google Sheets: {sheets_msg}")
        
        # 키워드 정보
        try:
            keywords = cls.get_search_keywords()
            print(f"🔑 사용 키워드: {len(keywords)}개")
            print(f"   주요 키워드: {', '.join(keywords[:5])}{'...' if len(keywords) > 5 else ''}")
        except Exception as e:
            print(f"⚠️ 키워드 로딩 오류: {e}")


def setup_environment():
    """환경 설정 가이드"""
    print("🔧 Google News AI 자동화 시스템 환경 설정")
    print("=" * 60)
    
    # .env 파일 예제 생성
    env_example = """# Google News AI 자동화 시스템 환경변수

# OpenAI API 설정
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_MAX_TOKENS=1500
OPENAI_TEMPERATURE=0.3

# Notion API 설정
NOTION_API_KEY=your_notion_api_key_here
NOTION_DATABASE_ID=your_notion_database_id_here
NOTION_PAGE_ID=your_notion_page_id_here

# Telegram Bot 설정
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here

# 🆕 구글시트 연동 설정 (선택사항)
GOOGLE_SHEETS_CREDENTIALS_FILE=path/to/service_account.json
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id_here
GOOGLE_SHEETS_WORKSHEET_NAME=keywords

# 🆕 시간대 및 스케줄 설정
TIMEZONE=Asia/Seoul
SCHEDULE_TIME=07:30

# Discord 설정 (선택사항)
DISCORD_BOT_TOKEN=your_discord_bot_token_here
DISCORD_CHANNEL_ID=your_discord_channel_id_here

# 기타 설정
DEBUG_MODE=False
"""
    
    with open('.env.example', 'w', encoding='utf-8') as f:
        f.write(env_example)
    
    print("📄 .env.example 파일이 생성되었습니다")
    print("🔑 필요한 API 키들을 .env 파일에 설정하세요")
    print("\n💡 구글시트 설정 가이드:")
    print("1. Google Cloud Console에서 Service Account 생성")
    print("2. Service Account JSON 키 다운로드")
    print("3. 구글시트를 Service Account와 공유")
    print("4. 스프레드시트 ID를 환경변수에 설정")
    
    # 설정 상태 확인
    try:
        Config.validate_config()
    except ValueError as e:
        print(f"⚠️ {e}")
        print("💡 .env 파일을 확인하고 필요한 API 키를 설정하세요")


def test_google_sheets_connection():
    """구글시트 연결 테스트"""
    print("🧪 구글시트 연결 테스트")
    print("=" * 50)
    
    try:
        from google_sheets_manager import GoogleSheetsManager
        manager = GoogleSheetsManager()
        
        if manager.test_connection():
            print("✅ 구글시트 연결 테스트 성공!")
            return True
        else:
            print("❌ 구글시트 연결 테스트 실패!")
            return False
            
    except ImportError:
        print("❌ google_sheets_manager.py가 없습니다")
        return False
    except Exception as e:
        print(f"❌ 구글시트 연결 테스트 오류: {e}")
        return False


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "setup":
            setup_environment()
        elif command == "test-sheets":
            test_google_sheets_connection()
        elif command == "keywords":
            print("🔑 현재 키워드 설정:")
            print("=" * 50)
            try:
                keywords = Config.get_search_keywords()
                print(f"📋 총 키워드: {len(keywords)}개")
                for i, kw in enumerate(keywords, 1):
                    print(f"  {i:2d}. {kw}")
            except Exception as e:
                print(f"❌ 키워드 로딩 실패: {e}")
        elif command == "help":
            print("사용법:")
            print("  python3 config.py          # 설정 정보 출력")
            print("  python3 config.py setup    # 환경 설정 가이드")
            print("  python3 config.py test-sheets # 구글시트 연결 테스트")
            print("  python3 config.py keywords # 현재 키워드 출력")
            print("  python3 config.py help     # 도움말")
        else:
            print(f"❌ 알 수 없는 명령어: {command}")
            print("python3 config.py help 로 도움말을 확인하세요")
    else:
        print("📋 Google News AI 자동화 시스템 설정 정보")
        print("=" * 60)
        Config.print_config()
        
        print("\n🧪 설정 검증...")
        try:
            Config.validate_config()
            print("🎉 모든 설정이 올바르게 구성되었습니다!")
        except ValueError as e:
            print(f"❌ 설정 오류: {e}")
            print("\n🔧 환경 설정을 시작하려면:")
            print("python3 config.py setup")