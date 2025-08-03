import 'lib/config.dart';
import 'lib/dart_service.dart';

void main() async {
  print('🏢 Open DART 기업코드 목록 다운로드');
  print('=' * 50);
  
  try {
    // 환경변수 로드
    await Config.load();
    print('✅ API 키 로드 완료');
    
    // 기업코드 ZIP 파일 다운로드
    print('\n📦 전체 기업코드 목록 다운로드 시작...');
    final success = await DartService.downloadCorpCodeList(
      fileName: 'corp_code_list.zip'
    );
    
    if (success) {
      print('\n🎉 다운로드 완료!');
      print('📁 파일명: corp_code_list.zip');
      print('💡 이 ZIP 파일을 압축 해제하면 CORPCODE.xml 파일이 나옵니다.');
      print('📊 XML 파일에는 모든 상장기업의 고유번호, 회사명, 종목코드 등이 포함되어 있습니다.');
    } else {
      print('\n❌ 다운로드 실패');
      print('🔧 API 키가 올바른지 확인해주세요.');
    }
    
  } catch (e) {
    print('\n❌ 오류 발생: $e');
    print('\n📝 해결 방법:');
    print('1. .env 파일에 DART_API_KEY를 올바르게 설정했는지 확인');
    print('2. Open DART 웹사이트에서 API 키가 승인되었는지 확인');
    print('3. 인터넷 연결 상태 확인');
  }
} 