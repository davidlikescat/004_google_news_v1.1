#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
간단한 Notion 저장 모듈
"""

import requests
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SimpleNotion:
    """간단한 Notion 페이지 생성 클래스"""
    
    def __init__(self):
        self.api_key = os.getenv('NOTION_API_KEY')
        self.database_id = os.getenv('NOTION_DATABASE_ID')
        self.page_id = os.getenv('NOTION_PAGE_ID')
        
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Notion-Version': '2022-06-28'
        }
    
    def save_to_notion(self, summary_data, html_content=None):
        """Notion에 데이터 저장"""
        
        if not self.api_key or not self.database_id:
            logger.error("Notion API 설정이 없습니다")
            return None
        
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            current_time = datetime.now().strftime('%H:%M')
            
            # 페이지 제목
            title = f"🤖 Google News AI 리포트 - {today} {current_time}"
            
            # 최소한의 속성으로 페이지 생성
            page_data = {
                "parent": {"database_id": self.database_id},
                "properties": {
                    "title": {  # Notion 데이터베이스의 실제 제목 속성명
                        "title": [
                            {
                                "type": "text",
                                "text": {"content": title}
                            }
                        ]
                    }
                }
            }
            
            # 추가 속성들 (있으면 추가, 없으면 무시)
            try:
                # 날짜 속성
                if "Date" in self._get_database_properties():
                    page_data["properties"]["Date"] = {
                        "date": {"start": today}
                    }
                
                # 기사 수
                if "Articles" in self._get_database_properties():
                    page_data["properties"]["Articles"] = {
                        "number": summary_data.get('total_articles', 0)
                    }
                
                # 카테고리
                if "Category" in self._get_database_properties():
                    page_data["properties"]["Category"] = {
                        "select": {"name": "AI 뉴스"}
                    }
                
            except Exception as e:
                logger.warning(f"추가 속성 설정 중 오류 (무시됨): {e}")
            
            # Notion API로 페이지 생성
            url = "https://api.notion.com/v1/pages"
            response = requests.post(url, headers=self.headers, json=page_data, timeout=30)
            
            if response.status_code == 200:
                page_result = response.json()
                page_url = page_result.get('url', '')
                
                # 페이지 내용 추가
                if page_result.get('id'):
                    self._add_page_content(page_result['id'], summary_data)
                
                logger.info(f"Notion 페이지 생성 성공: {page_url}")
                return page_url
            else:
                logger.error(f"Notion 페이지 생성 실패: {response.status_code}")
                logger.error(f"응답: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Notion 저장 중 오류: {e}")
            return None
    
    def _get_database_properties(self):
        """데이터베이스 속성 확인"""
        try:
            url = f"https://api.notion.com/v1/databases/{self.database_id}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                db_info = response.json()
                return db_info.get('properties', {}).keys()
            else:
                return []
        except:
            return []
    
    def _add_page_content(self, page_id, summary_data):
        """페이지에 상세 내용 추가 (새로운 형식)"""
        try:
            # 페이지 블록 내용 구성
            blocks = []
            
            # 메인 헤더
            blocks.append({
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": f"📰 주요 AI 뉴스 ({summary_data.get('total_articles', 0)}개)"}
                        }
                    ]
                }
            })
            
            # 각 기사를 상세하게 추가
            for i, article in enumerate(summary_data.get('articles', []), 1):
                # 기사 제목 (헤딩)
                title = article.get('title', 'No Title')
                source = article.get('source', 'Unknown')
                
                blocks.append({
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": f"{i}. \"{title}\" - {source}"}
                            }
                        ]
                    }
                })
                
                # 메타 정보 (출처, 시간, 카테고리)
                published = article.get('published', 'Unknown')
                meta_text = f"📍 {source} | ⏰ {published} | 🏷️ AI 뉴스"
                
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": meta_text}
                            }
                        ]
                    }
                })
                
                # 기사 첫 문장 (굵게)
                content = article.get('content', '')
                first_sentence = self._extract_first_sentence(content)
                
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": "💡 "},
                                "annotations": {"bold": True}
                            },
                            {
                                "type": "text",
                                "text": {"content": first_sentence}
                            }
                        ]
                    }
                })
                
                # 기사 URL을 bookmark 블록으로 추가
                article_url = article.get('url', '')
                if article_url:
                    blocks.append({
                        "object": "block",
                        "type": "bookmark",
                        "bookmark": {
                            "url": article_url
                        }
                    })
                
                # 키워드 태그
                keywords = self._extract_keywords_for_article(article, summary_data.get('keywords_found', []))
                if keywords:
                    keyword_text = " ".join([f"#{kw}" for kw in keywords])
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {"content": f"🏷️ {keyword_text}"},
                                    "annotations": {"color": "blue"}
                                }
                            ]
                        }
                    })
                
                # 구분선 (마지막 기사가 아닌 경우)
                if i < len(summary_data.get('articles', [])):
                    blocks.append({
                        "object": "block",
                        "type": "divider",
                        "divider": {}
                    })
            
            # 전체 키워드 요약
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "🏷️ 주요 키워드"}
                        }
                    ]
                }
            })
            
            if summary_data.get('keywords_found'):
                keyword_text = " ".join([f"#{kw}" for kw in summary_data['keywords_found'][:15]])
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": keyword_text},
                                "annotations": {"bold": True, "color": "blue"}
                            }
                        ]
                    }
                })
            
            # 수집 정보
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "📊 수집 정보"}
                        }
                    ]
                }
            })
            
            collection_info = f"""• 수집 시간: {summary_data.get('collection_time', 'Unknown')}
