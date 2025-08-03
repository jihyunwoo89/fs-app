#!/usr/bin/env python3
"""
재무제표 시각화 웹 애플리케이션
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS
import json
import os
import time
import plotly.graph_objs as go
import plotly.utils
import pandas as pd
from company_search import CompanySearcher
from financial_data import FinancialDataFetcher
from financial_ratios import FinancialRatioCalculator
from ai_analysis import FinancialAnalysisAI

app = Flask(__name__)
app.secret_key = 'financial_visualizer_secret_key'

# CORS 설정 추가
CORS(app, resources={
    r"/search": {"origins": "*"},
    r"/api/*": {"origins": "*"},
    r"/health": {"origins": "*"},
    r"/init": {"origins": "*"}
})

# 전역 객체 초기화
searcher = None
fetcher = None
ratio_calculator = None
ai_analyzer = None

def init_app(retry_count=0, max_retries=3):
    """애플리케이션 초기화 - 재시도 로직 포함"""
    global searcher, fetcher, ratio_calculator, ai_analyzer
    
    try:
        print(f"🚀 애플리케이션 초기화 중... (시도 {retry_count + 1}/{max_retries + 1})")
        
        # 작업 디렉토리 확인
        print(f"📁 현재 작업 디렉토리: {os.getcwd()}")
        
        # 필수 파일 존재 여부 미리 확인
        corp_files = ['corp_codes.json', 'corp_codes_sample.json']
        available_file = None
        for file in corp_files:
            if os.path.exists(file):
                file_size = os.path.getsize(file)
                print(f"📄 {file} 발견 (크기: {file_size:,} bytes)")
                available_file = file
                break
        
        if not available_file:
            raise FileNotFoundError("기업코드 파일이 없습니다. corp_codes.json 또는 corp_codes_sample.json이 필요합니다.")
        
        # 1. CompanySearcher 초기화
        print("📚 기업 검색 모듈 초기화 중...")
        try:
            searcher = CompanySearcher()
            print("✅ 기업 검색 모듈 초기화 성공")
        except Exception as e:
            print(f"❌ 기업 검색 모듈 초기화 실패: {e}")
            raise
        
        # 2. FinancialDataFetcher 초기화
        print("💰 재무데이터 모듈 초기화 중...")
        try:
            fetcher = FinancialDataFetcher()
            print("✅ 재무데이터 모듈 초기화 성공")
        except Exception as e:
            print(f"❌ 재무데이터 모듈 초기화 실패: {e}")
            raise
        
        # 3. FinancialRatioCalculator 초기화
        print("📊 재무비율 계산 모듈 초기화 중...")
        try:
            ratio_calculator = FinancialRatioCalculator()
            print("✅ 재무비율 계산 모듈 초기화 성공")
        except Exception as e:
            print(f"❌ 재무비율 계산 모듈 초기화 실패: {e}")
            raise
        
        # 4. AI 분석 모듈 초기화
        print("🤖 AI 분석 모듈 초기화 중...")
        try:
            ai_analyzer = FinancialAnalysisAI()
            print("✅ AI 분석 모듈 초기화 성공")
        except Exception as e:
            print(f"❌ AI 분석 모듈 초기화 실패: {e}")
            # AI 모듈 실패는 치명적이지 않음
            ai_analyzer = None
            print("⚠️ AI 분석 기능 없이 계속 진행합니다.")
        
        print("✅ 모든 모듈 초기화 완료!")
        return True
        
    except Exception as e:
        print(f"❌ 초기화 실패 (시도 {retry_count + 1}/{max_retries + 1}): {e}")
        print(f"❌ 상세 에러: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # 재시도 로직
        if retry_count < max_retries:
            print(f"⏰ {2 ** retry_count}초 후 재시도...")
            time.sleep(2 ** retry_count)  # 지수적 백오프
            return init_app(retry_count + 1, max_retries)
        else:
            print("❌ 최대 재시도 횟수 초과. 초기화 포기.")
            return False

@app.route('/health')
def health_check():
    """헬스체크 및 초기화 상태 확인"""
    status = {
        'searcher': searcher is not None,
        'fetcher': fetcher is not None,
        'ratio_calculator': ratio_calculator is not None,
        'ai_analyzer': ai_analyzer is not None,
        'all_initialized': all([searcher, fetcher, ratio_calculator, ai_analyzer])
    }
    
    # 파일 존재 여부 확인
    import os
    files_status = {
        'corp_codes.json': os.path.exists('corp_codes.json'),
        'corp_codes_sample.json': os.path.exists('corp_codes_sample.json'),
        'templates_exist': os.path.exists('templates'),
        'static_exist': os.path.exists('static')
    }
    
    # 환경변수 확인
    env_status = {
        'DART_API_KEY': bool(os.environ.get('DART_API_KEY')),
        'GEMINI_API_KEY': bool(os.environ.get('GEMINI_API_KEY')),
        'PORT': os.environ.get('PORT', 'not_set')
    }
    
    return jsonify({
        'status': 'healthy' if status['all_initialized'] else 'initializing',
        'modules': status,
        'files': files_status,
        'environment': env_status,
        'working_directory': os.getcwd()
    })

@app.route('/init')
def manual_init():
    """수동 초기화 트리거"""
    result = init_app()
    return jsonify({
        'success': result,
        'message': '초기화 성공!' if result else '초기화 실패. 로그를 확인하세요.',
        'redirect_to_health': '/health'
    })

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')

@app.route('/search')
def search_companies():
    """회사 검색 API - 강화된 오류 처리"""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({'companies': [], 'status': 'empty_query'})
        
        # 초기화 상태 확인
        if searcher is None:
            # 자동 재초기화 시도
            print("🔄 검색 요청 시 자동 재초기화 시도...")
            init_success = init_app()
            if not init_success or searcher is None:
                return jsonify({
                    'error': '애플리케이션 초기화가 완료되지 않았습니다. 잠시 후 다시 시도해주세요.',
                    'status': 'initialization_failed',
                    'suggestion': '/health 엔드포인트에서 상태를 확인하거나 /init 엔드포인트로 수동 초기화를 시도해보세요.'
                }), 503
        
        print(f"🔍 회사 검색 요청: '{query}'")
        
        # 상장기업 우선 검색
        try:
            listed_results = searcher.search_listed_companies(query, limit=5)
        except Exception as e:
            print(f"⚠️ 상장기업 검색 실패: {e}")
            listed_results = []
        
        # 전체 기업 검색
        try:
            all_results = searcher.search_by_name(query, limit=10)
        except Exception as e:
            print(f"⚠️ 전체 기업 검색 실패: {e}")
            all_results = []
        
        # 중복 제거하면서 상장기업을 앞에 배치
        seen = set()
        combined_results = []
        
        for company in listed_results + all_results:
            if company['corp_code'] not in seen:
                seen.add(company['corp_code'])
                combined_results.append(company)
            
            if len(combined_results) >= 10:
                break
        
        print(f"✅ 검색 결과: {len(combined_results)}개 기업 발견")
        
        return jsonify({
            'companies': combined_results,
            'status': 'success',
            'query': query,
            'total_found': len(combined_results)
        })
        
    except Exception as e:
        print(f"❌ 검색 중 예외 발생: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'error': f'검색 중 오류가 발생했습니다: {str(e)}',
            'status': 'error',
            'error_type': type(e).__name__
        }), 500

@app.route('/financial/<corp_code>')
def financial_dashboard(corp_code):
    """기업별 재무제표 대시보드"""
    if searcher is None:
        return "애플리케이션 초기화가 완료되지 않았습니다. 잠시 후 다시 시도해주세요.", 503
        
    try:
        # 기업 정보 조회
        company = searcher.get_by_corp_code(corp_code)
        if not company:
            return "기업을 찾을 수 없습니다.", 404
        
        return render_template('dashboard.html', 
                             company=company,
                             corp_code=corp_code)
    except Exception as e:
        return f"오류 발생: {e}", 500

@app.route('/api/financial/<corp_code>/<int:year>')
def get_financial_data(corp_code, year):
    """재무데이터 API"""
    try:
        # 보고서 유형 파라미터 받기 (기본값: 사업보고서)
        reprt_code = request.args.get('reprt_code', '11011')
        
        print(f"🔍 재무데이터 조회 요청: {corp_code}, {year}년, 보고서코드: {reprt_code}")
        
        raw_data = fetcher.get_financial_statements(corp_code, str(year), reprt_code)
        if not raw_data:
            return jsonify({'error': '데이터를 찾을 수 없습니다.'}), 404
        
        parsed_data = fetcher.parse_financial_data(raw_data)
        
        # 응답에 요청 정보 포함
        parsed_data['request_info'] = {
            'corp_code': corp_code,
            'year': year,
            'reprt_code': reprt_code,
            'report_name': get_report_name(reprt_code)
        }
        
        return jsonify(parsed_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_report_name(reprt_code):
    """보고서 코드를 이름으로 변환"""
    report_names = {
        '11011': '사업보고서',
        '11012': '반기보고서',
        '11013': '1분기보고서', 
        '11014': '3분기보고서'
    }
    return report_names.get(reprt_code, '알 수 없는 보고서')

@app.route('/api/ratios/<corp_code>/<int:year>')
def get_financial_ratios(corp_code, year):
    """재무비율 API"""
    try:
        # 보고서 유형 파라미터 받기 (기본값: 사업보고서)
        reprt_code = request.args.get('reprt_code', '11011')
        
        raw_data = fetcher.get_financial_statements(corp_code, str(year), reprt_code)
        if not raw_data:
            return jsonify({'error': '데이터를 찾을 수 없습니다.'}), 404
        
        parsed_data = fetcher.parse_financial_data(raw_data)
        ratios = ratio_calculator.calculate_ratios(parsed_data)
        
        return jsonify({
            'ratios': ratios,
            'year': year,
            'corp_code': corp_code,
            'reprt_code': reprt_code,
            'report_name': get_report_name(reprt_code)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai-analysis/<corp_code>/<int:year>')
def get_ai_analysis(corp_code, year):
    """AI 재무분석 API"""
    try:
        # 보고서 유형 파라미터 받기 (기본값: 사업보고서)
        reprt_code = request.args.get('reprt_code', '11011')
        
        # 회사 정보 조회
        company_info = searcher.get_by_corp_code(corp_code)
        company_name = company_info.get('corp_name', '알 수 없는 회사') if company_info else '알 수 없는 회사'
        
        # 재무제표 데이터 조회
        raw_data = fetcher.get_financial_statements(corp_code, str(year), reprt_code)
        if not raw_data:
            return jsonify({'error': '재무제표 데이터를 찾을 수 없습니다.'}), 404
        
        parsed_data = fetcher.parse_financial_data(raw_data)
        
        # 재무비율 계산
        ratios = ratio_calculator.calculate_ratios(parsed_data)
        
        # AI 분석 수행
        ai_analysis = ai_analyzer.analyze_financial_statement(company_name, parsed_data, ratios)
        
        # 할당량 초과 시 사용자 친화적인 메시지로 변환
        if ai_analysis == "quota_exceeded":
            ai_analysis = """## 🚫 AI 분석 서비스 일시 중단

