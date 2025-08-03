import 'package:dotenv/dotenv.dart';

class Config {
  static late DotEnv _dotEnv;
  
  /// 환경변수를 로드합니다
  static Future<void> load() async {
    _dotEnv = DotEnv();
    await _dotEnv.load(['.env']);
  }
  
  /// Open DART API 키를 가져옵니다
  static String get dartApiKey {
    final apiKey = _dotEnv['DART_API_KEY'];
    if (apiKey == null || apiKey.isEmpty) {
      throw Exception('DART_API_KEY가 .env 파일에 설정되지 않았습니다');
    }
    return apiKey;
  }
  
  /// Open DART Base URL을 가져옵니다
  static String get dartBaseUrl {
    return _dotEnv['DART_BASE_URL'] ?? 'https://opendart.fss.or.kr/api';
  }
} 