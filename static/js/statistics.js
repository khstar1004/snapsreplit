document.addEventListener('DOMContentLoaded', function() {
    // 게시물 성과 차트
    const postPerformanceCtx = document.getElementById('postPerformanceChart').getContext('2d');
    new Chart(postPerformanceCtx, {
        type: 'bar',
        data: {
            labels: ['게시물 1', '게시물 2', '게시물 3', '게시물 4', '게시물 5'],
            datasets: [{
                label: '좋아요 수',
                data: [120, 190, 300, 150, 200],
                backgroundColor: 'rgba(75, 192, 192, 0.6)'
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });

    // 팔로워 증가 차트
    const followerGrowthCtx = document.getElementById('followerGrowthChart').getContext('2d');
    new Chart(followerGrowthCtx, {
        type: 'line',
        data: {
            labels: ['1월', '2월', '3월', '4월', '5월'],
            datasets: [{
                label: '팔로워 수',
                data: [1000, 1200, 1400, 1600, 2000],
                borderColor: 'rgba(153, 102, 255, 1)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });

    // 인기 해시태그
    const popularHashtags = ['#여행', '#맛집', '#일상', '#OOTD', '#뷰티'];
    const hashtagList = document.getElementById('popularHashtags');
    popularHashtags.forEach(tag => {
        const li = document.createElement('li');
        li.textContent = tag;
        hashtagList.appendChild(li);
    });

    // 최근 활동
    const recentActivities = [
        { date: '2024-03-15', activity: '새 게시물 업로드', performance: '좋아요 150개' },
        { date: '2024-03-14', activity: '스토리 공유', performance: '조회수 500회' },
        { date: '2024-03-13', activity: '댓글 응답', performance: '팔로워 10명 증가' }
    ];
    const activityTable = document.getElementById('recentActivity').getElementsByTagName('tbody')[0];
    recentActivities.forEach(activity => {
        const row = activityTable.insertRow();
        row.insertCell(0).textContent = activity.date;
        row.insertCell(1).textContent = activity.activity;
        row.insertCell(2).textContent = activity.performance;
    });
});