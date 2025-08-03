// 메인 애플리케이션 JavaScript

// 유틸리티 함수들
const Utils = {
    // 숫자를 한국 원화 형식으로 포맷
    formatCurrency: function(amount) {
        if (!amount || isNaN(amount)) return '0원';
        return new Intl.NumberFormat('ko-KR', {
            style: 'currency',
            currency: 'KRW',
            minimumFractionDigits: 0
        }).format(amount);
    },

    // 숫자를 백만원 단위로 포맷
    formatToMillion: function(amount) {
        if (!amount || isNaN(amount)) return '0';
        return (amount / 1000000).toFixed(0) + '백만원';
    },

    // 로딩 스피너 표시
    showLoading: function(element) {
        if (element) {
            element.innerHTML = '<div class="loading"></div> 로딩 중...';
        }
    },

    // 에러 메시지 표시
    showError: function(element, message) {
        if (element) {
            element.innerHTML = `<div class="alert alert-danger">${message}</div>`;
        }
    }
};

// 페이지 로드 완료 시 실행
document.addEventListener('DOMContentLoaded', function() {
    console.log('📊 재무분석 대시보드 로딩 완료');
});