#!/usr/bin/env python3
"""
AI 재무분석 모듈 - Gemini API 사용
"""

import os
import json
import requests
from typing import Dict, List, Optional
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

class FinancialAnalysisAI:
    def __init__(self):
        """AI 분석기 초기화"""
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key or self.api_key == 'your_gemini_api_key_here':
            print("⚠️ Gemini API 키가 설정되지 않았습니다.")
            self.enabled = False
        else:
            self.enabled = True
            print("✅ Gemini AI 분석기 활성화")
    
    def analyze_financial_statement(self, company_name: str, financial_data: Dict, ratios_data: Dict = None) -> Optional[str]:
        """
        재무제표 데이터를 AI로 분석하여 쉬운 설명 생성
        
        Args:
            company_name: 회사명
            financial_data: 재무제표 데이터
            ratios_data: 재무비율 데이터 (선택사항)
            
        Returns:
            AI가 생성한 재무분석 설명 (한국어)
        """
        if not self.enabled:
            return None
        
        try:
            # 재무데이터 요약 생성
            financial_summary = self._create_financial_summary(company_name, financial_data, ratios_data)
            
            # Gemini API 호출
            prompt = self._create_analysis_prompt(financial_summary)
            analysis = self._call_gemini_api(prompt)
            
            return analysis
            
        except Exception as e:
            print(f"❌ AI 분석 오류: {e}")
            return None
    
    def _create_financial_summary(self, company_name: str, financial_data: Dict, ratios_data: Dict = None) -> str:
        """재무데이터를 요약하여 AI 분석용 텍스트 생성"""
        try:
            raw_data = financial_data.get('raw_data', [])
            
            # 주요 재무 항목 추출
            summary_parts = [f"**{company_name} 재무제표 분석**\n"]
            
            # 손익계산서 주요 항목
            income_items = []
            for item in raw_data:
                if item.get('sj_div') == 'IS':
                    account_name = item.get('account_name', '')
                    current_amount = item.get('current_year', {}).get('amount', 0)
                    previous_amount = item.get('previous_year', {}).get('amount', 0)
                    
                    if any(keyword in account_name for keyword in ['매출액', '영업이익', '당기순이익']):
                        if current_amount > 0 or previous_amount > 0:
                            growth_rate = 0
                            if previous_amount > 0:
                                growth_rate = ((current_amount - previous_amount) / previous_amount) * 100
                            
                            income_items.append(f"- {account_name}: {self._format_amount(current_amount)} (전년대비 {growth_rate:+.1f}%)")
            
            if income_items:
                summary_parts.append("## 손익계산서 주요 항목:")
                summary_parts.extend(income_items)
                summary_parts.append("")
            
            # 재무상태표 주요 항목
            balance_items = []
            for item in raw_data:
                if item.get('sj_div') == 'BS':
                    account_name = item.get('account_name', '')
                    current_amount = item.get('current_year', {}).get('amount', 0)
                    previous_amount = item.get('previous_year', {}).get('amount', 0)
                    
                    if any(keyword in account_name for keyword in ['자산총계', '부채총계', '자본총계']):
                        if current_amount > 0 or previous_amount > 0:
                            growth_rate = 0
                            if previous_amount > 0:
                                growth_rate = ((current_amount - previous_amount) / previous_amount) * 100
                            
                            balance_items.append(f"- {account_name}: {self._format_amount(current_amount)} (전년대비 {growth_rate:+.1f}%)")
            
            if balance_items:
                summary_parts.append("## 재무상태표 주요 항목:")
                summary_parts.extend(balance_items)
                summary_parts.append("")
            
            # 재무비율 추가 (있는 경우)
            if ratios_data:
                ratio_items = []
                profitability = ratios_data.get('profitability', {})
                stability = ratios_data.get('stability', {})
                
                for ratio_key, ratio_info in profitability.items():
                    if isinstance(ratio_info, dict) and 'name' in ratio_info and 'value' in ratio_info:
                        ratio_items.append(f"- {ratio_info['name']}: {ratio_info['value']:.2f}{ratio_info.get('unit', '')}")
                
                for ratio_key, ratio_info in stability.items():
                    if isinstance(ratio_info, dict) and 'name' in ratio_info and 'value' in ratio_info:
                        ratio_items.append(f"- {ratio_info['name']}: {ratio_info['value']:.2f}{ratio_info.get('unit', '')}")
                
                if ratio_items:
                    summary_parts.append("## 주요 재무비율:")
                    summary_parts.extend(ratio_items[:6])  # 최대 6개만
                    summary_parts.append("")
            
            return "\n".join(summary_parts)
            
        except Exception as e:
            print(f"재무데이터 요약 생성 오류: {e}")
            return f"{company_name}의 재무데이터 요약을 생성할 수 없습니다."
    
    def _format_amount(self, amount: float) -> str:
        """금액을 읽기 쉬운 형태로 포맷"""
        if amount >= 1_000_000_000_000:
            return f"{amount/1_000_000_000_000:.1f}조원"
        elif amount >= 1_000_000_000:
            return f"{amount/1_000_000_000:.0f}억원"
        elif amount >= 1_000_000:
            return f"{amount/1_000_000:.0f}백만원"
        else:
            return f"{amount:,.0f}원"
    
    def _create_analysis_prompt(self, financial_summary: str) -> str:
        """AI 분석용 프롬프트 생성"""
        prompt = f"""
다음 재무제표 데이터를 바탕으로 일반인도 쉽게 이해할 수 있도록 분석해주세요.

{financial_summary}

다음 관점에서 친근하고 이해하기 쉽게 설명해주세요:

1. **📊 전반적인 재무 상황**: 이 회사의 재무 상태가 어떤지 간단히 요약
2. **💰 수익성 분석**: 매출과 이익 상황이 어떤지, 좋은지 나쁜지
3. **🏦 재무 안정성**: 회사가 안정적인지, 부채는 많은지
4. **📈 성장성**: 전년 대비 성장하고 있는지
5. **⚠️ 주의사항**: 투자자가 알아야 할 위험요소나 특이사항
6. **🎯 종합 의견**: 이 회사에 대한 전반적인 평가

답변은 반드시 한국어로 하고, 전문용어는 쉽게 풀어서 설명해주세요.
각 섹션은 2-3문장으로 간결하게 작성해주세요.
"""
        return prompt
    
    def _call_gemini_api(self, prompt: str) -> Optional[str]:
        """Gemini API 호출"""
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={self.api_key}"
            
            headers = {
                'Content-Type': 'application/json',
            }
            
            data = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.3,
                    "topK": 40,
                    "topP": 0.8,
                    "maxOutputTokens": 2048,
                }
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                if 'candidates' in result and len(result['candidates']) > 0:
                    content = result['candidates'][0].get('content', {})
                    parts = content.get('parts', [])
                    
                    if parts and len(parts) > 0:
                        return parts[0].get('text', '').strip()
                
                print(f"예상치 못한 API 응답 구조: {result}")
                return None
            
            elif response.status_code == 429:
                # 할당량 초과 오류 처리
                print(f"❌ Gemini API 오류: {response.status_code}")
                print(f"응답: {response.text}")
                return "quota_exceeded"  # 특별한 반환값으로 할당량 초과를 알림
            else:
                print(f"❌ Gemini API 오류: {response.status_code}")
                print(f"응답: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            print("❌ Gemini API 타임아웃")
            return None
        except Exception as e:
            print(f"❌ Gemini API 호출 오류: {e}")
            return None
    
    def analyze_comparison_data(self, company_name: str, comparison_data: List[Dict]) -> Optional[str]:
        """당기vs전기 비교 데이터를 AI로 분석"""
        if not self.enabled:
            return None
        
        try:
            # 비교 데이터 요약
            summary_parts = [f"**{company_name} 당기 vs 전기 비교 분석**\n"]
            
            for item in comparison_data:
                item_name = item.get('item', '')
                current_year = item.get('current_year', '')
                previous_year = item.get('previous_year', '')
                growth_rate = item.get('growth_rate', 0)
                current_amount = item.get('current_amount', 0)
                
                direction = "증가" if growth_rate >= 0 else "감소"
                summary_parts.append(f"- {item_name}: {self._format_amount(current_amount)} ({previous_year}년 대비 {abs(growth_rate):.1f}% {direction})")
            
            summary = "\n".join(summary_parts)
            
            prompt = f"""
다음 재무데이터 변화를 분석해서 쉽게 설명해주세요:

{summary}

다음 관점에서 분석해주세요:

1. **📊 주요 변화**: 가장 눈에 띄는 변화 사항
2. **📈 긍정적 요소**: 좋아진 부분들
3. **📉 부정적 요소**: 악화된 부분들  
4. **🔍 원인 분석**: 이런 변화가 일어난 가능한 이유
5. **🎯 종합 평가**: 전반적으로 회사가 나아졌는지 악화됐는지

한국어로 쉽게 설명해주세요. 각 섹션은 2-3문장으로 간결하게 작성해주세요.
"""
            
            return self._call_gemini_api(prompt)
            
        except Exception as e:
            print(f"❌ AI 비교 분석 오류: {e}")
            return None

# 테스트 함수
def test_ai_analysis():
    """AI 분석 테스트"""
    print("🤖 AI 재무분석 테스트")
    print("=" * 50)
    
    ai = FinancialAnalysisAI()
    
    if not ai.enabled:
        print("⚠️ AI 분석 비활성화 - API 키를 확인하세요")
        return
    
    # 가상의 재무데이터로 테스트
    sample_data = {
        'raw_data': [
            {
                'account_name': '매출액',
                'current_year': {'amount': 100000000000000},
                'previous_year': {'amount': 95000000000000},
                'sj_div': 'IS'
            },
            {
                'account_name': '당기순이익',
                'current_year': {'amount': 10000000000000},
                'previous_year': {'amount': 8000000000000},
                'sj_div': 'IS'
            }
        ]
    }
    
    analysis = ai.analyze_financial_statement("테스트회사", sample_data)
    
    if analysis:
        print("✅ AI 분석 결과:")
        print(analysis)
    else:
        print("❌ AI 분석 실패")

if __name__ == "__main__":
    test_ai_analysis() 