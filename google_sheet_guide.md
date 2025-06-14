# 🔧 구글시트 연동 설정 가이드

## 📋 목차
1. [Google Cloud Console 설정](#1-google-cloud-console-설정)
2. [Service Account 생성](#2-service-account-생성)
3. [구글시트 준비](#3-구글시트-준비)
4. [환경변수 설정](#4-환경변수-설정)
5. [연결 테스트](#5-연결-테스트)

---

## 1. Google Cloud Console 설정

### 1.1 프로젝트 생성/선택
1. https://console.cloud.google.com/ 접속
2. 상단에서 프로젝트 선택 또는 **새 프로젝트** 생성
3. 프로젝트 이름: `google-news-ai` (예시)

### 1.2 Google Sheets API 활성화
1. **APIs & Services** > **Library** 이동
2. "Google Sheets API" 검색
3. **ENABLE** 클릭하여 API 활성화
4. "Google Drive API"도 함께 활성화 (권장)

---

## 2. Service Account 생성

### 2.1 Service Account 만들기
1. **APIs & Services** > **Credentials** 이동
2. **+ CREATE CREDENTIALS** > **Service account** 선택
3. Service account 정보 입력:
   ```
   Name: google-news-ai-service
   Description: Google News AI 시스템용 서비스 계정
   ```
4. **CREATE AND CONTINUE** 클릭

### 2.2 권한 설정 (선택사항)
- 특별한 권한이 필요하지 않으므로 **CONTINUE** 클릭
- **DONE** 클릭

### 2.3 JSON 키 생성
1. 생성된 Service Account 클릭
2. **Keys** 탭 > **ADD KEY** > **Create new key**
3. **JSON** 선택 후 **CREATE**
4. JSON 파일이 자동으로 다운로드됨
5. 파일을 프로젝트 폴더에 저장 (예: `service_account.json`)

### 2.4 Service Account 이메일 복사
- Service Account 이메일 주소를 복사해둡니다
- 형식: `service-account-name@project-id.iam.gserviceaccount.com`

---

## 3. 구글시트 준비

### 3.1 새 스프레드시트 생성
1. https://sheets.google.com/ 접속
2. **새 스프레드시트** 생성
3. 제목: "Google News AI Keywords" (예시)

### 3.2 키워드 테이블 구성
첫 번째 워크시트 이름을 `keywords`로 변경하고 다음과 같이 구성:

| A (keyword) | B (category) | C (priority) | D (active) |
|-------------|--------------|--------------|------------|
| 인공지능    | AI           | 1            | TRUE       |
| ChatGPT     | AI           | 1            | TRUE       |
| 생성형AI    | AI           | 1            | TRUE       |
| 머신러닝    | AI           | 1            | TRUE       |
| 딥러닝      | AI           | 2            | TRUE       |
| LLM         | AI           | 2            | TRUE       |
| 네이버      | TECH         | 2            | TRUE       |
| 카카오      | TECH         | 2            | TRUE       |
| 삼성        | TECH         | 2            | TRUE       |
| 자율주행    | TECH         | 2            | TRUE       |

### 3.3 컬럼 설명
- **keyword**: 검색할 키워드
- **category**: 카테고리 (AI, TECH, CORP 등)
- **priority**: 우선순위 (1=최고, 3=최저)
- **active**: 활성화 여부 (TRUE/FALSE)

### 3.4 스프레드시트 공유
1. **공유** 버튼 클릭
2. Service Account 이메일 주소 입력
3. 권한을 **편집자**로 설정
4. **완료** 클릭

### 3.5 스프레드시트 ID 복사
URL에서 스프레드시트 ID 추출:
```
https://docs.google.com/spreadsheets/d/[SPREADSHEET_ID]/edit
```

---

## 4. 환경변수 설정

### 4.1 .env 파일 수정
```bash
# 구글시트 연동 설정
GOOGLE_SHEETS_CREDENTIALS_FILE=./service_account.json
GOOGLE_SHEETS_SPREADSHEET_ID=1ABC123...XYZ789
GOOGLE_SHEETS_WORKSHEET_NAME=keywords
```

### 4.2 JSON 키 파일 경로 확인
- JSON 파일이 프로젝트 루트에 있는지 확인
- 파일 경로가 정확한지 확인 (절대경로 사용 권장)

---

## 5. 연결 테스트

### 5.1 의존성 설치
```bash
pip install gspread google-auth google-auth-oauthlib google-auth-httplib2
```

### 5.2 연결 테스트 실행
```bash
# 구글시트 연결 테스트
python3 google_sheets_manager.py test

# 또는 설정 파일에서 테스트
python3 config.py test-sheets
```

### 5.3 키워드 로딩 테스트
```bash
# 키워드 관리자 테스트
python3 keyword_manager.py test

# 현재 키워드 목록 확인
python3 keyword_manager.py keywords
```

### 5.4 전체 시스템 테스트
```bash
# 전체 시스템 테스트
python3 simple_scheduler.py test
```

---

## 🔧 문제 해결

### 자주 발생하는 오류들

#### 1. "File not found" 오류
```bash
❌ 인증 파일을 찾을 수 없습니다: ./service_account.json
```
**해결방법:**
- JSON 파일 경로 확인
- 절대경로 사용: `/full/path/to/service_account.json`

#### 2. "Permission denied" 오류
```bash
❌ 스프레드시트에 접근할 수 없습니다
```
**해결방법:**
- 스프레드시트가 Service Account와 공유되었는지 확인
- Service Account 이메일 주소가 정확한지 확인
- 편집 권한이 있는지 확인

#### 3. "API not enabled" 오류
```bash
❌ Google Sheets API가 활성화되지 않았습니다
```
**해결방법:**
- Google Cloud Console에서 Google Sheets API 활성화
- Google Drive API도 함께 활성화

#### 4. "Worksheet not found" 오류
```bash
❌ 워크시트 'keywords'를 찾을 수 없습니다
```
**해결방법:**
- 워크시트 이름이 정확한지 확인 (대소문자 구분)
- 환경변수 `GOOGLE_SHEETS_WORKSHEET_NAME` 확인

---

## 📊 키워드 관리 팁

### 1. 효과적인 키워드 구성
- **우선순위 1**: 핵심 AI 키워드 (인공지능, ChatGPT, AI)
- **우선순위 2**: 기술 키워드 (네이버, 카카오, 자율주행)
- **우선순위 3**: 보조 키워드 (블록체인, 메타버스)

### 2. 카테고리 분류
- **AI**: 인공지능 관련
- **TECH**: 일반 기술
- **CORP**: 기업 관련
- **TREND**: 트렌드 키워드

### 3. 키워드 업데이트
- 구글시트에서 직접 수정
- 시스템 재시작 없이 실시간 반영
- `active` 컬럼으로 키워드 활성화/비활성화

---

## 🎯 완료 체크리스트

- [ ] Google Cloud Console 프로젝트 생성
- [ ] Google Sheets API 활성화
- [ ] Service Account 생성 및 JSON 키 다운로드
- [ ] 구글시트 생성 및 키워드 테이블 구성
- [ ] Service Account와 스프레드시트 공유
- [ ] 환경변수 설정 완료
- [ ] 연결 테스트 성공
- [ ] 키워드 로딩 테스트 성공
- [ ] 전체 시스템 테스트 성공

---

## 📞 추가 지원

구글시트 연동에 문제가 있으시면:
1. 연결 테스트 결과 로그 확인
2. 환경변수 설정 재확인
3. Service Account 권한 확인
4. 개발자에게 문의: davidlikescat@icloud.com

🎉 **설정 완료 후 시스템이 구글시트의 키워드를 자동으로 사용합니다!**