**📊 Gemini AI 할당량 초과로 인해 현재 AI 분석을 제공할 수 없습니다.**

### 🔄 **해결 방법:**
- **24시간 후 다시 시도**: 무료 할당량이 매일 자정(UTC)에 리셋됩니다
- **수동 분석**: 아래 재무제표와 차트를 참고하여 직접 분석해보세요

### 📈 **분석 가이드:**
1. **매출액과 영업이익** 증감률 확인
2. **자산 대비 부채 비율** 검토  
3. **전년 대비 성장률** 비교

**죄송합니다. 조금 후에 다시 이용해주세요! 🙏**"""

        return jsonify({
            'company_name': company_name,
            'year': year,
            'corp_code': corp_code,
            'reprt_code': reprt_code,
            'report_name': get_report_name(reprt_code),
            'ai_analysis': ai_analysis,
            'ai_enabled': ai_analyzer.enabled,
            'quota_exceeded': ai_analysis and "할당량 초과" in ai_analysis
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai-comparison/<corp_code>')
def get_ai_comparison_analysis(corp_code):
    """AI 당기vs전기 비교분석 API"""
    try:
        years = request.args.get('years', '2022,2023').split(',')
        current_year = years[-1] if years else '2023'
        previous_year = str(int(current_year) - 1)
        
        # 회사 정보 조회
        company_info = searcher.get_by_corp_code(corp_code)
        company_name = company_info.get('corp_name', '알 수 없는 회사') if company_info else '알 수 없는 회사'
        
        # 비교 데이터 생성 (기존 comparison 차트 로직 활용)
        current_data = fetcher.get_financial_statements(corp_code, current_year)
        previous_data = fetcher.get_financial_statements(corp_code, previous_year)
        
        if not current_data or not previous_data:
            return jsonify({'error': f'{current_year}년 또는 {previous_year}년 데이터가 없습니다.'}), 404
        
        current_parsed = fetcher.parse_financial_data(current_data)
        previous_parsed = fetcher.parse_financial_data(previous_data)
        
        # 비교 데이터 테이블 생성
        comparison_data = create_comparison_data_table(current_parsed, previous_parsed, current_year, previous_year)
        
        if not comparison_data:
            return jsonify({'error': '비교 데이터를 생성할 수 없습니다.'}), 404
        
        # AI 비교 분석 수행
        ai_analysis = ai_analyzer.analyze_comparison_data(company_name, comparison_data)
        
        # 할당량 초과 시 사용자 친화적인 메시지로 변환
        if ai_analysis == "quota_exceeded":
            ai_analysis = """## 🚫 AI 비교분석 서비스 일시 중단

