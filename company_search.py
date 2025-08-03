#!/usr/bin/env python3
"""
회사명으로 기업코드를 검색하는 모듈
"""

import json
import re
from typing import List, Dict, Optional

class CompanySearcher:
    def __init__(self, json_file: str = "corp_codes.json"):
        """JSON 파일을 로드하여 검색 준비"""
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.companies = data['companies']
        self.total_count = data['metadata']['total_count']
        print(f"✅ {self.total_count:,}개 기업 데이터 로드 완료")
    
    def search_by_name(self, company_name: str, limit: int = 10) -> List[Dict]:
        """
        회사명으로 기업 검색
        
        Args:
            company_name: 검색할 회사명 (부분 검색 가능)
            limit: 최대 결과 수
            
        Returns:
            검색된 기업 정보 리스트
        """
        if not company_name or len(company_name.strip()) < 1:
            return []
        
        query = company_name.strip().lower()
        results = []
        
        for company in self.companies:
            corp_name = company['corp_name'].lower()
            corp_eng_name = company.get('corp_eng_name', '').lower()
            
            # 한글명 또는 영문명에서 검색
            if (query in corp_name or 
                query in corp_eng_name or
                corp_name.startswith(query)):
                
                results.append(company)
                
                if len(results) >= limit:
                    break
        
        return results
    
    def search_exact(self, company_name: str) -> Optional[Dict]:
        """정확한 회사명으로 검색"""
        query = company_name.strip()
        
        for company in self.companies:
            if company['corp_name'] == query:
                return company
        
        return None
    
    def get_by_corp_code(self, corp_code: str) -> Optional[Dict]:
        """기업코드로 회사 정보 조회"""
        for company in self.companies:
            if company['corp_code'] == corp_code:
                return company
        
        return None
    
    def search_listed_companies(self, company_name: str = "", limit: int = 20) -> List[Dict]:
        """상장기업만 검색"""
        results = []
        query = company_name.strip().lower() if company_name else ""
        
        for company in self.companies:
            # 상장기업 (종목코드가 있는 기업)만 필터링
            if company['stock_code'] is not None:
                if not query:  # 검색어가 없으면 모든 상장기업
                    results.append(company)
                else:  # 검색어가 있으면 이름으로 필터링
                    corp_name = company['corp_name'].lower()
                    if query in corp_name:
                        results.append(company)
                
                if len(results) >= limit:
                    break
        
        return results

def test_search():
    """검색 기능 테스트"""
    print("🔍 회사 검색 기능 테스트")
    print("=" * 50)
    
    searcher = CompanySearcher()
    
    # 테스트 케이스들
    test_cases = [
        "삼성전자",
        "삼성",
        "LG",
        "현대자동차",
        "NAVER",
        "SK하이닉스"
    ]
    
    for test_name in test_cases:
        print(f"\n🔎 '{test_name}' 검색 결과:")
        results = searcher.search_by_name(test_name, limit=5)
        
        if results:
            for i, company in enumerate(results, 1):
                stock_info = f" (종목코드: {company['stock_code']})" if company['stock_code'] else " (비상장)"
                print(f"  {i}. {company['corp_name']} | {company['corp_code']}{stock_info}")
        else:
            print("  검색 결과가 없습니다.")
    
    # 상장기업 검색 테스트
    print(f"\n📈 상장기업 '삼성' 검색:")
    listed_results = searcher.search_listed_companies("삼성", limit=5)
    for i, company in enumerate(listed_results, 1):
        print(f"  {i}. {company['corp_name']} | {company['corp_code']} | {company['stock_code']}")

if __name__ == "__main__":
    test_search() 