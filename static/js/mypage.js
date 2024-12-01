function editProfile() {
    // 프로필 수정 로직
    alert('프로필 수정 기능은 현재 개발 중입니다.');
}

function refreshInstagramToken() {
    alert('토큰이 갱신되었습니다.');
}

async function linkInstagramAccount() {
    try {
        const response = await fetch('/auth/instagram', {
            method: 'GET',
            headers: {
                'Accept': 'application/json'
            }
        });

        const data = await response.json();
        
        if (data.success) {
            // 연동 상태 UI 업데이트
            const statusElement = document.querySelector('.connection-status');
            statusElement.classList.remove('not-connected');
            statusElement.classList.add('connected');
            statusElement.innerHTML = '<span>✓ 연동됨</span>';
            
            // 버튼 변경
            const button = statusElement.nextElementSibling;
            button.className = 'secondary-button';
            button.textContent = '토큰 갱신';
            button.onclick = refreshInstagramToken;
            
            alert('Instagram 계정이 성공적으로 연동되었습니다.');
        } else {
            alert(data.error || 'Instagram 연동에 실패했습니다.');
        }
    } catch (error) {
        console.error('Instagram 연동 오류:', error);
        alert('Instagram 연동 중 오류가 발생했습니다.');
    }
}

async function checkThreadConnection() {
    try {
        const response = await fetch('/check_thread_account');
        const data = await response.json();
        
        const statusElement = document.getElementById('threadConnectionStatus');
        if (data.linked) {
            statusElement.innerHTML = '<span>✓ 연동됨</span>';
            statusElement.className = 'connection-status connected';
            document.querySelector('.connection-card button').textContent = 'Thread 연동 해제';
            document.querySelector('.connection-card button').onclick = unlinkThreadAccount;
        } else {
            statusElement.innerHTML = '<span>연동되지 않음</span>';
            statusElement.className = 'connection-status not-connected';
            document.querySelector('.connection-card button').textContent = 'Thread 연동하기';
            document.querySelector('.connection-card button').onclick = linkThreadAccount;
        }
    } catch (error) {
        console.error('Thread connection check failed:', error);
    }
}

async function linkThreadAccount() {
    try {
        const response = await fetch('/link_thread_account', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                thread_user_id: "28229663363291121"
            })
        });
        
        const data = await response.json();
        if (data.success) {
            const statusElement = document.getElementById('threadConnectionStatus');
            statusElement.innerHTML = '<span>✓ 연동됨</span>';
            statusElement.className = 'connection-status connected';
            
            const button = statusElement.nextElementSibling;
            button.textContent = 'Thread 연동 해제';
            button.className = 'secondary-button';
            button.onclick = unlinkThreadAccount;
            
            alert('Thread 계정이 성공적으로 연동되었습니다.');
        } else {
            alert(data.error || 'Thread 계정 연동에 실패했습니다.');
        }
    } catch (error) {
        console.error('Thread account linking failed:', error);
        alert('Thread 계정 연동 중 오류가 발생했습니다.');
    }
}

async function unlinkThreadAccount() {
    if (!confirm('Thread 계정 연동을 해제하시겠습니까?')) {
        return;
    }
    
    try {
        const response = await fetch('/unlink_thread_account', {
            method: 'POST'
        });
        
        const data = await response.json();
        if (data.success) {
            const statusElement = document.getElementById('threadConnectionStatus');
            statusElement.innerHTML = '<span>연동되지 않음</span>';
            statusElement.className = 'connection-status not-connected';
            
            const button = statusElement.nextElementSibling;
            button.textContent = 'Thread 연동하기';
            button.className = 'primary-button';
            button.onclick = linkThreadAccount;
            
            alert('Thread 계정 연동이 해제되었습니다.');
        } else {
            alert(data.error || 'Thread 계정 연동 해제에 실패했습니다.');
        }
    } catch (error) {
        console.error('Thread account unlinking failed:', error);
        alert('Thread 계정 연동 해제 중 오류가 발생했습니다.');
    }
}

function changePassword() {
    // 비밀번호 변경 로직
    alert('비밀번호 변경 기능은 현재 개발 중입니다.');
}

function manageLinkedAccounts() {
    // 연결된 계정 관리 로직
    alert('계정 관리 기능은 현재 개발 중입니다.');
}

function notificationSettings() {
    // 알림 설정 로직
    alert('알림 설정 기능은 현재 개발 중입니다.');
}

function privacySettings() {
    // 개인정보 설정 로직
    alert('개인정보 설정 기능은 현재 개발 중입니다.');
}

// DOM이 로드되면 Thread 연동 상태 확인 (이제 필요 없음)
// document.addEventListener('DOMContentLoaded', function() {
//     checkThreadConnection();
// }); 