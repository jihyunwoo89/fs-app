#!/usr/bin/env python3
"""
Open DART 기업코드 XML을 JSON으로 변환하는 스크립트
"""

import xml.etree.ElementTree as ET
import json
from datetime import datetime

def xml_to_json(xml_file, json_file):
    """XML 파일을 JSON으로 변환"""
    print(f"🔄 {xml_file} 파일을 JSON으로 변환 중...")
    
    try:
        # XML 파일 파싱
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        companies = []
        
        # 모든 <list> 요소를 순회
        for company in root.findall('list'):
            corp_code = company.find('corp_code')
            corp_name = company.find('corp_name')
            corp_eng_name = company.find('corp_eng_name')
            stock_code = company.find('stock_code')
            modify_date = company.find('modify_date')
            
            # 데이터 정리
            company_data = {
                'corp_code': corp_code.text.strip() if corp_code is not None else '',
                'corp_name': corp_name.text.strip() if corp_name is not None else '',
                'corp_eng_name': corp_eng_name.text.strip() if corp_eng_name is not None else '',
                'stock_code': stock_code.text.strip() if stock_code is not None and stock_code.text.strip() else None,
                'modify_date': modify_date.text.strip() if modify_date is not None else ''
            }
            
            companies.append(company_data)
        
        # JSON 파일로 저장
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': {
                    'total_count': len(companies),
                    'converted_at': datetime.now().isoformat(),
                    'source': xml_file
                },
                'companies': companies
            }, f, ensure_ascii=False, indent=2)
        
        # 상장기업 수 계산
        listed_companies = [c for c in companies if c['stock_code'] is not None]
        
        print(f"✅ 변환 완료!")
        print(f"📁 JSON 파일: {json_file}")
        print(f"📊 전체 기업 수: {len(companies):,}개")
        print(f"📈 상장기업 수: {len(listed_companies):,}개")
        print(f"📦 파일 크기: {get_file_size(json_file)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 변환 중 오류 발생: {e}")
        return False

def get_file_size(file_path):
    """파일 크기를 읽기 쉬운 형태로 반환"""
    import os
    size = os.path.getsize(file_path)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"

def create_sample_json(companies, sample_file, sample_count=100):
    """샘플 JSON 파일 생성"""
    print(f"\n🎯 상위 {sample_count}개 기업으로 샘플 파일 생성 중...")
    
    sample_data = {
        'metadata': {
            'sample_count': min(sample_count, len(companies)),
            'total_count': len(companies),
            'created_at': datetime.now().isoformat(),
            'description': f'Open DART 기업코드 상위 {sample_count}개 샘플'
        },
        'companies': companies[:sample_count]
    }
    
    with open(sample_file, 'w', encoding='utf-8') as f:
        json.dump(sample_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 샘플 파일 생성 완료: {sample_file}")

if __name__ == "__main__":
    xml_file = "CORPCODE.xml"
    json_file = "corp_codes.json"
    sample_file = "corp_codes_sample.json"
    
    print("🏢 Open DART 기업코드 XML → JSON 변환기")
    print("=" * 50)
    
    # XML을 JSON으로 변환
    if xml_to_json(xml_file, json_file):
        # JSON 파일 로드하여 샘플 생성
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                create_sample_json(data['companies'], sample_file)
        except Exception as e:
            print(f"⚠️ 샘플 파일 생성 중 오류: {e}")
    
    print("\n🎉 모든 작업이 완료되었습니다!") 