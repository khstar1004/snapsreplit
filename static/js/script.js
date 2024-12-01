document.addEventListener('DOMContentLoaded', function() {
    // 현재 페이지 URL에 따라 해당 네비게이션 버튼 강조
    const currentPath = window.location.pathname;
    const navButtons = document.querySelectorAll('nav button');
    
    navButtons.forEach(button => {
        if (button.getAttribute('onclick').includes(currentPath)) {
            button.classList.add('active');
        }
    });

    // 특성 카드에 마우스 오버 효과 추가
    const featureCards = document.querySelectorAll('.feature-card');
    
    featureCards.forEach(card => {
        card.addEventListener('mouseover', function() {
            this.style.transform = 'scale(1.05)';
        });
        
        card.addEventListener('mouseout', function() {
            this.style.transform = 'scale(1)';
        });
    });

    // 추가적인 JavaScript 기능은 여기에 구현할 수 있습니다.
});