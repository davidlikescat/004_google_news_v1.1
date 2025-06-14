#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Sheets 연동 관리자
키워드 데이터를 구글시트에서 동적으로 로딩
"""

import os
import json
import logging
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
from typing import List, Dict, Optional

# .env 파일 로드
load_dotenv()

# 로깅 설정
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# 콘솔 핸들러 생성
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# 포맷터 생성
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)

# 핸들러 추가
logger.addHandler(ch)

try:
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False
    print("⚠️ gspread 라이브러리가 설치되지 않았습니다. pip install gspread google-auth 실행하세요.")

class GoogleSheetsManager:
    """구글시트 키워드 관리 시스템"""
    
    def __init__(self):
        try:
            # 현재 디렉토리의 절대 경로 가져오기
            current_dir = os.path.dirname(os.path.abspath(__file__))
            
            # 자격증명 파일 경로
            self.credentials_file = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE', os.path.join(current_dir, 'credential.json'))
            self.spreadsheet_id = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')
            self.worksheet_name = os.getenv('GOOGLE_SHEETS_WORKSHEET_NAME', 'Sheet1')
            
            # 환경 변수 유효성 검사
            if not self.spreadsheet_id:
                raise ValueError("❌ 스프레드시트 ID가 설정되어 있지 않습니다. .env 파일을 확인하세요")
            
            logger.info("⚙️ 구글시트 설정 로드:")
            logger.info(f"  • 자격증명 파일: {self.credentials_file}")
            logger.info(f"  • 스프레드시트 ID: {self.spreadsheet_id}")
            logger.info(f"  • 워크시트 이름: {self.worksheet_name}")
            
            # 환경 변수 로드 확인
            logger.info(f"🔍 환경 변수 로드 확인:")
            logger.info(f"  • 자격증명 파일 존재 여부: {'✅' if os.path.exists(self.credentials_file) else '❌'}")
            logger.info(f"  • 스프레드시트 ID 길이: {len(self.spreadsheet_id) if self.spreadsheet_id else 'None'}")
            
            # 자격증명 확인
            if not os.path.exists(self.credentials_file):
                raise FileNotFoundError(f"❌ 자격증명 파일이 없습니다: {self.credentials_file}")
                
            # 구글 API 자격증명 생성
            scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly']
            logger.info(f"🔑 자격증명 생성 시도:")
            credentials = Credentials.from_service_account_file(
                self.credentials_file,
                scopes=scopes
            )
            logger.info("✅ 자격증명 생성 완료")
            
            # gspread 클라이언트 초기화
            logger.info("🔗 gspread 클라이언트 초기화 시도:")
            gc = gspread.authorize(credentials)
            logger.info("✅ gspread 클라이언트 초기화 완료")
            
            # 스프레드시트 열기
            try:
                logger.info(f"📁 스프레드시트 열기 시도: {self.spreadsheet_id}")
                spreadsheet = gc.open_by_key(self.spreadsheet_id)
                logger.info(f"✅ 스프레드시트 열기 성공: {self.spreadsheet_id}")
                
                # 워크시트 선택
                try:
                    logger.info(f"📄 워크시트 선택 시도: {self.worksheet_name}")
                    worksheet = spreadsheet.worksheet(self.worksheet_name)
                    logger.info(f"✅ 워크시트 선택 성공: {self.worksheet_name}")
                    
                    # 키워드 로드
                    try:
                        logger.info("📚 키워드 로드 시도:")
                        keywords = self._load_keywords_from_sheet(worksheet)
                        logger.info(f"✅ 키워드 로드 성공: {len(keywords)}개")
                        self.cached_keywords = keywords
                        self.last_update = datetime.now()
                        
                        # 키워드 내용 확인
                        logger.info("🔍 키워드 내용:")
                        for idx, keyword in enumerate(keywords[:3]):  # 처음 3개만 출력
                            logger.info(f"  {idx + 1}. {keyword}")
                    except Exception as e:
                        logger.error(f"❌ 키워드 로드 실패: {e}")
                        self.cached_keywords = None
                        
                except Exception as e:
                    logger.error(f"❌ 워크시트 선택 실패: {e}")
                    
            except Exception as e:
                logger.error(f"❌ 스프레드시트 열기 실패: {e}")
                
        except Exception as e:
            logger.error(f"❌ 구글시트 초기화 실패: {e}")
            
        # 캐시 설정
        self.cache_duration = 300  # 5분 캐시
        self.last_update = None
        self.cached_keywords = None
        
        # 기본 키워드 (Fallback)
        self.fallback_keywords = [
            {'keyword': '인공지능', 'category': 'AI', 'priority': 1, 'active': True},
            {'keyword': 'ChatGPT', 'category': 'AI', 'priority': 1, 'active': True},
            {'keyword': '생성형AI', 'category': 'AI', 'priority': 1, 'active': True},
            {'keyword': '네이버', 'category': 'TECH', 'priority': 2, 'active': True},
            {'keyword': '카카오', 'category': 'TECH', 'priority': 2, 'active': True},
            {'keyword': 'AI', 'category': 'AI', 'priority': 1, 'active': True},
            {'keyword': '머신러닝', 'category': 'AI', 'priority': 2, 'active': True},
            {'keyword': '딥러닝', 'category': 'AI', 'priority': 2, 'active': True},
            {'keyword': '자율주행', 'category': 'TECH', 'priority': 2, 'active': True},
            {'keyword': 'LLM', 'category': 'AI', 'priority': 2, 'active': True}
        ]
        
        # 클라이언트 초기화
        self.client = None
        self.worksheet = None
        self._initialize_client()
    
    def _initialize_client(self):
        """구글시트 클라이언트 초기화"""
        if not GSPREAD_AVAILABLE:
            logger.warning("⚠️ gspread 라이브러리가 없습니다. Fallback 키워드 사용")
            return False
        
        if not self.credentials_file or not self.spreadsheet_id:
            logger.warning("⚠️ 구글시트 설정이 없습니다. Fallback 키워드 사용")
            return False
        
        try:
            # 서비스 계정 인증
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets.readonly',
                'https://www.googleapis.com/auth/drive.readonly'
            ]
            
            if not os.path.exists(self.credentials_file):
                logger.error(f"❌ 인증 파일을 찾을 수 없습니다: {self.credentials_file}")
                return False
            
            creds = Credentials.from_service_account_file(
                self.credentials_file, 
                scopes=scopes
            )
            
            self.client = gspread.authorize(creds)
            
            # 스프레드시트 열기
            spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            self.worksheet = spreadsheet.worksheet(self.worksheet_name)
            
            logger.info("✅ 구글시트 연결 성공")
            logger.info(f"📊 시트: {spreadsheet.title} > {self.worksheet_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 구글시트 초기화 실패: {e}")
            self.client = None
            self.worksheet = None
            return False
    
    def _should_refresh_cache(self) -> bool:
        """캐시 갱신이 필요한지 확인"""
        if self.last_update is None:
            return True
        
        return datetime.now() - self.last_update > timedelta(seconds=self.cache_duration)
    
    def load_keywords_from_sheet(self) -> List[Dict]:
        """구글시트에서 키워드 로딩"""
        if not self.worksheet:
            logger.warning("⚠️ 구글시트가 연결되지 않았습니다. 재연결 시도...")
            if not self._initialize_client():
                return []
        
        try:
            logger.info("📥 구글시트에서 키워드 로딩 중...")
            
            # 모든 데이터 가져오기
            all_values = self.worksheet.get_all_values()
            
            if not all_values:
                logger.warning("⚠️ 시트가 비어있습니다")
                return []
            
            # 헤더 확인
            headers = all_values[0]
            logger.info(f"📋 시트 헤더: {headers}")
            
            # 필수 컬럼 확인
            required_columns = ['keyword']
            header_map = {}
            
            for col in required_columns:
                if col in headers:
                    header_map[col] = headers.index(col)
                else:
                    logger.error(f"❌ 필수 컬럼 누락: {col}")
                    return []
            
            # 선택적 컬럼 매핑
            optional_columns = ['category', 'priority', 'active']
            for col in optional_columns:
                if col in headers:
                    header_map[col] = headers.index(col)
            
            keywords = []
            
            # 데이터 행 처리 (헤더 제외)
            for i, row in enumerate(all_values[1:], 2):
                if len(row) <= header_map.get('keyword', 0):
                    continue
                
                keyword_text = row[header_map['keyword']].strip()
                if not keyword_text:
                    continue
                
                # 키워드 데이터 구성
                keyword_data = {
                    'keyword': keyword_text,
                    'category': row[header_map.get('category', -1)].strip() if header_map.get('category', -1) < len(row) else 'GENERAL',
                    'priority': self._safe_int(row[header_map.get('priority', -1)] if header_map.get('priority', -1) < len(row) else '1'),
                    'active': self._safe_bool(row[header_map.get('active', -1)] if header_map.get('active', -1) < len(row) else 'TRUE'),
                    'row_number': i
                }
                
                keywords.append(keyword_data)
            
            logger.info(f"✅ 키워드 로딩 완료: {len(keywords)}개")
            
            # 활성화된 키워드만 필터링
            active_keywords = [k for k in keywords if k['active']]
            logger.info(f"🎯 활성 키워드: {len(active_keywords)}개")
            
            return active_keywords
            
        except Exception as e:
            logger.error(f"❌ 키워드 로딩 실패: {e}")
            return []
    
    def _safe_int(self, value: str, default: int = 1) -> int:
        """안전한 정수 변환"""
        try:
            return int(value) if value.strip() else default
        except (ValueError, AttributeError):
            return default
    
    def _safe_bool(self, value: str, default: bool = True) -> bool:
        """안전한 불린 변환"""
        if not value:
            return default
        
        value = value.strip().upper()
        return value in ['TRUE', 'T', '1', 'YES', 'Y', '참', '활성']
    
    def get_keywords(self, use_cache: bool = True) -> List[Dict]:
        """키워드 조회 (캐시 지원)"""
        # 캐시 사용 및 유효성 확인
        if use_cache and self.cached_keywords and not self._should_refresh_cache():
            logger.info("💾 캐시된 키워드 사용")
            return self.cached_keywords
        
        # 시트에서 로딩 시도
        keywords = self.load_keywords_from_sheet()
        
        if keywords:
            # 성공적으로 로딩됨
            self.cached_keywords = keywords
            self.last_update = datetime.now()
            logger.info(f"✅ 키워드 캐시 업데이트: {len(keywords)}개")
        else:
            # 로딩 실패시 Fallback 사용
            logger.warning("⚠️ 시트 로딩 실패, Fallback 키워드 사용")
            keywords = self.fallback_keywords
            
            # Fallback도 캐시 (단, 짧은 시간)
            if not self.cached_keywords:
                self.cached_keywords = keywords
                self.last_update = datetime.now() - timedelta(seconds=self.cache_duration - 60)  # 1분 후 재시도
        
        return keywords
    
    def get_keywords_by_category(self, category: str = None, priority: int = None) -> List[str]:
        """카테고리 및 우선순위별 키워드 조회"""
        keywords = self.get_keywords()
        
        filtered = keywords
        
        if category:
            filtered = [k for k in filtered if k['category'].upper() == category.upper()]
        
        if priority is not None:
            filtered = [k for k in filtered if k['priority'] <= priority]
        
        # 우선순위 순으로 정렬
        filtered.sort(key=lambda x: x['priority'])
        
        result = [k['keyword'] for k in filtered]
        
        logger.info(f"🔍 필터링 결과 (category={category}, priority<={priority}): {len(result)}개")
        
        return result
    
    def get_all_keywords_list(self) -> List[str]:
        """모든 활성 키워드를 단순 리스트로 반환"""
        keywords = self.get_keywords()
        return [k['keyword'] for k in keywords]
    
    def get_priority_keywords(self, max_priority: int = 1) -> List[str]:
        """우선순위 높은 키워드만 조회"""
        return self.get_keywords_by_category(priority=max_priority)
    
    def refresh_cache(self):
        """캐시 강제 갱신"""
        logger.info("🔄 키워드 캐시 강제 갱신")
        self.last_update = None
        return self.get_keywords(use_cache=False)
    
    def test_connection(self) -> bool:
        """연결 테스트"""
        logger.info("🧪 구글시트 연결 테스트")
        
        if not GSPREAD_AVAILABLE:
            print("❌ gspread 라이브러리가 설치되지 않았습니다")
            return False
        
        if not self.credentials_file:
            print("❌ GOOGLE_SHEETS_CREDENTIALS_FILE 환경변수가 없습니다")
            return False
        
        if not self.spreadsheet_id:
            print("❌ GOOGLE_SHEETS_SPREADSHEET_ID 환경변수가 없습니다")
            return False
        
        if not os.path.exists(self.credentials_file):
            print(f"❌ 인증 파일을 찾을 수 없습니다: {self.credentials_file}")
            return False
        
        # 연결 테스트
        try:
            keywords = self.load_keywords_from_sheet()
            
            if keywords:
                print("✅ 구글시트 연결 성공")
                print(f"📊 로딩된 키워드: {len(keywords)}개")
                
                # 샘플 키워드 출력
                for i, kw in enumerate(keywords[:5], 1):
                    print(f"   {i}. {kw['keyword']} ({kw['category']}, 우선순위: {kw['priority']})")
                
                if len(keywords) > 5:
                    print(f"   ... 외 {len(keywords) - 5}개")
                
                return True
            else:
                print("❌ 키워드 로딩 실패")
                return False
                
        except Exception as e:
            print(f"❌ 연결 테스트 실패: {e}")
            return False
    
    def get_status(self) -> Dict:
        """현재 상태 정보 반환"""
        keywords = self.get_keywords()
        
        status = {
            'connected': self.client is not None,
            'spreadsheet_id': self.spreadsheet_id,
            'worksheet_name': self.worksheet_name,
            'total_keywords': len(keywords),
            'last_update': self.last_update.strftime('%Y-%m-%d %H:%M:%S') if self.last_update else None,
            'cache_valid': not self._should_refresh_cache() if self.last_update else False,
            'categories': {},
            'priorities': {}
        }
        
        # 카테고리별 통계
        for kw in keywords:
            cat = kw['category']
            if cat not in status['categories']:
                status['categories'][cat] = 0
            status['categories'][cat] += 1
        
        # 우선순위별 통계
        for kw in keywords:
            pri = kw['priority']
            if pri not in status['priorities']:
                status['priorities'][pri] = 0
            status['priorities'][pri] += 1
        
        return status
    
    def print_status(self):
        """상태 정보 출력"""
        status = self.get_status()
        
        print("\n📊 Google Sheets Manager 상태:")
        print("=" * 50)
        print(f"🔗 연결 상태: {'✅ 연결됨' if status['connected'] else '❌ 연결 안됨'}")
        print(f"📋 스프레드시트: {status['spreadsheet_id'][:20]}..." if status['spreadsheet_id'] else "❌ 설정 안됨")
        print(f"📄 워크시트: {status['worksheet_name']}")
        print(f"🔑 총 키워드: {status['total_keywords']}개")
        print(f"🕐 마지막 업데이트: {status['last_update'] or '없음'}")
        print(f"💾 캐시 상태: {'✅ 유효' if status['cache_valid'] else '❌ 만료'}")
        
        if status['categories']:
            print("\n📂 카테고리별 키워드:")
            for cat, count in status['categories'].items():
                print(f"   • {cat}: {count}개")
        
        if status['priorities']:
            print("\n⭐ 우선순위별 키워드:")
            for pri, count in sorted(status['priorities'].items()):
                print(f"   • 우선순위 {pri}: {count}개")


def main():
    """테스트 및 상태 확인"""
    import sys
    
    manager = GoogleSheetsManager()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            manager.test_connection()
        elif sys.argv[1] == "status":
            manager.print_status()
        elif sys.argv[1] == "keywords":
            keywords = manager.get_all_keywords_list()
            print(f"📋 전체 키워드 ({len(keywords)}개):")
            for i, kw in enumerate(keywords, 1):
                print(f"  {i:2d}. {kw}")
        elif sys.argv[1] == "refresh":
            manager.refresh_cache()
            print("✅ 캐시 갱신 완료")
        elif sys.argv[1] == "help":
            print("사용법:")
            print("  python3 google_sheets_manager.py test      # 연결 테스트")
            print("  python3 google_sheets_manager.py status    # 상태 확인")
            print("  python3 google_sheets_manager.py keywords  # 키워드 목록")
            print("  python3 google_sheets_manager.py refresh   # 캐시 갱신")
            print("  python3 google_sheets_manager.py help      # 도움말")
    else:
        # 기본: 상태 확인
        manager.print_status()


if __name__ == "__main__":
    main()