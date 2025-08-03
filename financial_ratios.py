#!/usr/bin/env python3
"""
재무비율 계산 및 분석 모듈
"""

from typing import Dict, List, Optional
import pandas as pd

class FinancialRatioCalculator:
    def __init__(self):
        """재무비율 계산기 초기화"""
        pass
    
    def calculate_ratios(self, financial_data: Dict) -> Dict:
        """
        재무데이터로부터 주요 재무비율 계산
        
        Args:
            financial_data: 파싱된 재무제표 데이터
            
        Returns:
            계산된 재무비율 딕셔너리
        """
        if not financial_data or not financial_data.get('raw_data'):
            return {}
        
        # 주요 계정 추출
        accounts = self._extract_key_accounts(financial_data['raw_data'])
        
        # 재무비율 계산
        ratios = {
            'profitability': self._calculate_profitability_ratios(accounts),
            'stability': self._calculate_stability_ratios(accounts),
            'growth': self._calculate_growth_ratios(accounts),
            'activity': self._calculate_activity_ratios(accounts)
        }
        
        return ratios
    
    def _extract_key_accounts(self, raw_data: List[Dict]) -> Dict:
        """원시 데이터에서 주요 계정 추출"""
        accounts = {}
        
        for item in raw_data:
            account_name = item.get('account_name', '')
            current_amount = item.get('current_year', {}).get('amount', 0)
            previous_amount = item.get('previous_year', {}).get('amount', 0)
            sj_div = item.get('sj_div', '')
            
            # 재무상태표 계정
            if sj_div == 'BS':
                if '자산총계' in account_name:
                    accounts['total_assets'] = {'current': current_amount, 'previous': previous_amount}
                elif '유동자산' in account_name:
                    accounts['current_assets'] = {'current': current_amount, 'previous': previous_amount}
                elif '부채총계' in account_name:
                    accounts['total_liabilities'] = {'current': current_amount, 'previous': previous_amount}
                elif '유동부채' in account_name:
                    accounts['current_liabilities'] = {'current': current_amount, 'previous': previous_amount}
                elif '자본총계' in account_name:
                    accounts['total_equity'] = {'current': current_amount, 'previous': previous_amount}
            
            # 손익계산서 계정
            elif sj_div == 'IS':
                if '매출액' in account_name and '매출원가' not in account_name:
                    accounts['revenue'] = {'current': current_amount, 'previous': previous_amount}
                elif '영업이익' in account_name:
                    accounts['operating_profit'] = {'current': current_amount, 'previous': previous_amount}
                elif '당기순이익' in account_name and '손실' not in account_name:
                    accounts['net_income'] = {'current': current_amount, 'previous': previous_amount}
        
        return accounts
    
    def _calculate_profitability_ratios(self, accounts: Dict) -> Dict:
        """수익성 비율 계산"""
        ratios = {}
        
        try:
            # ROE (자기자본이익률) = 당기순이익 / 자기자본 × 100
            if 'net_income' in accounts and 'total_equity' in accounts:
                net_income = accounts['net_income']['current']
                equity = accounts['total_equity']['current']
                if equity > 0:
                    ratios['roe'] = {
                        'value': (net_income / equity) * 100,
                        'name': 'ROE (자기자본이익률)',
                        'unit': '%'
                    }
            
            # ROA (총자산이익률) = 당기순이익 / 총자산 × 100
            if 'net_income' in accounts and 'total_assets' in accounts:
                net_income = accounts['net_income']['current']
                assets = accounts['total_assets']['current']
                if assets > 0:
                    ratios['roa'] = {
                        'value': (net_income / assets) * 100,
                        'name': 'ROA (총자산이익률)',
                        'unit': '%'
                    }
            
            # 영업이익률 = 영업이익 / 매출액 × 100
            if 'operating_profit' in accounts and 'revenue' in accounts:
                operating_profit = accounts['operating_profit']['current']
                revenue = accounts['revenue']['current']
                if revenue > 0:
                    ratios['operating_margin'] = {
                        'value': (operating_profit / revenue) * 100,
                        'name': '영업이익률',
                        'unit': '%'
                    }
            
            # 순이익률 = 당기순이익 / 매출액 × 100
            if 'net_income' in accounts and 'revenue' in accounts:
                net_income = accounts['net_income']['current']
                revenue = accounts['revenue']['current']
                if revenue > 0:
                    ratios['net_margin'] = {
                        'value': (net_income / revenue) * 100,
                        'name': '순이익률',
                        'unit': '%'
                    }
                    
        except (ZeroDivisionError, TypeError, KeyError):
            pass
        
        return ratios
    
    def _calculate_stability_ratios(self, accounts: Dict) -> Dict:
        """안정성 비율 계산"""
        ratios = {}
        
        try:
            # 부채비율 = 부채총계 / 자기자본 × 100
            if 'total_liabilities' in accounts and 'total_equity' in accounts:
                liabilities = accounts['total_liabilities']['current']
                equity = accounts['total_equity']['current']
                if equity > 0:
                    ratios['debt_ratio'] = {
                        'value': (liabilities / equity) * 100,
                        'name': '부채비율',
                        'unit': '%'
                    }
            
            # 자기자본비율 = 자기자본 / 총자산 × 100
            if 'total_equity' in accounts and 'total_assets' in accounts:
                equity = accounts['total_equity']['current']
                assets = accounts['total_assets']['current']
                if assets > 0:
                    ratios['equity_ratio'] = {
                        'value': (equity / assets) * 100,
                        'name': '자기자본비율',
                        'unit': '%'
                    }
            
            # 유동비율 = 유동자산 / 유동부채 × 100
            if 'current_assets' in accounts and 'current_liabilities' in accounts:
                current_assets = accounts['current_assets']['current']
                current_liabilities = accounts['current_liabilities']['current']
                if current_liabilities > 0:
                    ratios['current_ratio'] = {
                        'value': (current_assets / current_liabilities) * 100,
                        'name': '유동비율',
                        'unit': '%'
                    }
                    
        except (ZeroDivisionError, TypeError, KeyError):
            pass
        
        return ratios
    
    def _calculate_growth_ratios(self, accounts: Dict) -> Dict:
        """성장성 비율 계산"""
        ratios = {}
        
        try:
            # 매출액 증가율 = (당기매출액 - 전기매출액) / 전기매출액 × 100
            if 'revenue' in accounts:
                current_revenue = accounts['revenue']['current']
                previous_revenue = accounts['revenue']['previous']
                if previous_revenue > 0:
                    ratios['revenue_growth'] = {
                        'value': ((current_revenue - previous_revenue) / previous_revenue) * 100,
                        'name': '매출액 증가율',
                        'unit': '%'
                    }
            
            # 순이익 증가율 = (당기순이익 - 전기순이익) / 전기순이익 × 100
            if 'net_income' in accounts:
                current_income = accounts['net_income']['current']
                previous_income = accounts['net_income']['previous']
                if previous_income > 0:
                    ratios['income_growth'] = {
                        'value': ((current_income - previous_income) / previous_income) * 100,
                        'name': '순이익 증가율',
                        'unit': '%'
                    }
            
            # 자산 증가율 = (당기총자산 - 전기총자산) / 전기총자산 × 100
            if 'total_assets' in accounts:
                current_assets = accounts['total_assets']['current']
                previous_assets = accounts['total_assets']['previous']
                if previous_assets > 0:
                    ratios['asset_growth'] = {
                        'value': ((current_assets - previous_assets) / previous_assets) * 100,
                        'name': '총자산 증가율',
                        'unit': '%'
                    }
                    
        except (ZeroDivisionError, TypeError, KeyError):
            pass
        
        return ratios
    
    def _calculate_activity_ratios(self, accounts: Dict) -> Dict:
        """활동성 비율 계산"""
        ratios = {}
        
        try:
            # 총자산회전율 = 매출액 / 총자산
            if 'revenue' in accounts and 'total_assets' in accounts:
                revenue = accounts['revenue']['current']
                assets = accounts['total_assets']['current']
                if assets > 0:
                    ratios['asset_turnover'] = {
                        'value': revenue / assets,
                        'name': '총자산회전율',
                        'unit': '회'
                    }
                    
        except (ZeroDivisionError, TypeError, KeyError):
            pass
        
        return ratios
    
    def calculate_multi_year_ratios(self, multi_year_data: Dict) -> Dict:
        """여러 연도의 재무비율 계산"""
        multi_year_ratios = {}
        
        for year, data in multi_year_data.items():
            ratios = self.calculate_ratios(data)
            multi_year_ratios[year] = ratios
        
        return multi_year_ratios
    
    def get_ratio_trends(self, multi_year_ratios: Dict, ratio_category: str, ratio_name: str) -> Dict:
        """특정 비율의 연도별 추세 데이터 반환"""
        trend_data = {
            'years': [],
            'values': [],
            'ratio_info': None
        }
        
        for year in sorted(multi_year_ratios.keys()):
            ratios = multi_year_ratios[year]
            if ratio_category in ratios and ratio_name in ratios[ratio_category]:
                ratio_info = ratios[ratio_category][ratio_name]
                trend_data['years'].append(str(year))
                trend_data['values'].append(ratio_info['value'])
                if not trend_data['ratio_info']:
                    trend_data['ratio_info'] = {
                        'name': ratio_info['name'],
                        'unit': ratio_info['unit']
                    }
        
        return trend_data

