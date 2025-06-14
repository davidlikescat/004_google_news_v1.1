#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
개선된 Google News AI 스케줄러
한국시간 기준 정확한 스케줄링 + 구글시트 키워드 연동
"""

import schedule
import time
import subprocess
import sys
import os
import logging
import pytz
from datetime import datetime, timedelta
from config import Config

# 키워드 관리자 import (선택적)
try:
    from keyword_manager import KeywordManager
    KEYWORD_MANAGER_AVAILABLE = True
except ImportError:
    KEYWORD_MANAGER_AVAILABLE = False
    print("⚠️ keyword_manager.py가 없습니다. 기본 키워드 사용")

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ImprovedScheduler:
    """개선된 Google News AI 스케줄러"""
    
    def __init__(self):
        self.config = Config
        self.timezone = pytz.timezone(self.config.TIMEZONE)
        self.schedule_time = self.config.SCHEDULE_TIME
        
        # 키워드 관리자 초기화
        self.keyword_manager = None
        if KEYWORD_MANAGER_AVAILABLE:
            try:
                self.keyword_manager = KeywordManager()
                logger.info("✅ 키워드 관리자 초기화 완료")
            except Exception as e:
                logger.warning(f"⚠️ 키워드 관리자 초기화 실패: {e}")
        
        # 실행 상태 관리
        self.is_running = False
        self.last_execution = None
        self.execution_count = 0
        self.success_count = 0
        
        # 스크립트 경로
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.main_script = os.path.join(self.script_dir, 'main.py')
        
        # 스케줄 설정
        self.setup_schedule()
    
    def get_korea_time(self) -> datetime:
        """현재 한국시간 반환"""
        return datetime.now(self.timezone)
    
    def setup_schedule(self):
        """한국시간 기준 스케줄 설정"""
        try:
            # 기존 스케줄 초기화
            schedule.clear()
            
            # 한국시간 기준 스케줄 등록
            schedule.every().day.at(self.schedule_time).do(self.run_news_automation)
            
            korea_time = self.get_korea_time()
            next_run = schedule.next_run()
            
            logger.info("📅 스케줄 설정 완료:")
            logger.info(f"   • 실행 시간: 매일 {self.schedule_time} (한국시간)")
            logger.info(f"   • 현재 한국시간: {korea_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            
            if next_run:
                # UTC 시간을 한국시간으로 변환
                next_run_kst = next_run.replace(tzinfo=pytz.UTC).astimezone(self.timezone)
                logger.info(f"   • 다음 실행: {next_run_kst.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            
            # 키워드 상태 확인
            if self.keyword_manager:
                try:
                    keywords = self.keyword_manager.get_search_keywords()
                    logger.info(f"🔑 사용 예정 키워드: {len(keywords)}개")
                    logger.info(f"   주요 키워드: {', '.join(keywords[:5])}{'...' if len(keywords) > 5 else ''}")
                except Exception as e:
                    logger.warning(f"⚠️ 키워드 미리보기 실패: {e}")
            
        except Exception as e:
            logger.error(f"❌ 스케줄 설정 실패: {e}")
            raise
    
    def run_news_automation(self):
        """뉴스 자동화 실행"""
        if self.is_running:
            logger.warning("⚠️ 이미 실행 중입니다. 중복 실행 방지")
            return False
        
        try:
            self.is_running = True
            self.execution_count += 1
            
            start_time = self.get_korea_time()
            logger.info("🚀 Google News AI 자동화 시작")
            logger.info(f"📍 시작 시간: {start_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            logger.info(f"🔢 실행 횟수: {self.execution_count}회")
            
            # 키워드 상태 확인 및 갱신
            if self.keyword_manager:
                try:
                    # 키워드 캐시 갱신 (매 실행시)
                    keywords = self.keyword_manager.get_search_keywords(source="auto")
                    logger.info(f"🔑 로딩된 키워드: {len(keywords)}개")
                    
                    # 주요 키워드 로그
                    if keywords:
                        logger.info(f"   사용 키워드: {', '.join(keywords[:10])}{'...' if len(keywords) > 10 else ''}")
                    
                except Exception as e:
                    logger.warning(f"⚠️ 키워드 로딩 중 오류: {e}")
                    logger.info("🔧 기본 키워드로 진행합니다")
            
            # main.py 실행
            logger.info(f"▶️ 메인 스크립트 실행: {self.main_script}")
            
            result = subprocess.run(
                [sys.executable, 'main.py'],
                capture_output=True,
                text=True,
                timeout=300,  # 5분 타임아웃
                cwd=self.script_dir
            )
            
            end_time = self.get_korea_time()
            duration = (end_time - start_time).total_seconds()
            
            # 실행 결과 처리
            if result.returncode == 0:
                self.success_count += 1
                self.last_execution = end_time
                
                logger.info("✅ Google News AI 자동화 성공")
                logger.info(f"⏱️ 소요시간: {duration:.1f}초")
                logger.info(f"🕐 완료시간: {end_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
                logger.info(f"📊 성공률: {self.success_count}/{self.execution_count} ({self.success_count/self.execution_count*100:.1f}%)")
                
                # 성공 시 결과 요약 로그
                if result.stdout:
                    output_lines = result.stdout.strip().split('\n')
                    logger.info("📋 실행 결과 요약:")
                    for line in output_lines[-5:]:  # 마지막 5줄만
                        if line.strip():
                            logger.info(f"   {line}")
                
                return True
                
            else:
                logger.error("❌ Google News AI 자동화 실패")
                logger.error(f"Exit code: {result.returncode}")
                logger.error(f"⏱️ 소요시간: {duration:.1f}초")
                
                if result.stderr:
                    logger.error(f"Error output:")
                    for line in result.stderr.split('\n')[:10]:  # 최대 10줄
                        if line.strip():
                            logger.error(f"   {line}")
                
                # 실패 알림 전송 시도
                self._send_failure_notification(result.stderr)
                
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("⏰ 실행 시간 초과 (5분)")
            self._send_failure_notification("실행 시간 초과")
            return False
            
        except Exception as e:
            logger.error(f"❌ 예상치 못한 오류: {e}")
            self._send_failure_notification(str(e))
            return False
            
        finally:
            self.is_running = False
    
    def _send_failure_notification(self, error_message: str):
        """실패 알림 전송"""
        try:
            # 간단한 텔레그램 알림 전송
            notification_script = f"""
