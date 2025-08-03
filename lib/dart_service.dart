import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'config.dart';

class DartService {
  /// 기업개황 정보를 조회합니다
  static Future<Map<String, dynamic>?> getCompanyInfo({
    required String corpCode,
  }) async {
    try {
      final url = Uri.parse('${Config.dartBaseUrl}/company.json').replace(
        queryParameters: {
          'crtfc_key': Config.dartApiKey,
          'corp_code': corpCode,
        },
      );
      
      final response = await http.get(url);
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['status'] == '000') {
          return data;
        } else {
          print('DART API 오류: ${data['message']}');
          return null;
        }
      } else {
        print('DART API 호출 오류: ${response.statusCode}');
        print('응답: ${response.body}');
        return null;
      }
    } catch (e) {
      print('DART API 호출 중 오류 발생: $e');
      return null;
    }
  }
  
  /// 공시검색 목록을 조회합니다
  static Future<Map<String, dynamic>?> getDisclosureList({
    required String corpCode,
    String? beginDe,
    String? endDe,
    String? lastReprtAt,
    String? pblntfTy,
    String? pblntfDetailTy,
    String? corpCls,
    String? sortSt,
    String? sortMth,
    String? pageNo,
    String? pageCount,
  }) async {
    try {
      final queryParams = <String, String>{
        'crtfc_key': Config.dartApiKey,
        'corp_code': corpCode,
      };
      
      if (beginDe != null) queryParams['bgn_de'] = beginDe;
      if (endDe != null) queryParams['end_de'] = endDe;
      if (lastReprtAt != null) queryParams['last_reprt_at'] = lastReprtAt;
      if (pblntfTy != null) queryParams['pblntf_ty'] = pblntfTy;
      if (pblntfDetailTy != null) queryParams['pblntf_detail_ty'] = pblntfDetailTy;
      if (corpCls != null) queryParams['corp_cls'] = corpCls;
      if (sortSt != null) queryParams['sort_st'] = sortSt;
      if (sortMth != null) queryParams['sort_mth'] = sortMth;
      if (pageNo != null) queryParams['page_no'] = pageNo;
      if (pageCount != null) queryParams['page_count'] = pageCount;
      
      final url = Uri.parse('${Config.dartBaseUrl}/list.json').replace(
        queryParameters: queryParams,
      );
      
      final response = await http.get(url);
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['status'] == '000') {
          return data;
        } else {
          print('DART API 오류: ${data['message']}');
          return null;
        }
      } else {
        print('DART API 호출 오류: ${response.statusCode}');
        print('응답: ${response.body}');
        return null;
      }
    } catch (e) {
      print('DART API 호출 중 오류 발생: $e');
      return null;
    }
  }
  
  /// 기업코드 ZIP 파일을 다운로드합니다
  static Future<bool> downloadCorpCodeList({String fileName = 'corp_code_list.zip'}) async {
    try {
      final url = Uri.parse('${Config.dartBaseUrl}/corpCode.xml').replace(
        queryParameters: {
          'crtfc_key': Config.dartApiKey,
        },
      );
      
      print('🔄 기업코드 목록 다운로드 중...');
      print('URL: $url');
      
      final response = await http.get(url);
      
      if (response.statusCode == 200) {
        // ZIP 파일로 응답이 오므로 바이너리 데이터를 파일로 저장
        final file = File(fileName);
        await file.writeAsBytes(response.bodyBytes);
        
        print('✅ 기업코드 ZIP 파일 다운로드 완료: $fileName');
        print('📁 파일 크기: ${(response.bodyBytes.length / 1024).toStringAsFixed(1)} KB');
        
        return true;
      } else {
        print('❌ DART API 호출 오류: ${response.statusCode}');
        if (response.body.isNotEmpty) {
          print('응답: ${response.body}');
        }
        return false;
      }
    } catch (e) {
      print('❌ 기업코드 다운로드 중 오류 발생: $e');
      return false;
    }
  }
} 