• 총 기사 수: {summary_data.get('total_articles', 0)}개
• 언론사 수: {summary_data.get('stats', {}).get('total_sources', 0)}곳
• 발견된 키워드: {len(summary_data.get('keywords_found', []))}개"""
            
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": collection_info}
                        }
                    ]
                }
            })
            
            # ⭐ Footer 추가 (시스템 정보)
            blocks.append({
                "object": "block",
                "type": "divider",
                "divider": {}
            })
            
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "🤖 시스템 정보"},
                            "annotations": {"bold": True}
                        }
                    ]
                }
            })
            
            # 시스템 정보 내용
            system_info = """• 개발자: JoonmoYang
• 시스템: Google News 자동화 에이전트 v1.4
• 기술: Python 3.9+ • Notion API • GoogleNewsAPI
• 처리: GoogleNews → 크롤링 → 노션 저장 → 텔레그램 알림
• 문의: davidlikescat@icloud.com"""
            
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": system_info}
                        }
                    ]
                }
            })
            
            # 저작권 정보
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "© 2025 JoonmoYang. Google News AI Automation Tool. All rights reserved."},
                            "annotations": {"italic": True, "color": "gray"}
                        }
                    ]
                }
            })
            
            # 블록을 페이지에 추가 (최대 100개씩 나누어서)
            self._add_blocks_to_page(page_id, blocks)
                
        except Exception as e:
            logger.warning(f"Notion 페이지 내용 추가 중 오류: {e}")
    
    def _extract_first_sentence(self, content):
        """기사 내용에서 첫 번째 문장 추출 (HTML 태그 제거)"""
        if not content:
            return "기사 내용을 확인할 수 없습니다."
        
        import re
        
        # HTML 태그 제거
        clean_content = re.sub(r'<[^>]+>', '', content)
        # 특수 문자 정리
        clean_content = re.sub(r'&[a-zA-Z0-9#]+;', '', clean_content)
        # 연속된 공백 정리
        clean_content = re.sub(r'\s+', ' ', clean_content)
        # 줄바꿈 정리
        clean_content = clean_content.replace('\n', ' ').replace('\r', '')
        
        # 첫 번째 문장 추출 (최대 150자)
        sentences = clean_content.split('.')
        first_sentence = sentences[0].strip()
        
        # 너무 짧거나 의미없는 내용 필터링
        if len(first_sentence) < 20 and len(sentences) > 1:
            # 두 번째 문장도 포함
            second_sentence = sentences[1].strip()
            first_sentence = f"{first_sentence}. {second_sentence}"
        
        # 최대 길이 제한
        if len(first_sentence) > 150:
            first_sentence = first_sentence[:150] + "..."
        
        # 빈 문장이면 기본 메시지
        if not first_sentence.strip():
            return "기사 내용을 확인할 수 없습니다."
        
        return first_sentence.strip()
    
    def _extract_keywords_for_article(self, article, all_keywords):
        """기사별 관련 키워드 추출"""
        article_text = (article.get('title', '') + ' ' + article.get('content', '')).lower()
        found_keywords = []
        
        for keyword in all_keywords[:10]:  # 상위 10개 키워드만 확인
            if keyword.lower() in article_text:
                found_keywords.append(keyword)
        
        # 기본 키워드가 없으면 AI 추가
        if not found_keywords:
            found_keywords.append('AI')
        
        return found_keywords[:5]  # 최대 5개만 반환
    
    def _add_blocks_to_page(self, page_id, blocks):
        """블록을 페이지에 추가 (100개씩 나누어서)"""
        try:
            # Notion API는 한 번에 최대 100개 블록만 추가 가능
            chunk_size = 100
            
            for i in range(0, len(blocks), chunk_size):
                chunk = blocks[i:i + chunk_size]
                
                url = f"https://api.notion.com/v1/blocks/{page_id}/children"
                response = requests.patch(
                    url, 
                    headers=self.headers, 
                    json={"children": chunk}, 
                    timeout=30
                )
                
                if response.status_code == 200:
                    logger.info(f"Notion 블록 {i+1}-{min(i+chunk_size, len(blocks))} 추가 성공")
                else:
                    logger.warning(f"Notion 블록 추가 실패: {response.status_code}")
                    logger.warning(f"응답: {response.text}")
                    
        except Exception as e:
            logger.warning(f"Notion 블록 추가 중 오류: {e}")

# 기존 NotionSaver와 호환성을 위한 별칭
NotionSaver = SimpleNotion

if __name__ == "__main__":
    # 테스트
    notion = SimpleNotion()
    
    # 테스트 데이터
    test_data = {
        'total_articles': 5,
        'collection_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'keywords_found': ['AI', 'machine learning', 'ChatGPT'],
        'stats': {'total_sources': 3},
        'articles': [
            {'title': '테스트 기사 1', 'source': '테스트 뉴스'},
            {'title': '테스트 기사 2', 'source': '기술 신문'}
        ]
    }
    
    url = notion.save_to_notion(test_data)
    
    if url:
        print(f"✅ Notion 테스트 성공: {url}")
    else:
        print("❌ Notion 테스트 실패!")