import sys
import os
sys.path.append('{self.script_dir}')
try:
    from telegram_sender import TelegramSender
    telegram = TelegramSender()
    telegram.send_error_notification('스케줄 실행 실패: {error_message[:100]}')
    print('실패 알림 전송 완료')
except Exception as e:
    print(f'알림 전송 실패: {{e}}')
"""
            subprocess.run([sys.executable, '-c', notification_script], timeout=30, cwd=self.script_dir)
            logger.info("📤 실패 알림 전송 완료")
            
        except Exception as e:
            logger.error(f"❌ 실패 알림 전송 실패: {e}")
    
    def get_status(self) -> dict:
        """현재 상태 반환"""
        korea_time = self.get_korea_time()
        next_run = schedule.next_run()
        
        status = {
            'current_time_kst': korea_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
            'schedule_time': self.schedule_time,
            'is_running': self.is_running,
            'execution_count': self.execution_count,
            'success_count': self.success_count,
            'success_rate': f"{self.success_count/self.execution_count*100:.1f}%" if self.execution_count > 0 else "0%",
            'last_execution': self.last_execution.strftime('%Y-%m-%d %H:%M:%S %Z') if self.last_execution else None,
            'next_run_utc': next_run.strftime('%Y-%m-%d %H:%M:%S UTC') if next_run else None,
            'keyword_manager': {
                'available': KEYWORD_MANAGER_AVAILABLE,
                'initialized': self.keyword_manager is not None
            }
        }
        
        # 다음 실행 시간을 한국시간으로 변환
        if next_run:
            next_run_kst = next_run.replace(tzinfo=pytz.UTC).astimezone(self.timezone)
            status['next_run_kst'] = next_run_kst.strftime('%Y-%m-%d %H:%M:%S %Z')
        
        # 키워드 상태 추가
        if self.keyword_manager:
            try:
                keyword_stats = self.keyword_manager.get_keyword_statistics()
                status['keywords'] = {
                    'sheets_connected': keyword_stats['sheets']['connected'],
                    'total_sheets_keywords': keyword_stats['sheets']['total'],
                    'total_default_keywords': keyword_stats['default']['total'],
                    'combined_keywords': keyword_stats['combined']['total']
                }
            except:
                status['keywords'] = {'error': 'Failed to load keyword statistics'}
        
        return status
    
    def print_status(self):
        """상태 정보 출력"""
        status = self.get_status()
        
        print("\n📊 Google News AI 스케줄러 상태:")
        print("=" * 60)
        print(f"🕐 현재 한국시간: {status['current_time_kst']}")
        print(f"⏰ 스케줄 시간: 매일 {status['schedule_time']}")
        print(f"🔄 현재 실행 상태: {'실행 중' if status['is_running'] else '대기 중'}")
        
        if status.get('next_run_kst'):
            print(f"⏭️ 다음 실행: {status['next_run_kst']}")
        
        print(f"\n📈 실행 통계:")
        print(f"   • 총 실행 횟수: {status['execution_count']}회")
        print(f"   • 성공 횟수: {status['success_count']}회")
        print(f"   • 성공률: {status['success_rate']}")
        
        if status['last_execution']:
            print(f"   • 마지막 실행: {status['last_execution']}")
        
        print(f"\n🔑 키워드 관리:")
        kw_mgr = status['keyword_manager']
        print(f"   • 키워드 관리자: {'✅ 사용 가능' if kw_mgr['available'] else '❌ 사용 불가'}")
        print(f"   • 초기화 상태: {'✅ 완료' if kw_mgr['initialized'] else '❌ 실패'}")
        
        if 'keywords' in status:
            kw = status['keywords']
            if 'error' not in kw:
                print(f"   • 구글시트 연결: {'✅' if kw['sheets_connected'] else '❌'}")
                print(f"   • 시트 키워드: {kw['total_sheets_keywords']}개")
                print(f"   • 기본 키워드: {kw['total_default_keywords']}개")
                print(f"   • 통합 키워드: {kw['combined_keywords']}개")
            else:
                print(f"   • 키워드 상태: ❌ {kw['error']}")
    
    def test_execution(self):
        """테스트 실행"""
        print("🧪 Google News AI 테스트 실행")
        print("=" * 50)
        
        # 키워드 테스트
        if self.keyword_manager:
            try:
                print("🔑 키워드 테스트...")
                keywords = self.keyword_manager.get_search_keywords()
                print(f"✅ 키워드 로딩 성공: {len(keywords)}개")
                print(f"   주요 키워드: {', '.join(keywords[:5])}")
            except Exception as e:
                print(f"❌ 키워드 테스트 실패: {e}")
        
        # 실제 실행 테스트
        print("\n🚀 메인 스크립트 테스트 실행...")
        success = self.run_news_automation()
        
        if success:
            print("✅ 테스트 실행 성공!")
        else:
            print("❌ 테스트 실행 실패!")
        
        return success
    
    def run_scheduler(self):
        """스케줄러 메인 루프"""
        logger.info("🚀 Google News AI 스케줄러 시작")
        logger.info("=" * 60)
        logger.info(f"🔧 프로젝트: {self.config.PROJECT_CODE}")
        logger.info(f"⚙️ 시스템: {self.config.SYSTEM_NAME} {self.config.SYSTEM_VERSION}")
        logger.info(f"👤 개발자: {self.config.DEVELOPER_NAME}")
        
        self.print_status()
        
        print(f"\n🎯 실행 방법:")
        print("=" * 50)
        korea_time = self.get_korea_time()
        next_run = schedule.next_run()
        
        if next_run:
            next_run_kst = next_run.replace(tzinfo=pytz.UTC).astimezone(self.timezone)
            time_until_next = next_run_kst - korea_time
            hours, remainder = divmod(time_until_next.total_seconds(), 3600)
            minutes, _ = divmod(remainder, 60)
            
            print(f"📅 자동 실행: {next_run_kst.strftime('%Y-%m-%d %H:%M:%S')} ({int(hours)}시간 {int(minutes)}분 후)")
        
        print("⚡ 수동 실행: python3 main.py")
        print("📊 상태 확인: python3 simple_scheduler.py status")
        print("🧪 테스트 실행: python3 simple_scheduler.py test")
        print("⏹️ 종료: Ctrl+C")
        
        try:
            logger.info("⏳ 스케줄 대기 중... (Ctrl+C로 종료)")
            
            while True:
                schedule.run_pending()
                time.sleep(60)  # 1분마다 체크
                
        except KeyboardInterrupt:
            logger.info("⏹️ 스케줄러 종료")
            self.print_status()
        except Exception as e:
            logger.error(f"❌ 스케줄러 오류: {e}")
            return False
        
        return True
    
    def force_run(self):
        """강제 실행"""
        print("⚡ 강제 실행 시작...")
        return self.run_news_automation()


def main():
    """메인 실행"""
    import sys
    
    scheduler = ImprovedScheduler()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "test":
            scheduler.test_execution()
            
        elif command == "status":
            scheduler.print_status()
            
        elif command == "run":
            success = scheduler.force_run()
            if success:
                print("✅ 강제 실행 성공")
            else:
                print("❌ 강제 실행 실패")
                
        elif command == "keywords":
            if scheduler.keyword_manager:
                try:
                    scheduler.keyword_manager.print_statistics()
                except Exception as e:
                    print(f"❌ 키워드 정보 조회 실패: {e}")
            else:
                print("❌ 키워드 관리자가 사용 불가능합니다")
                
        elif command == "refresh":
            if scheduler.keyword_manager:
                try:
                    scheduler.keyword_manager.refresh_sheets_cache()
                    print("✅ 키워드 캐시 갱신 완료")
                except Exception as e:
                    print(f"❌ 캐시 갱신 실패: {e}")
            else:
                print("❌ 키워드 관리자가 사용 불가능합니다")
                
        elif command == "help":
            print("사용법:")
            print("  python3 simple_scheduler.py          # 스케줄러 시작")
            print("  python3 simple_scheduler.py test     # 테스트 실행")
            print("  python3 simple_scheduler.py status   # 상태 확인")
            print("  python3 simple_scheduler.py run      # 강제 실행")
            print("  python3 simple_scheduler.py keywords # 키워드 정보")
            print("  python3 simple_scheduler.py refresh  # 키워드 캐시 갱신")
            print("  python3 simple_scheduler.py help     # 도움말")
            
        else:
            print(f"❌ 알 수 없는 명령어: {command}")
            print("python3 simple_scheduler.py help 로 도움말을 확인하세요")
    else:
        # 기본: 스케줄러 실행
        scheduler.run_scheduler()


if __name__ == "__main__":
    main()