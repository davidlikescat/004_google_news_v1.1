# 🔧 Google News AI 시스템 구조 수정 계획

## 📋 수정 요구사항
1. **한국시간 기준 07:30 AM 정확한 자동발송**
2. **하드코딩 키워드 → 구글시트 데이터테이블 참조**

## 🗂️ 새로운 파일 구조

```
004_google_news_ai/
├── main.py                      # 메인 실행 파일
├── config.py                    # 설정 관리 (수정)
├── google_news_collector.py     # Google News 수집기
├── article_crawler.py           # 기사 크롤링
├── ai_summarizer.py            # AI 요약 생성
├── artifact_generator.py       # 리포트 생성
├── notion_saver.py             # Notion 저장
├── telegram_sender.py          # Telegram 전송
├── simple_scheduler.py         # 스케줄러 (수정)
├── master_controller.py        # 마스터 컨트롤러 (수정)
├── discord_trigger.py          # Discord 트리거
│
├── 🆕 google_sheets_manager.py   # 구글시트 연동 관리
├── 🆕 keyword_manager.py         # 키워드 동적 로딩 관리
│
├── requirements.txt            # 의존성 (수정)
├── .env                        # 환경 변수 (수정)
├── .env.example               # 환경 변수 예제 (수정)
└── README.md                   # 문서
```

## 🔧 주요 수정사항

### 1. 시간대 처리 개선
- **현재 문제**: schedule 라이브러리가 로컬 시스템 시간 사용
- **해결 방안**: pytz 사용한 명시적 한국시간 처리
- **개선 효과**: GCP VM 환경에서도 정확한 한국시간 기준 실행

### 2. 구글시트 키워드 연동
- **새로운 기능**: Google Sheets API 연동
- **동적 키워드**: 시트에서 실시간 키워드 로딩
- **Fallback 처리**: 시트 접속 실패시 기본 키워드 사용

### 3. 환경변수 추가
```env
# 기존 환경변수...
OPENAI_API_KEY=your_openai_api_key
NOTION_API_KEY=your_notion_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token

# 🆕 구글시트 연동
GOOGLE_SHEETS_CREDENTIALS_FILE=path/to/service_account.json
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id
GOOGLE_SHEETS_WORKSHEET_NAME=keywords

# 🆕 시간대 설정
TIMEZONE=Asia/Seoul
SCHEDULE_TIME=07:30
```

## 📊 구글시트 테이블 구조

### 권장 시트 구조
| A (keyword) | B (category) | C (priority) | D (active) |
|-------------|--------------|--------------|------------|
| 인공지능    | AI           | 1            | TRUE       |
| ChatGPT     | AI           | 1            | TRUE       |
| 생성형AI    | AI           | 1            | TRUE       |
| 네이버      | TECH         | 2            | TRUE       |
| 카카오      | TECH         | 2            | TRUE       |
| 삼성        | CORP         | 3            | FALSE      |

### 컬럼 설명
- **keyword**: 검색할 키워드
- **category**: 카테고리 분류 (AI, TECH, CORP 등)
- **priority**: 우선순위 (1=최고, 3=최저)
- **active**: 활성화 여부 (TRUE/FALSE)

## 🚀 개발 단계

### Phase 1: 구글시트 연동 기반 구축
1. `google_sheets_manager.py` 개발
2. `keyword_manager.py` 개발
3. 환경변수 및 설정 업데이트

### Phase 2: 시간대 처리 개선
1. `simple_scheduler.py` 시간대 처리 개선
2. `master_controller.py` 로깅 개선
3. 한국시간 기준 정확한 스케줄링

### Phase 3: 통합 테스트 및 배포
1. 로컬 환경 테스트
2. GCP VM 환경 테스트
3. 실운영 배포

## 🔄 작업 플로우 변경

### 기존 플로우
```
하드코딩 키워드 → Google News 검색 → 기사 수집 → AI 요약 → Notion 저장 → Telegram 알림
```

### 🆕 새로운 플로우
```
구글시트 키워드 로딩 → Google News 검색 → 기사 수집 → AI 요약 → Notion 저장 → Telegram 알림
                ↑
         (실시간 키워드 업데이트)
```

## 📈 예상 효과

### 1. 운영 편의성 향상
- 코드 수정 없이 키워드 변경 가능
- 실시간 키워드 우선순위 조정
- 비개발자도 키워드 관리 가능

### 2. 시스템 안정성 향상
- 정확한 한국시간 기준 실행
- 구글시트 접속 실패시 Fallback 처리
- 로깅 개선으로 디버깅 용이

### 3. 확장성 향상
- 키워드 카테고리별 분류 가능
- 우선순위 기반 검색 가능
- 향후 다양한 데이터 소스 연동 기반

## ⚠️ 주의사항

### 1. Google Sheets API 설정
- Service Account 키 발급 필요
- 시트 공유 권한 설정 필요
- API 할당량 모니터링 필요

### 2. 보안 고려사항
- Service Account JSON 키 보안 관리
- 환경변수 암호화 고려
- 시트 접근 권한 최소화

### 3. 성능 고려사항
- 시트 조회 캐싱 처리
- API 호출 빈도 최적화
- 네트워크 오류 대응

## 🎯 다음 단계

1. **즉시 시작 가능**: 구글시트 연동 개발
2. **병렬 진행 가능**: 시간대 처리 개선
3. **완료 후**: 통합 테스트 및 배포

이 구조 수정으로 더욱 유연하고 관리하기 쉬운 시스템이 될 것입니다! 🚀