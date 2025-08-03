#!/usr/bin/env python3
"""
Open DART API를 통한 재무제표 데이터 조회 모듈
"""

import requests
import json
import os
from typing import Dict, List, Optional
from datetime import datetime

class FinancialDataFetcher:
    def __init__(self, api_key: str = None):
        """
        재무데이터 조회 클래스 초기화
        
        Args:
            api_key: Open DART API 키 (None이면 .env에서 읽기)
        """
        if api_key:
            self.api_key = api_key
        else:
            # .env 파일에서 API 키 읽기
            self.api_key = self._load_api_key()
        
        self.base_url = "https://opendart.fss.or.kr/api"
        
        # 보고서 코드 매핑
        self.report_codes = {
            '1분기': '11013',
            '반기': '11012', 
            '3분기': '11014',
            '사업보고서': '11011'
        }
    
    def _load_api_key(self) -> str:
        """환경 변수에서 API 키 로드"""
        try:
            with open('.env', 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip().startswith('DART_API_KEY='):
                        return line.strip().split('=', 1)[1]
            raise ValueError("DART_API_KEY not found in .env file")
        except FileNotFoundError:
            raise ValueError(".env file not found")
    
    def get_financial_statements(self, 
                               corp_code: str, 
                               bsns_year: str, 
                               reprt_code: str = '11011') -> Optional[Dict]:
        """
        단일회사 주요계정 재무제표 조회
        
        Args:
            corp_code: 기업코드 (8자리)
            bsns_year: 사업연도 (4자리, 예: '2023')
            reprt_code: 보고서코드 (기본값: '11011' - 사업보고서)
                       11013: 1분기보고서
                       11012: 반기보고서  
                       11014: 3분기보고서
                       11011: 사업보고서
        
        Returns:
            재무제표 데이터 딕셔너리 또는 None (오류시)
        """
        url = f"{self.base_url}/fnlttSinglAcnt.json"
        
        params = {
            'crtfc_key': self.api_key,
            'corp_code': corp_code,
            'bsns_year': bsns_year,
            'reprt_code': reprt_code
        }
        
        try:
            print(f"🔍 재무제표 조회 중... ({corp_code}, {bsns_year}년, 보고서: {reprt_code})")
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == '000':
                print(f"✅ 재무제표 조회 성공! ({len(data.get('list', []))}개 항목)")
                return data
            else:
                print(f"❌ API 오류: {data.get('message', '알 수 없는 오류')}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 네트워크 오류: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ JSON 파싱 오류: {e}")
            return None
    
    def parse_financial_data(self, raw_data: Dict) -> Dict:
        """
        원시 재무데이터를 구조화된 형태로 변환
        
        Args:
            raw_data: API에서 받은 원시 데이터
            
        Returns:
            구조화된 재무제표 데이터
        """
        if not raw_data or not raw_data.get('list'):
            return {}
        
        parsed = {
            'metadata': {
                'status': raw_data.get('status'),
                'message': raw_data.get('message'),
                'parsed_at': datetime.now().isoformat()
            },
            'balance_sheet': {  # 재무상태표 (BS)
                'assets': {},      # 자산
                'liabilities': {}, # 부채  
                'equity': {}       # 자본
            },
            'income_statement': {  # 손익계산서 (IS)
                'revenue': {},     # 매출
                'profit': {},      # 이익
                'expenses': {}     # 비용
            },
            'raw_data': []
        }
        
        for item in raw_data['list']:
            # 기본 정보 추출
            account_nm = item.get('account_nm', '')
            sj_div = item.get('sj_div', '')  # BS: 재무상태표, IS: 손익계산서
            thstrm_amount = self._parse_amount(item.get('thstrm_amount', '0'))
            frmtrm_amount = self._parse_amount(item.get('frmtrm_amount', '0'))
            
            # 항목 정보
            financial_item = {
                'account_name': account_nm,
                'current_year': {
                    'amount': thstrm_amount,
                    'period': item.get('thstrm_nm', ''),
                    'date': item.get('thstrm_dt', '')
                },
                'previous_year': {
                    'amount': frmtrm_amount, 
                    'period': item.get('frmtrm_nm', ''),
                    'date': item.get('frmtrm_dt', '')
                },
                'currency': item.get('currency', 'KRW'),
                'fs_div': item.get('fs_div', ''),
                'fs_nm': item.get('fs_nm', ''),
                'sj_div': sj_div,
                'sj_nm': item.get('sj_nm', '')
            }
            
            parsed['raw_data'].append(financial_item)
            
            # 재무상태표 항목 분류
            if sj_div == 'BS':
                if '자산' in account_nm:
                    parsed['balance_sheet']['assets'][account_nm] = financial_item
                elif '부채' in account_nm or '차입' in account_nm:
                    parsed['balance_sheet']['liabilities'][account_nm] = financial_item
                elif '자본' in account_nm or '이익잉여금' in account_nm:
                    parsed['balance_sheet']['equity'][account_nm] = financial_item
            
            # 손익계산서 항목 분류  
            elif sj_div == 'IS':
                if '매출' in account_nm:
                    parsed['income_statement']['revenue'][account_nm] = financial_item
                elif '이익' in account_nm or '손익' in account_nm:
                    parsed['income_statement']['profit'][account_nm] = financial_item
                elif '비용' in account_nm or '원가' in account_nm:
                    parsed['income_statement']['expenses'][account_nm] = financial_item
        
        return parsed
    
    def _parse_amount(self, amount_str: str) -> int:
        """금액 문자열을 정수로 변환"""
        try:
            # 콤마 제거하고 정수로 변환
            return int(amount_str.replace(',', ''))
        except (ValueError, AttributeError):
            return 0
    
    def get_multi_year_data(self, corp_code: str, start_year: int, end_year: int) -> Dict:
        """
        여러 연도의 재무데이터를 한번에 조회
        
        Args:
            corp_code: 기업코드
            start_year: 시작연도
            end_year: 종료연도
            
        Returns:
            연도별 재무데이터 딕셔너리
        """
        multi_year_data = {}
        
        for year in range(start_year, end_year + 1):
            year_str = str(year)
            print(f"\n📅 {year}년 데이터 조회 중...")
            
            raw_data = self.get_financial_statements(corp_code, year_str)
            if raw_data:
                parsed_data = self.parse_financial_data(raw_data)
                multi_year_data[year] = parsed_data
            else:
                print(f"⚠️ {year}년 데이터 조회 실패")
        
        return multi_year_data

def test_financial_data():
    """재무데이터 조회 테스트"""
    print("💰 재무제표 데이터 조회 테스트")
    print("=" * 50)
    
    fetcher = FinancialDataFetcher()
    
    # 삼성전자 테스트 (기업코드: 00126380)
    corp_code = "00126380"
    year = "2023"
    
    print(f"🏢 테스트 대상: 삼성전자 ({corp_code})")
    print(f"📅 조회 연도: {year}년")
    
    # 재무제표 조회
    raw_data = fetcher.get_financial_statements(corp_code, year)
    
    if raw_data:
        print("\n📊 원시 데이터 미리보기:")
        items = raw_data.get('list', [])[:3]  # 처음 3개만
        for item in items:
            print(f"  - {item.get('account_nm')}: {item.get('thstrm_amount')} {item.get('currency')}")
        
        # 데이터 파싱
        parsed = fetcher.parse_financial_data(raw_data)
        
        print(f"\n📈 파싱된 데이터 요약:")
        print(f"  - 재무상태표 자산 항목: {len(parsed['balance_sheet']['assets'])}개")
        print(f"  - 재무상태표 부채 항목: {len(parsed['balance_sheet']['liabilities'])}개") 
        print(f"  - 재무상태표 자본 항목: {len(parsed['balance_sheet']['equity'])}개")
        print(f"  - 손익계산서 매출 항목: {len(parsed['income_statement']['revenue'])}개")
        print(f"  - 손익계산서 이익 항목: {len(parsed['income_statement']['profit'])}개")
        
        # 주요 항목 출력
        print(f"\n💡 주요 재무 지표:")
        for item in parsed['raw_data'][:5]:
            current = item['current_year']['amount']
            previous = item['previous_year']['amount']
            growth = ((current - previous) / previous * 100) if previous > 0 else 0
            
            print(f"  - {item['account_name']}: {current:,} 원 (전년대비 {growth:+.1f}%)")

if __name__ == "__main__":
    test_financial_data() 