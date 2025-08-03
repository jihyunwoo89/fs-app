# Open DART API Dart 프로젝트

이 프로젝트는 Dart에서 한국 금융감독원의 Open DART API를 사용하며, API 키를 `.env` 파일로 안전하게 관리합니다.

## 🚀 시작하기

### 1. 의존성 설치

```bash
dart pub get
```

### 2. .env 파일 생성

프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 다음과 같이 설정하세요:

```env
# Open DART API 설정
DART_API_KEY=your_dart_api_key_here

# 기타 설정 (선택사항)
DART_BASE_URL=https://opendart.fss.or.kr/api
```

⚠️ **중요**: `.env` 파일에는 실제 API 키를 입력해야 합니다. 이 파일은 Git에 커밋되지 않도록 `.gitignore`에 추가되어 있습니다.

### 3. Open DART API 키 발급

1. [Open DART 웹사이트](https://opendart.fss.or.kr/)에 접속
2. 회원가입 또는 로그인
3. 'API 신청' 메뉴에서 API 키 발급 신청
4. 승인 후 발급된 키를 `.env` 파일의 `DART_API_KEY`에 설정

### 4. 프로그램 실행

```bash
dart run bin/main.dart
```

## 📁 프로젝트 구조

```
fs-project_1/
├── bin/
│   └── main.dart           # 메인 실행 파일
├── lib/
│   ├── config.dart         # 환경변수 설정 관리
│   └── dart_service.dart   # Open DART API 호출 서비스
├── .env                    # 환경변수 파일 (직접 생성 필요)
├── .gitignore             # Git 제외 파일 목록
├── pubspec.yaml           # Dart 프로젝트 설정
└── README.md              # 이 파일
```

## 🔧 사용법

### 기본 기업정보 조회 API 호출

```dart
import 'lib/config.dart';
import 'lib/dart_service.dart';

void main() async {
  // 환경변수 로드
  await Config.load();
  
  // 기업개황 정보 조회 (삼성전자 예시)
  final companyInfo = await DartService.getCompanyInfo(
    corpCode: '00126380', // 삼성전자 기업코드
  );
  
  if (companyInfo != null) {
    print('회사명: ${companyInfo['corp_name']}');
    print('CEO: ${companyInfo['ceo_nm']}');
  }
  
  // 공시검색 목록 조회
  final disclosureList = await DartService.getDisclosureList(
    corpCode: '00126380',
    pageCount: '10',
  );
  
  print(disclosureList);
  
  // 전체 기업코드 ZIP 파일 다운로드
  final downloadSuccess = await DartService.downloadCorpCodeList(
    fileName: 'corp_code_list.zip'
  );
  
  if (downloadSuccess) {
    print('기업코드 ZIP 파일 다운로드 완료!');
  }
}
```

### 주요 API 메서드

- `getCompanyInfo()`: 기업개황 정보 조회
- `getDisclosureList()`: 공시검색 목록 조회  
- `downloadCorpCodeList()`: 전체 기업코드 ZIP 파일 다운로드

### 주요 매개변수

- `corpCode`: 기업코드 (필수) - 8자리 고유코드
- `beginDe`, `endDe`: 검색 시작일, 종료일 (YYYYMMDD 형식)
- `pageNo`, `pageCount`: 페이지 번호, 페이지당 건수

## 🔒 보안 주의사항

1. `.env` 파일은 절대 Git 저장소에 커밋하지 마세요
2. API 키를 코드에 직접 하드코딩하지 마세요
3. API 키를 공유하거나 공개하지 마세요
4. 프로덕션 환경에서는 적절한 환경변수 관리 도구를 사용하세요

## 📚 추가 자료

- [Open DART API 문서](https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS001&apiId=2019001)
- [Open DART 개발가이드](https://opendart.fss.or.kr/guide/main.do)
- [Dart dotenv 패키지](https://pub.dev/packages/dotenv)
- [Dart HTTP 패키지](https://pub.dev/packages/http)

## 💡 유용한 기업코드

- 삼성전자: 00126380
- SK하이닉스: 00164779  
- LG전자: 00401731
- 현대자동차: 00164742
- NAVER: 00781290

💡 **팁**: 기업코드는 `getCorpCodeList()` API를 통해 전체 목록을 다운로드할 수 있습니다. 