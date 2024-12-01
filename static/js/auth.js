function showLoading() {
    const loadingElement = document.querySelector('.loading');
    if (loadingElement) {
        loadingElement.style.display = 'flex';
    }
}

function hideLoading() {
    const loadingElement = document.querySelector('.loading');
    if (loadingElement) {
        loadingElement.style.display = 'none';
    }
}

function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function loginWithGoogle() {
    alert('Google 로그인 기능은 현재 개발 중입니다.');
}

function loginWithInstagram() {
    window.location.href = '/auth/instagram';
}

function showError(elementId, message) {
    const errorElement = document.getElementById(elementId);
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.style.display = 'block';
    }
}

function clearErrors() {
    const errors = document.querySelectorAll('.error');
    errors.forEach(error => error.style.display = 'none');
}

async function handleLogin(event) {
    event.preventDefault();
    clearErrors();
    showLoading();

    const email = document.getElementById('email')?.value;
    const password = document.getElementById('password')?.value;
    const remember = document.getElementById('remember')?.checked || false;

    if (!email || !password) {
        hideLoading();
        showError('emailError', '이메일과 비밀번호를 입력해주세요.');
        return false;
    }

    try {
        const response = await fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                email: email,
                password: password,
                remember: remember
            })
        });

        if (response.redirected) {
            window.location.href = response.url;
            return false;
        }

        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            const data = await response.json();
            if (data.error) {
                showError('emailError', data.error);
            }
        } else {
            const text = await response.text();
            if (response.ok) {
                window.location.href = '/my-page';
            } else {
                showError('emailError', '이메일 또는 비밀번호가 올바르지 않습니다.');
            }
        }
    } catch (error) {
        console.error('Login error:', error);
        showError('emailError', '로그인 중 오류가 발생했습니다.');
    } finally {
        hideLoading();
    }

    return false;
}

async function handleRegister(event) {
    event.preventDefault();
    clearErrors();
    showLoading();

    const username = document.getElementById('username')?.value;
    const email = document.getElementById('email')?.value;
    const password = document.getElementById('password')?.value;
    const confirmPassword = document.getElementById('confirm_password')?.value;
    const terms = document.getElementById('terms')?.checked;

    if (!username || !email || !password || !confirmPassword) {
        hideLoading();
        showError('emailError', '모든 필드를 입력해주세요.');
        return false;
    }

    if (!terms) {
        hideLoading();
        showError('emailError', '이용약관에 동의해주세요.');
        return false;
    }

    try {
        const response = await fetch('/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                username: username,
                email: email,
                password: password,
                confirm_password: confirmPassword
            })
        });

        if (response.redirected) {
            window.location.href = response.url;
            return false;
        }

        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            const data = await response.json();
            if (data.error) {
                showError('emailError', data.error);
            } else {
                window.location.href = '/login';
            }
        } else {
            const text = await response.text();
            if (response.ok) {
                window.location.href = '/login';
            } else {
                showError('emailError', '회원가입 중 오류가 발생했습니다.');
            }
        }
    } catch (error) {
        console.error('Register error:', error);
        showError('emailError', '회원가입 중 오류가 발생했습니다.');
    } finally {
        hideLoading();
    }

    return false;
}

// 비밀번호 강도 체크 기능
function checkPasswordStrength(password) {
    const strengthMeter = document.getElementById('strengthMeter');
    if (!strengthMeter) return;

    let strength = 0;
    if (password.length >= 8) strength++;
    if (password.match(/[a-z]/)) strength++;
    if (password.match(/[A-Z]/)) strength++;
    if (password.match(/[0-9]/)) strength++;
    if (password.match(/[^a-zA-Z0-9]/)) strength++;

    strengthMeter.style.width = `${(strength / 5) * 100}%`;
    strengthMeter.className = '';
    if (strength < 2) strengthMeter.classList.add('weak');
    else if (strength < 4) strengthMeter.classList.add('medium');
    else strengthMeter.classList.add('strong');
}

// 비밀번호 입력 필드에 이벤트 리스너 추가
document.addEventListener('DOMContentLoaded', function() {
    const passwordInput = document.getElementById('password');
    if (passwordInput) {
        passwordInput.addEventListener('input', (e) => checkPasswordStrength(e.target.value));
    }
}); 