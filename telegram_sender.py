#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
텔레그램 메시지 전송 모듈 (기존 파일 업데이트)
"""

import requests
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class TelegramSender:
    """텔레그램 메시지 전송 클래스"""
    
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        
    def send_message(self, message, parse_mode='HTML'):
        """텔레그램 메시지 전송"""
        
        if not self.bot_token or not self.chat_id:
            logger.error("Telegram 설정이 없습니다")
            return False
        
        try:
            url = f"{self.api_url}/sendMessage"
            
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode,
                'disable_web_page_preview': True
            }
            
            response = requests.post(url, data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    logger.info("텔레그램 메시지 전송 성공")
                    return True
                else:
                    logger.error(f"텔레그램 API 오류: {result.get('description')}")
                    return False
            else:
                logger.error(f"HTTP 오류: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"텔레그램 전송 실패: {e}")
            return False
    
    def send_summary_message(self, summary_data, notion_url):
        """요약 메시지 전송 (새로운 형식으로 업데이트)"""
        
        message = f"""📰 <b>AI관련 Google News!</b>

🔗 <b>기사원문 바로가기 (아래링크클릭) :</b>
{notion_url}

📊 <b>수집 결과:</b>
• 기사 수: {summary_data['total_articles']}개
• 언론사: {summary_data['stats']['total_sources']}곳
• 수집 시간: {summary_data['collection_time']}

🏷️ <b>키워드:</b>
{' '.join(['#' + kw for kw in summary_data['keywords_found'][:10]])}

📑 <b>주요 기사:</b>"""
        
        # 상위 5개 기사 제목 추가
        for article in summary_data['articles'][:5]:
            title = article['title']
            if len(title) > 80:
                title = title[:80] + "..."
            
            message += f"\n• \"{title}\" - {article['source']}"
            message += f"\n  📰 {article['source']} | ⏰ {article['published']}"
        
        if len(summary_data['articles']) > 5:
            message += f"\n... 외 {len(summary_data['articles']) - 5}개 기사"
        
        message += f"""

🤖 <b>시스템 정보</b>
- 개발자: Joonmo Yang
- 시스템: Google News 자동화 에이전트 v1.4
- 기술: Python 3.9+ • Notion API • GoogleNewsAPI
- 처리: GoogleNews → 크롤링 → 노션 저장 → 텔레그램 알림
- 문의: davidlikescat@icloud.com

© 2025 Joonmo Yang. Google News AI Automation Tool. All rights reserved."""
        
        return self.send_message(message)
    
    def send_error_notification(self, error_message):
        """에러 알림 전송"""
        
        message = f"""❌ <b>Google News 수집 오류</b>

🚨 <b>오류 내용:</b>
{error_message}

⏰ <b>발생 시간:</b>
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

💡 <i>잠시 후 다시 시도하거나 로그를 확인해주세요</i>"""
        
        return self.send_message(message)
    
    def send_notification(self, message):
        """일반 알림 전송"""
        return self.send_message(message)

if __name__ == "__main__":
    # 테스트
    telegram = TelegramSender()
    
    test_message = """🧪 <b>텔레그램 테스트 메시지 (업데이트됨)</b>

✅ 연결 테스트 성공!
⏰ 시간: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    success = telegram.send_message(test_message)
    
    if success:
        print("✅ 텔레그램 테스트 성공!")
    else:
        print("❌ 텔레그램 테스트 실패!")