# 테스트 함수
def test_ratios():
    """재무비율 계산 테스트"""
    print("💰 재무비율 계산 테스트")
    print("=" * 50)
    
    # 가상의 재무데이터로 테스트
    sample_data = {
        'raw_data': [
            {
                'account_name': '자산총계',
                'current_year': {'amount': 1000000000000},
                'previous_year': {'amount': 900000000000},
                'sj_div': 'BS'
            },
            {
                'account_name': '부채총계',
                'current_year': {'amount': 400000000000},
                'previous_year': {'amount': 380000000000},
                'sj_div': 'BS'
            },
            {
                'account_name': '자본총계',
                'current_year': {'amount': 600000000000},
                'previous_year': {'amount': 520000000000},
                'sj_div': 'BS'
            },
            {
                'account_name': '매출액',
                'current_year': {'amount': 800000000000},
                'previous_year': {'amount': 750000000000},
                'sj_div': 'IS'
            },
            {
                'account_name': '당기순이익',
                'current_year': {'amount': 80000000000},
                'previous_year': {'amount': 70000000000},
                'sj_div': 'IS'
            }
        ]
    }
    
    calculator = FinancialRatioCalculator()
    ratios = calculator.calculate_ratios(sample_data)
    
    for category, category_ratios in ratios.items():
        print(f"\n📊 {category.upper()} 비율:")
        for ratio_name, ratio_info in category_ratios.items():
            print(f"  - {ratio_info['name']}: {ratio_info['value']:.2f}{ratio_info['unit']}")

if __name__ == "__main__":
    test_ratios() 