**📊 Gemini AI 할당량 초과로 인해 현재 AI 비교분석을 제공할 수 없습니다.**

### 🔄 **해결 방법:**
- **24시간 후 다시 시도**: 무료 할당량이 매일 자정(UTC)에 리셋됩니다
- **수동 비교**: 아래 비교 차트를 참고하여 직접 분석해보세요

### 📊 **비교분석 가이드:**
1. **매출 성장률**: 전년 대비 증가/감소율 확인
2. **수익성 변화**: 영업이익률, 순이익률 비교
3. **안정성 변화**: 부채비율, 유동비율 변화 추이

**죄송합니다. 조금 후에 다시 이용해주세요! 🙏**"""

        return jsonify({
            'company_name': company_name,
            'current_year': current_year,
            'previous_year': previous_year,
            'corp_code': corp_code,
            'ai_analysis': ai_analysis,
            'ai_enabled': ai_analyzer.enabled,
            'quota_exceeded': ai_analysis and "할당량 초과" in ai_analysis
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chart/<corp_code>')
def generate_charts(corp_code):
    """차트 생성 API"""
    try:
        years = request.args.get('years', '2021,2022,2023').split(',')
        chart_type = request.args.get('type', 'trend')
        
        charts = {}
        
        if chart_type == 'trend':
            charts = create_trend_charts(corp_code, years)
        elif chart_type == 'structure':
            charts = create_structure_charts(corp_code, years[-1])  # 최신년도
        elif chart_type == 'ratios':
            charts = create_ratio_charts(corp_code, years)
        elif chart_type == 'comparison':
            current_year = years[-1] if years else '2023'
            previous_year = str(int(current_year) - 1)
            charts = create_comparison_charts(corp_code, current_year, previous_year)
        
        return jsonify(charts)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def create_trend_charts(corp_code, years):
    """추세 차트 생성"""
    charts = {}
    
    # 여러 연도 데이터 수집
    multi_year_data = {}
    for year in years:
        try:
            raw_data = fetcher.get_financial_statements(corp_code, year)
            if raw_data:
                parsed_data = fetcher.parse_financial_data(raw_data)
                multi_year_data[int(year)] = parsed_data
        except:
            continue
    
    if not multi_year_data:
        return {'error': '데이터가 없습니다.'}
    
    # 1. 매출액 및 순이익 추세
    revenue_data = []
    profit_data = []
    years_list = sorted(multi_year_data.keys())
    
    for year in years_list:
        data = multi_year_data[year]
        
        # 매출액 찾기
        for item in data.get('raw_data', []):
            if '매출액' in item['account_name'] and item['sj_div'] == 'IS':
                revenue_data.append(item['current_year']['amount'])
                break
        else:
            revenue_data.append(0)
        
        # 순이익 찾기
        for item in data.get('raw_data', []):
            if '당기순이익' in item['account_name'] and item['sj_div'] == 'IS':
                profit_data.append(item['current_year']['amount'])
                break
        else:
            profit_data.append(0)
    
    # 매출액 차트
    revenue_chart = go.Figure()
    revenue_chart.add_trace(go.Scatter(
        x=[str(y) for y in years_list],
        y=[r/1_000_000_000_000 for r in revenue_data],  # 조원 단위
        mode='lines+markers',
        name='매출액',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=8)
    ))
    
    revenue_chart.update_layout(
        title='매출액 추세 (조원)',
        xaxis_title='연도',
        yaxis_title='매출액 (조원)',
        template='plotly_white',
        height=400
    )
    
    # 순이익 차트
    profit_chart = go.Figure()
    profit_chart.add_trace(go.Scatter(
        x=[str(y) for y in years_list],
        y=[p/1_000_000_000_000 for p in profit_data],  # 조원 단위
        mode='lines+markers',
        name='순이익',
        line=dict(color='#2ca02c', width=3),
        marker=dict(size=8)
    ))
    
    profit_chart.update_layout(
        title='순이익 추세 (조원)',
        xaxis_title='연도',
        yaxis_title='순이익 (조원)',
        template='plotly_white',
        height=400
    )
    
    charts['revenue_trend'] = json.loads(plotly.utils.PlotlyJSONEncoder().encode(revenue_chart))
    charts['profit_trend'] = json.loads(plotly.utils.PlotlyJSONEncoder().encode(profit_chart))
    
    return charts

def create_ratio_charts(corp_code, years):
    """재무비율 차트 생성"""
    charts = {}
    
    try:
        # 여러 연도 재무데이터 수집
        multi_year_data = {}
        for year in years:
            try:
                raw_data = fetcher.get_financial_statements(corp_code, year)
                if raw_data:
                    parsed_data = fetcher.parse_financial_data(raw_data)
                    multi_year_data[int(year)] = parsed_data
            except:
                continue
        
        if not multi_year_data:
            return {'error': '재무비율 계산을 위한 데이터가 없습니다.'}
        
        # 재무비율 계산
        multi_year_ratios = ratio_calculator.calculate_multi_year_ratios(multi_year_data)
        
        # 1. 수익성 비율 차트
        profitability_chart = create_profitability_chart(multi_year_ratios)
        if profitability_chart:
            charts['profitability'] = profitability_chart
        
        # 2. 안정성 비율 차트
        stability_chart = create_stability_chart(multi_year_ratios)
        if stability_chart:
            charts['stability'] = stability_chart
        
        # 3. 성장성 비율 차트
        growth_chart = create_growth_chart(multi_year_ratios)
        if growth_chart:
            charts['growth'] = growth_chart
        
        # 4. 종합 비율 비교 차트
        comparison_chart = create_ratio_comparison_chart(multi_year_ratios)
        if comparison_chart:
            charts['comparison'] = comparison_chart
        
    except Exception as e:
        charts['error'] = str(e)
    
    return charts

def create_profitability_chart(multi_year_ratios):
    """수익성 비율 차트 생성"""
    try:
        years_list = sorted(multi_year_ratios.keys())
        
        # ROE, ROA, 영업이익률, 순이익률 데이터 수집
        roe_data = []
        roa_data = []
        operating_margin_data = []
        net_margin_data = []
        
        for year in years_list:
            ratios = multi_year_ratios[year]
            profitability = ratios.get('profitability', {})
            
            roe_data.append(profitability.get('roe', {}).get('value', 0))
            roa_data.append(profitability.get('roa', {}).get('value', 0))
            operating_margin_data.append(profitability.get('operating_margin', {}).get('value', 0))
            net_margin_data.append(profitability.get('net_margin', {}).get('value', 0))
        
        # 차트 생성
        chart = go.Figure()
        
        chart.add_trace(go.Scatter(
            x=[str(y) for y in years_list],
            y=roe_data,
            mode='lines+markers',
            name='ROE (%)',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=8)
        ))
        
        chart.add_trace(go.Scatter(
            x=[str(y) for y in years_list],
            y=roa_data,
            mode='lines+markers',
            name='ROA (%)',
            line=dict(color='#ff7f0e', width=3),
            marker=dict(size=8)
        ))
        
        chart.add_trace(go.Scatter(
            x=[str(y) for y in years_list],
            y=operating_margin_data,
            mode='lines+markers',
            name='영업이익률 (%)',
            line=dict(color='#2ca02c', width=3),
            marker=dict(size=8)
        ))
        
        chart.add_trace(go.Scatter(
            x=[str(y) for y in years_list],
            y=net_margin_data,
            mode='lines+markers',
            name='순이익률 (%)',
            line=dict(color='#d62728', width=3),
            marker=dict(size=8)
        ))
        
        chart.update_layout(
            title='수익성 비율 추세',
            xaxis_title='연도',
            yaxis_title='비율 (%)',
            template='plotly_white',
            height=400,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        return json.loads(plotly.utils.PlotlyJSONEncoder().encode(chart))
    
    except Exception as e:
        print(f"수익성 차트 생성 오류: {e}")
        return None

def create_stability_chart(multi_year_ratios):
    """안정성 비율 차트 생성"""
    try:
        years_list = sorted(multi_year_ratios.keys())
        
        debt_ratio_data = []
        equity_ratio_data = []
        current_ratio_data = []
        
        for year in years_list:
            ratios = multi_year_ratios[year]
            stability = ratios.get('stability', {})
            
            debt_ratio_data.append(stability.get('debt_ratio', {}).get('value', 0))
            equity_ratio_data.append(stability.get('equity_ratio', {}).get('value', 0))
            current_ratio_data.append(stability.get('current_ratio', {}).get('value', 0))
        
        # 두 개의 서브플롯 생성
        from plotly.subplots import make_subplots
        
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('부채 vs 자기자본 비율', '유동비율'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # 첫 번째 서브플롯: 부채비율, 자기자본비율
        fig.add_trace(
            go.Scatter(
                x=[str(y) for y in years_list],
                y=debt_ratio_data,
                mode='lines+markers',
                name='부채비율 (%)',
                line=dict(color='#d62728', width=3)
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=[str(y) for y in years_list],
                y=equity_ratio_data,
                mode='lines+markers',
                name='자기자본비율 (%)',
                line=dict(color='#2ca02c', width=3)
            ),
            row=1, col=1
        )
        
        # 두 번째 서브플롯: 유동비율
        fig.add_trace(
            go.Scatter(
                x=[str(y) for y in years_list],
                y=current_ratio_data,
                mode='lines+markers',
                name='유동비율 (%)',
                line=dict(color='#1f77b4', width=3),
                showlegend=True
            ),
            row=1, col=2
        )
        
        fig.update_layout(
            title_text="안정성 비율 분석",
            template='plotly_white',
            height=400
        )
        
        fig.update_xaxes(title_text="연도", row=1, col=1)
        fig.update_xaxes(title_text="연도", row=1, col=2)
        fig.update_yaxes(title_text="비율 (%)", row=1, col=1)
        fig.update_yaxes(title_text="비율 (%)", row=1, col=2)
        
        return json.loads(plotly.utils.PlotlyJSONEncoder().encode(fig))
    
    except Exception as e:
        print(f"안정성 차트 생성 오류: {e}")
        return None

def create_growth_chart(multi_year_ratios):
    """성장성 비율 차트 생성"""
    try:
        years_list = sorted(multi_year_ratios.keys())
        
        revenue_growth_data = []
        income_growth_data = []
        asset_growth_data = []
        
        for year in years_list:
            ratios = multi_year_ratios[year]
            growth = ratios.get('growth', {})
            
            revenue_growth_data.append(growth.get('revenue_growth', {}).get('value', 0))
            income_growth_data.append(growth.get('income_growth', {}).get('value', 0))
            asset_growth_data.append(growth.get('asset_growth', {}).get('value', 0))
        
        # 막대 차트 생성
        chart = go.Figure()
        
        chart.add_trace(go.Bar(
            x=[str(y) for y in years_list],
            y=revenue_growth_data,
            name='매출액 증가율',
            marker_color='#1f77b4'
        ))
        
        chart.add_trace(go.Bar(
            x=[str(y) for y in years_list],
            y=income_growth_data,
            name='순이익 증가율',
            marker_color='#ff7f0e'
        ))
        
        chart.add_trace(go.Bar(
            x=[str(y) for y in years_list],
            y=asset_growth_data,
            name='총자산 증가율',
            marker_color='#2ca02c'
        ))
        
        chart.update_layout(
            title='성장성 비율 분석',
            xaxis_title='연도',
            yaxis_title='증가율 (%)',
            template='plotly_white',
            height=400,
            barmode='group'
        )
        
        return json.loads(plotly.utils.PlotlyJSONEncoder().encode(chart))
    
    except Exception as e:
        print(f"성장성 차트 생성 오류: {e}")
        return None

def create_ratio_comparison_chart(multi_year_ratios):
    """종합 비율 비교 차트 (레이더 차트) - 4가지 주요 비율"""
    try:
        # 최신 연도의 데이터 사용
        latest_year = max(multi_year_ratios.keys())
        ratios = multi_year_ratios[latest_year]
        
        # 4가지 주요 비율 선택
        categories = []
        values = []
        
        profitability = ratios.get('profitability', {})
        
        # 1. 순이익률
        if 'net_margin' in profitability:
            categories.append('순이익률')
            values.append(max(0, min(profitability['net_margin']['value'], 50)))  # 0-50% 범위
        
        # 2. 영업이익률
        if 'operating_margin' in profitability:
            categories.append('영업이익률')
            values.append(max(0, min(profitability['operating_margin']['value'], 50)))  # 0-50% 범위
        
        # 3. ROE (자기자본이익률)
        if 'roe' in profitability:
            categories.append('ROE(자기자본이익률)')
            values.append(max(0, min(profitability['roe']['value'], 30)))  # 0-30% 범위
        
        # 4. ROA (총자산이익률)
        if 'roa' in profitability:
            categories.append('ROA(총자산이익률)')
            values.append(max(0, min(profitability['roa']['value'], 20)))  # 0-20% 범위
        
        if not categories:
            return None
        
        # 레이더 차트 생성
        chart = go.Figure()
        
        chart.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name=f'{latest_year}년 주요 재무비율',
            line_color='#1f77b4',
            fillcolor='rgba(31, 119, 180, 0.3)',
            line_width=3,
            marker=dict(size=8, color='#1f77b4')
        ))
        
        # 최대값 계산 (적어도 10은 되도록)
        max_value = max(max(values) * 1.3, 10) if values else 20
        
        chart.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, max_value],
                    tickmode='linear',
                    tick0=0,
                    dtick=max_value/5,
                    ticksuffix='%',
                    gridcolor='lightgray'
                ),
                angularaxis=dict(
                    gridcolor='lightgray'
                )
            ),
            title=dict(
                text=f'{latest_year}년 주요 재무비율 종합 분석',
                x=0.5,
                font=dict(size=16, color='darkblue')
            ),
            template='plotly_white',
            height=500,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.1,
                xanchor="center",
                x=0.5
            )
        )
        
        return json.loads(plotly.utils.PlotlyJSONEncoder().encode(chart))
    
    except Exception as e:
        print(f"종합 비교 차트 생성 오류: {e}")
        return None

def create_comparison_charts(corp_code, current_year, previous_year):
    """당기vs전기 비교 차트 생성"""
    charts = {}
    
    try:
        # 당기와 전기 데이터 가져오기
        current_data = fetcher.get_financial_statements(corp_code, current_year)
        previous_data = fetcher.get_financial_statements(corp_code, previous_year)
        
        if not current_data or not previous_data:
            return {'error': f'{current_year}년 또는 {previous_year}년 데이터가 없습니다.'}
        
        current_parsed = fetcher.parse_financial_data(current_data)
        previous_parsed = fetcher.parse_financial_data(previous_data)
        
        # 1. 손익계산서 비교 차트
        income_chart = create_income_comparison_chart(current_parsed, previous_parsed, current_year, previous_year)
        if income_chart:
            charts['income_comparison'] = income_chart
        
        # 2. 재무상태표 비교 차트
        balance_chart = create_balance_comparison_chart(current_parsed, previous_parsed, current_year, previous_year)
        if balance_chart:
            charts['balance_comparison'] = balance_chart
        
        # 3. 증감률 분석 차트
        growth_analysis_chart = create_growth_analysis_chart(current_parsed, previous_parsed, current_year, previous_year)
        if growth_analysis_chart:
            charts['growth_analysis'] = growth_analysis_chart
        
        # 4. 비교 데이터 테이블
        comparison_data = create_comparison_data_table(current_parsed, previous_parsed, current_year, previous_year)
        if comparison_data:
            charts['comparison_data'] = comparison_data
        
    except Exception as e:
        charts['error'] = str(e)
    
    return charts

def create_income_comparison_chart(current_data, previous_data, current_year, previous_year):
    """손익계산서 비교 차트"""
    try:
        # 주요 손익계산서 항목 추출
        income_items = ['매출액', '영업이익', '당기순이익']
        current_values = []
        previous_values = []
        labels = []
        
        for item in income_items:
            current_val = 0
            previous_val = 0
            
            # 당기 데이터 검색
            for data in current_data.get('raw_data', []):
                if item in data.get('account_name', '') and data.get('sj_div') == 'IS':
                    current_val = data.get('current_year', {}).get('amount', 0)
                    break
            
            # 전기 데이터 검색
            for data in previous_data.get('raw_data', []):
                if item in data.get('account_name', '') and data.get('sj_div') == 'IS':
                    previous_val = data.get('current_year', {}).get('amount', 0)
                    break
            
            if current_val > 0 or previous_val > 0:
                current_values.append(current_val / 1_000_000_000_000)  # 조원 단위
                previous_values.append(previous_val / 1_000_000_000_000)
                labels.append(item)
        
        if not labels:
            return None
        
        # 그룹 막대 차트 생성
        chart = go.Figure()
        
        chart.add_trace(go.Bar(
            name=f'{previous_year}년',
            x=labels,
            y=previous_values,
            marker_color='#ff7f0e',
            text=[f'{val:.1f}조' for val in previous_values],
            textposition='auto'
        ))
        
        chart.add_trace(go.Bar(
            name=f'{current_year}년',
            x=labels,
            y=current_values,
            marker_color='#1f77b4',
            text=[f'{val:.1f}조' for val in current_values],
            textposition='auto'
        ))
        
        chart.update_layout(
            title=f'손익계산서 비교 ({previous_year} vs {current_year})',
            xaxis_title='항목',
            yaxis_title='금액 (조원)',
            template='plotly_white',
            height=400,
            barmode='group'
        )
        
        return json.loads(plotly.utils.PlotlyJSONEncoder().encode(chart))
    
    except Exception as e:
        print(f"손익계산서 비교 차트 생성 오류: {e}")
        return None

def create_balance_comparison_chart(current_data, previous_data, current_year, previous_year):
    """재무상태표 비교 차트"""
    try:
        # 주요 재무상태표 항목 추출
        balance_items = ['자산총계', '부채총계', '자본총계']
        current_values = []
        previous_values = []
        labels = []
        
        for item in balance_items:
            current_val = 0
            previous_val = 0
            
            # 당기 데이터 검색
            for data in current_data.get('raw_data', []):
                if item in data.get('account_name', '') and data.get('sj_div') == 'BS':
                    current_val = data.get('current_year', {}).get('amount', 0)
                    break
            
            # 전기 데이터 검색
            for data in previous_data.get('raw_data', []):
                if item in data.get('account_name', '') and data.get('sj_div') == 'BS':
                    previous_val = data.get('current_year', {}).get('amount', 0)
                    break
            
            if current_val > 0 or previous_val > 0:
                current_values.append(current_val / 1_000_000_000_000)  # 조원 단위
                previous_values.append(previous_val / 1_000_000_000_000)
                labels.append(item)
        
        if not labels:
            return None
        
        # 그룹 막대 차트 생성
        chart = go.Figure()
        
        chart.add_trace(go.Bar(
            name=f'{previous_year}년',
            x=labels,
            y=previous_values,
            marker_color='#2ca02c',
            text=[f'{val:.1f}조' for val in previous_values],
            textposition='auto'
        ))
        
        chart.add_trace(go.Bar(
            name=f'{current_year}년',
            x=labels,
            y=current_values,
            marker_color='#d62728',
            text=[f'{val:.1f}조' for val in current_values],
            textposition='auto'
        ))
        
        chart.update_layout(
            title=f'재무상태표 비교 ({previous_year} vs {current_year})',
            xaxis_title='항목',
            yaxis_title='금액 (조원)',
            template='plotly_white',
            height=400,
            barmode='group'
        )
        
        return json.loads(plotly.utils.PlotlyJSONEncoder().encode(chart))
    
    except Exception as e:
        print(f"재무상태표 비교 차트 생성 오류: {e}")
        return None

def create_growth_analysis_chart(current_data, previous_data, current_year, previous_year):
    """증감률 분석 차트"""
    try:
        # 주요 항목들의 증감률 계산
        items = [
            ('매출액', 'IS'),
            ('영업이익', 'IS'),
            ('당기순이익', 'IS'),
            ('자산총계', 'BS'),
            ('부채총계', 'BS'),
            ('자본총계', 'BS')
        ]
        
        growth_rates = []
        labels = []
        colors = []
        
        for item_name, div in items:
            current_val = 0
            previous_val = 0
            
            # 데이터 검색
            for data in current_data.get('raw_data', []):
                if item_name in data.get('account_name', '') and data.get('sj_div') == div:
                    current_val = data.get('current_year', {}).get('amount', 0)
                    break
            
            for data in previous_data.get('raw_data', []):
                if item_name in data.get('account_name', '') and data.get('sj_div') == div:
                    previous_val = data.get('current_year', {}).get('amount', 0)
                    break
            
            # 증감률 계산
            if previous_val > 0:
                growth_rate = ((current_val - previous_val) / previous_val) * 100
                growth_rates.append(growth_rate)
                labels.append(item_name)
                colors.append('#2ca02c' if growth_rate >= 0 else '#d62728')
        
        if not labels:
            return None
        
        # 가로 막대 차트 생성
        chart = go.Figure()
        
        chart.add_trace(go.Bar(
            y=labels,
            x=growth_rates,
            orientation='h',
            marker_color=colors,
            text=[f'{rate:+.1f}%' for rate in growth_rates],
            textposition='auto'
        ))
        
        chart.update_layout(
            title=f'주요 항목 증감률 분석 ({previous_year} → {current_year})',
            xaxis_title='증감률 (%)',
            yaxis_title='항목',
            template='plotly_white',
            height=400
        )
        
        # 0% 기준선 추가
        chart.add_vline(x=0, line_dash="dash", line_color="gray")
        
        return json.loads(plotly.utils.PlotlyJSONEncoder().encode(chart))
    
    except Exception as e:
        print(f"증감률 분석 차트 생성 오류: {e}")
        return None

def create_comparison_data_table(current_data, previous_data, current_year, previous_year):
    """비교 데이터 테이블 생성"""
    try:
        # 주요 항목들
        items = [
            ('매출액', 'IS'),
            ('영업이익', 'IS'),
            ('당기순이익', 'IS'),
            ('자산총계', 'BS'),
            ('부채총계', 'BS'),
            ('자본총계', 'BS')
        ]
        
        table_data = []
        
        for item_name, div in items:
            current_val = 0
            previous_val = 0
            
            # 데이터 검색
            for data in current_data.get('raw_data', []):
                if item_name in data.get('account_name', '') and data.get('sj_div') == div:
                    current_val = data.get('current_year', {}).get('amount', 0)
                    break
            
            for data in previous_data.get('raw_data', []):
                if item_name in data.get('account_name', '') and data.get('sj_div') == div:
                    previous_val = data.get('current_year', {}).get('amount', 0)
                    break
            
            # 증감액과 증감률 계산
            diff_amount = current_val - previous_val
            growth_rate = ((current_val - previous_val) / previous_val * 100) if previous_val > 0 else 0
            
            table_data.append({
                'item': item_name,
                'previous_year': previous_year,
                'previous_amount': previous_val,
                'current_year': current_year,
                'current_amount': current_val,
                'diff_amount': diff_amount,
                'growth_rate': growth_rate
            })
        
        return table_data
    
    except Exception as e:
        print(f"비교 데이터 테이블 생성 오류: {e}")
        return None

def create_structure_charts(corp_code, year):
    """구조 차트 생성 (최신년도)"""
    charts = {}
    
    try:
        raw_data = fetcher.get_financial_statements(corp_code, year)
        if not raw_data:
            return {'error': '데이터가 없습니다.'}
        
        parsed_data = fetcher.parse_financial_data(raw_data)
        
        # 자산 구조 차트 (파이 차트)
        assets_data = []
        assets_labels = []
        
        for account_name, item in parsed_data['balance_sheet']['assets'].items():
            if '총계' not in account_name:  # 총계는 제외
                assets_labels.append(account_name)
                assets_data.append(item['current_year']['amount'] / 1_000_000_000_000)  # 조원
        
        if assets_data:
            assets_chart = go.Figure(data=[go.Pie(
                labels=assets_labels,
                values=assets_data,
                hole=.3,
                textinfo='label+percent',
                textposition='outside'
            )])
            
            assets_chart.update_layout(
                title=f'{year}년 자산 구조',
                template='plotly_white',
                height=500
            )
            
            charts['assets_structure'] = json.loads(plotly.utils.PlotlyJSONEncoder().encode(assets_chart))
        
        # 자본 vs 부채 비교 (막대 차트)
        categories = []
        amounts = []
        
        # 자본총계
        for item in parsed_data['raw_data']:
            if '자본총계' in item['account_name']:
                categories.append('자본총계')
                amounts.append(item['current_year']['amount'] / 1_000_000_000_000)
                break
        
        # 부채총계
        for item in parsed_data['raw_data']:
            if '부채총계' in item['account_name']:
                categories.append('부채총계')
                amounts.append(item['current_year']['amount'] / 1_000_000_000_000)
                break
        
        if categories and amounts:
            debt_equity_chart = go.Figure(data=[
                go.Bar(
                    x=categories,
                    y=amounts,
                    marker_color=['#ff7f0e', '#d62728'],
                    text=[f'{a:.1f}조원' for a in amounts],
                    textposition='auto'
                )
            ])
            
            debt_equity_chart.update_layout(
                title=f'{year}년 자본 vs 부채',
                yaxis_title='금액 (조원)',
                template='plotly_white',
                height=400
            )
            
            charts['debt_equity'] = json.loads(plotly.utils.PlotlyJSONEncoder().encode(debt_equity_chart))
        
    except Exception as e:
        charts['error'] = str(e)
    
    return charts

if __name__ == '__main__':
    # 포트 설정
    port = int(os.environ.get('PORT', 8080))
    
    # 초기화 시도
    init_success = init_app()
    
    if init_success:
        print("🌐 웹 서버 시작!")
        print(f"📍 http://localhost:{port} 에서 접속하세요")
    else:
        print("⚠️ 초기화 실패했지만 서버를 시작합니다. /health 및 /init 엔드포인트를 통해 복구를 시도할 수 있습니다.")
        print("🌐 제한된 모드로 웹 서버 시작!")
        print(f"📍 http://localhost:{port} 에서 접속하세요")
        print("🔧 복구를 위해 {}/health 또는 {}/init을 방문하세요".format(
            f"http://localhost:{port}", f"http://localhost:{port}"
        ))
    
    # 서버 시작 (초기화 성공 여부와 관계없이)
    try:
        app.run(debug=False, host='0.0.0.0', port=port)
    except Exception as e:
        print(f"❌ 서버 시작 실패: {e}")
        exit(1) 