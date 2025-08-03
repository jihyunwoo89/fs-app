import '../lib/config.dart';
import '../lib/dart_service.dart';

void main() async {
  print('Open DART API 테스트 시작...');
  
  try {
    // 환경변수 로드
    await Config.load();
    print('✅ 환경변수를 성공적으로 로드했습니다.');
    
    // 삼성전자 기업코드로 테스트 (00126380)
    const samsungCorpCode = '00126380';
    
    print('\n🔍 삼성전자 기업개황 정보 조회 중...');
    final companyInfo = await DartService.getCompanyInfo(
      corpCode: samsungCorpCode,
    );
    
    if (companyInfo != null) {
      print('✅ DART API 응답 성공:');
      print('회사명: ${companyInfo['corp_name']}');
      print('CEO: ${companyInfo['ceo_nm']}');
      print('법인구분: ${companyInfo['corp_cls']}');
      print('상장코드: ${companyInfo['stock_code']}');
    } else {
      print('❌ DART API 호출에 실패했습니다.');
    }
    
    print('\n🔍 공시검색 목록 조회 중...');
    final disclosureList = await DartService.getDisclosureList(
      corpCode: samsungCorpCode,
      pageCount: '5', // 최근 5개만 조회
    );
    
    if (disclosureList != null && disclosureList['list'] != null) {
      print('✅ 최근 공시 목록:');
      final list = disclosureList['list'] as List;
      for (int i = 0; i < list.length && i < 3; i++) {
        final item = list[i];
        print('${i + 1}. ${item['report_nm']} (${item['rcept_dt']})');
      }
    } else {
      print('❌ 공시 목록 조회에 실패했습니다.');
    }
    
    print('\n📦 전체 기업코드 목록 다운로드 중...');
    final downloadSuccess = await DartService.downloadCorpCodeList(
      fileName: 'corp_code_list.zip'
    );
    
    if (downloadSuccess) {
      print('✅ 전체 기업코드 ZIP 파일이 성공적으로 다운로드되었습니다!');
      print('💡 ZIP 파일을 압축 해제하면 XML 형태의 전체 기업코드 목록을 확인할 수 있습니다.');
    } else {
      print('❌ 기업코드 ZIP 파일 다운로드에 실패했습니다.');
    }
    
  } catch (e) {
    print('❌ 오류 발생: $e');
    print('\n📝 .env 파일을 생성하고 DART_API_KEY를 설정해주세요.');
    print('예시:');
    print('DART_API_KEY=your_dart_api_key_here');
    print('\n🔗 API 키 발급: https://opendart.fss.or.kr/');
  }
} 