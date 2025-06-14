#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
키워드 동적 로딩 관리자
구글시트와 하드코딩 키워드를 통합 관리
"""

import logging
from typing import List, Dict, Set
from google_sheets_manager import GoogleSheetsManager

logger = logging.getLogger(__name__)

class KeywordManager:
    """키워드 통합 관리 시스템"""
    
    def __init__(self):
        self.sheets_manager = GoogleSheetsManager()
        
        # 기본 하드코딩 키워드 (백업용)
        self.default_ai_keywords = [
            "artificial intelligence", "AI", "machine learning", "deep learning", 
            "neural network", "ChatGPT", "OpenAI", "Google AI", "인공지능", 
            "머신러닝", "딥러닝", "생성형 AI", "AI 기술", "LLM", "GPT"
        ]
        
        self.default_tech_keywords = [
            "technology", "tech", "software", "programming", "developer", 
            "기술", "소프트웨어", "개발자", "IT", "스타트업", "네이버", 
            "카카오", "삼성", "자율주행", "블록체인"
        ]
        
        # 키워드 우선순위 설정
        self.priority_keywords = ["AI", "인공지능", "ChatGPT", "생성형AI", "머신러닝"]
        
    def get_search_keywords(self, source: str = "auto", category: str = None, max_count: int = None) -> List[str]:
        """
        검색 키워드 조회
        
        Args:
            source: "sheets", "default", "auto" (기본값)
            category: 카테고리 필터 ("AI", "TECH", etc.)
            max_count: 최대 키워드 수
        """
        keywords = []
        
        try:
            if source == "sheets":
                # 구글시트에서만 로딩
                keywords = self._get_keywords_from_sheets(category)
                
            elif source == "default":
                # 기본 키워드만 사용
                keywords = self._get_default_keywords(category)
                
            else:  # auto
                # 구글시트 우선, 실패시 기본 키워드
                keywords = self._get_keywords_from_sheets(category)
                
                if not keywords:
                    logger.warning("⚠️ 구글시트 키워드 로딩 실패, 기본 키워드 사용")
                    keywords = self._get_default_keywords(category)
        
        except Exception as e:
            logger.error(f"❌ 키워드 로딩 오류: {e}")
            keywords = self._get_default_keywords(category)
        
        # 중복 제거 및 정리
        keywords = self._clean_keywords(keywords)
        
        # 우선순위 정렬
        keywords = self._sort_by_priority(keywords)
        
        # 개수 제한
        if max_count and len(keywords) > max_count:
            keywords = keywords[:max_count]
            logger.info(f"🔢 키워드 개수 제한: {max_count}개로 조정")
        
        logger.info(f"🔑 사용할 키워드 ({len(keywords)}개): {', '.join(keywords[:5])}{'...' if len(keywords) > 5 else ''}")
        
        return keywords
    
    def _get_keywords_from_sheets(self, category: str = None) -> List[str]:
        """구글시트에서 키워드 로딩"""
        try:
            if category:
                keywords = self.sheets_manager.get_keywords_by_category(category)
            else:
                keywords = self.sheets_manager.get_all_keywords_list()
            
            if keywords:
                logger.info(f"📥 구글시트에서 키워드 로딩: {len(keywords)}개")
                return keywords
            else:
                logger.warning("⚠️ 구글시트에서 키워드를 찾을 수 없습니다")
                return []
                
        except Exception as e:
            logger.error(f"❌ 구글시트 키워드 로딩 실패: {e}")
            return []
    
    def _get_default_keywords(self, category: str = None) -> List[str]:
        """기본 하드코딩 키워드 반환"""
        if category:
            category_upper = category.upper()
            if category_upper == "AI":
                keywords = self.default_ai_keywords.copy()
            elif category_upper == "TECH":
                keywords = self.default_tech_keywords.copy()
            else:
                keywords = self.default_ai_keywords + self.default_tech_keywords
        else:
            keywords = self.default_ai_keywords + self.default_tech_keywords
        
        logger.info(f"🔧 기본 키워드 사용: {len(keywords)}개")
        return keywords
    
    def _clean_keywords(self, keywords: List[str]) -> List[str]:
        """키워드 정리 및 중복 제거"""
        # 중복 제거 (대소문자 구분)
        seen = set()
        cleaned = []
        
        for keyword in keywords:
            keyword = keyword.strip()
            if keyword and keyword not in seen:
                seen.add(keyword)
                cleaned.append(keyword)
        
        return cleaned
    
    def _sort_by_priority(self, keywords: List[str]) -> List[str]:
        """우선순위 기반 키워드 정렬"""
        priority_set = set(self.priority_keywords)
        
        # 우선순위 키워드와 일반 키워드 분리
        priority_keywords = []
        regular_keywords = []
        
        for keyword in keywords:
            if keyword in priority_set:
                priority_keywords.append(keyword)
            else:
                regular_keywords.append(keyword)
        
        # 우선순위 키워드를 지정된 순서대로 정렬
        sorted_priority = []
        for priority_kw in self.priority_keywords:
            if priority_kw in priority_keywords:
                sorted_priority.append(priority_kw)
        
        # 남은 우선순위 키워드 추가
        for kw in priority_keywords:
            if kw not in sorted_priority:
                sorted_priority.append(kw)
        
        return sorted_priority + regular_keywords
    
    def get_ai_keywords_only(self) -> List[str]:
        """AI 관련 키워드만 조회"""
        return self.get_search_keywords(category="AI")
    
    def get_tech_keywords_only(self) -> List[str]:
        """기술 관련 키워드만 조회"""
        return self.get_search_keywords(category="TECH")
    
    def get_priority_keywords_only(self, max_count: int = 5) -> List[str]:
        """우선순위 높은 키워드만 조회"""
        try:
            # 구글시트에서 우선순위 1인 키워드 조회
            keywords = self.sheets_manager.get_priority_keywords(max_priority=1)
            
            if keywords:
                return keywords[:max_count]
            else:
                # Fallback: 기본 우선순위 키워드
                return self.priority_keywords[:max_count]
                
        except Exception as e:
            logger.error(f"❌ 우선순위 키워드 조회 실패: {e}")
            return self.priority_keywords[:max_count]
    
    def get_combined_keywords(self, include_sheets: bool = True, include_default: bool = True) -> List[str]:
        """구글시트와 기본 키워드 결합"""
        combined = []
        
        if include_sheets:
            try:
                sheets_keywords = self.sheets_manager.get_all_keywords_list()
                combined.extend(sheets_keywords)
                logger.info(f"📥 구글시트 키워드 추가: {len(sheets_keywords)}개")
            except Exception as e:
                logger.warning(f"⚠️ 구글시트 키워드 로딩 실패: {e}")
        
        if include_default:
            default_keywords = self.default_ai_keywords + self.default_tech_keywords
            combined.extend(default_keywords)
            logger.info(f"🔧 기본 키워드 추가: {len(default_keywords)}개")
        
        # 중복 제거 및 정리
        combined = self._clean_keywords(combined)
        combined = self._sort_by_priority(combined)
        
        logger.info(f"🔗 통합 키워드: {len(combined)}개")
        
        return combined
    
    def validate_keywords(self, keywords: List[str]) -> Dict:
        """키워드 유효성 검증"""
        validation = {
            'total_count': len(keywords),
            'valid_keywords': [],
            'invalid_keywords': [],
            'duplicates': [],
            'korean_count': 0,
            'english_count': 0,
            'recommendations': []
        }
        
        seen = set()
        
        for keyword in keywords:
            keyword = keyword.strip()
            
            # 빈 키워드 체크
            if not keyword:
                validation['invalid_keywords'].append("(빈 키워드)")
                continue
            
            # 중복 체크
            if keyword in seen:
                validation['duplicates'].append(keyword)
                continue
            
            seen.add(keyword)
            validation['valid_keywords'].append(keyword)
            
            # 언어 분류
            if any('\u3131' <= char <= '\u3163' or '\uac00' <= char <= '\ud7a3' for char in keyword):
                validation['korean_count'] += 1
            else:
                validation['english_count'] += 1
        
        # 권장사항 생성
        if validation['total_count'] < 5:
            validation['recommendations'].append("키워드가 너무 적습니다. 최소 5개 이상 권장")
        
        if validation['total_count'] > 50:
            validation['recommendations'].append("키워드가 너무 많습니다. 성능상 30개 이하 권장")
        
        if validation['korean_count'] == 0:
            validation['recommendations'].append("한국어 키워드를 추가하는 것을 권장합니다")
        
        if validation['english_count'] == 0:
            validation['recommendations'].append("영어 키워드를 추가하는 것을 권장합니다")
        
        return validation
    
    def get_keyword_statistics(self) -> Dict:
        """키워드 통계 정보"""
        try:
            sheets_keywords = self.sheets_manager.get_all_keywords_list()
            sheets_status = self.sheets_manager.get_status()
        except:
            sheets_keywords = []
            sheets_status = {}
        
        default_keywords = self.default_ai_keywords + self.default_tech_keywords
        combined_keywords = self.get_combined_keywords()
        
        stats = {
            'sheets': {
                'total': len(sheets_keywords),
                'connected': sheets_status.get('connected', False),
                'categories': sheets_status.get('categories', {}),
                'last_update': sheets_status.get('last_update')
            },
            'default': {
                'ai_keywords': len(self.default_ai_keywords),
                'tech_keywords': len(self.default_tech_keywords),
                'total': len(default_keywords)
            },
            'combined': {
                'total': len(combined_keywords),
                'unique_count': len(set(combined_keywords))
            },
            'priority': {
                'count': len(self.priority_keywords),
                'keywords': self.priority_keywords
            }
        }
        
        return stats
    
    def print_statistics(self):
        """키워드 통계 출력"""
        stats = self.get_keyword_statistics()
        
        print("\n📊 키워드 관리자 통계:")
        print("=" * 50)
        
        print(f"\n📥 구글시트 키워드:")
        print(f"   • 연결 상태: {'✅ 연결됨' if stats['sheets']['connected'] else '❌ 연결 안됨'}")
        print(f"   • 총 키워드: {stats['sheets']['total']}개")
        print(f"   • 마지막 업데이트: {stats['sheets']['last_update'] or '없음'}")
        
        if stats['sheets']['categories']:
            print("   • 카테고리별:")
            for cat, count in stats['sheets']['categories'].items():
                print(f"     - {cat}: {count}개")
        
        print(f"\n🔧 기본 키워드:")
        print(f"   • AI 키워드: {stats['default']['ai_keywords']}개")
        print(f"   • 기술 키워드: {stats['default']['tech_keywords']}개")
        print(f"   • 총합: {stats['default']['total']}개")
        
        print(f"\n🔗 통합 키워드:")
        print(f"   • 전체: {stats['combined']['total']}개")
        print(f"   • 고유: {stats['combined']['unique_count']}개")
        
        print(f"\n⭐ 우선순위 키워드:")
        print(f"   • 개수: {stats['priority']['count']}개")
        print(f"   • 목록: {', '.join(stats['priority']['keywords'])}")
    
    def refresh_sheets_cache(self):
        """구글시트 캐시 갱신"""
        try:
            self.sheets_manager.refresh_cache()
            logger.info("✅ 구글시트 캐시 갱신 완료")
        except Exception as e:
            logger.error(f"❌ 캐시 갱신 실패: {e}")


def main():
    """테스트 및 상태 확인"""
    import sys
    
    manager = KeywordManager()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            print("🧪 키워드 로딩 테스트")
            
            # 자동 모드 테스트
            keywords = manager.get_search_keywords()
            print(f"✅ 자동 모드: {len(keywords)}개 키워드")
            
            # 구글시트 모드 테스트
            try:
                sheets_keywords = manager.get_search_keywords(source="sheets")
                print(f"✅ 구글시트 모드: {len(sheets_keywords)}개 키워드")
            except:
                print("❌ 구글시트 모드 실패")
            
            # 기본 모드 테스트
            default_keywords = manager.get_search_keywords(source="default")
            print(f"✅ 기본 모드: {len(default_keywords)}개 키워드")
            
        elif sys.argv[1] == "stats":
            manager.print_statistics()
            
        elif sys.argv[1] == "keywords":
            keywords = manager.get_search_keywords()
            print(f"📋 현재 키워드 ({len(keywords)}개):")
            for i, kw in enumerate(keywords, 1):
                print(f"  {i:2d}. {kw}")
                
        elif sys.argv[1] == "priority":
            priority_keywords = manager.get_priority_keywords_only()
            print(f"⭐ 우선순위 키워드 ({len(priority_keywords)}개):")
            for i, kw in enumerate(priority_keywords, 1):
                print(f"  {i}. {kw}")
                
        elif sys.argv[1] == "validate":
            keywords = manager.get_search_keywords()
            validation = manager.validate_keywords(keywords)
            
            print("🔍 키워드 유효성 검증:")
            print(f"   • 총 키워드: {validation['total_count']}개")
            print(f"   • 유효한 키워드: {len(validation['valid_keywords'])}개")
            print(f"   • 무효한 키워드: {len(validation['invalid_keywords'])}개")
            print(f"   • 중복 키워드: {len(validation['duplicates'])}개")
            print(f"   • 한국어: {validation['korean_count']}개")
            print(f"   • 영어: {validation['english_count']}개")
            
            if validation['recommendations']:
                print("\n💡 권장사항:")
                for rec in validation['recommendations']:
                    print(f"   • {rec}")
                    
        elif sys.argv[1] == "refresh":
            manager.refresh_sheets_cache()
            print("✅ 구글시트 캐시 갱신 완료")
            
        elif sys.argv[1] == "help":
            print("사용법:")
            print("  python3 keyword_manager.py test       # 키워드 로딩 테스트")
            print("  python3 keyword_manager.py stats      # 통계 정보")
            print("  python3 keyword_manager.py keywords   # 현재 키워드 목록")
            print("  python3 keyword_manager.py priority   # 우선순위 키워드")
            print("  python3 keyword_manager.py validate   # 키워드 유효성 검증")
            print("  python3 keyword_manager.py refresh    # 구글시트 캐시 갱신")
            print("  python3 keyword_manager.py help       # 도움말")
    else:
        # 기본: 통계 출력
        manager.print_statistics()


if __name__ == "__main__":
    main()