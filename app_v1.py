from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for, flash
from flask_talisman import Talisman
from flask_sqlalchemy import SQLAlchemy
from flask import session
from SnapsAI import InstagramAPI, convert_post, RAGConverter, ThreadAPI
import os
from dotenv import load_dotenv
import logging
import hashlib
import hmac
import base64
import json
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import requests

load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = os.getenv('SECRET_KEY')

# Define a custom CSP that allows inline styles and scripts
csp = {
    'default-src': "'self'",
    'style-src': "'self' 'unsafe-inline' https://fonts.googleapis.com",
    'script-src': "'self' 'unsafe-inline' https://cdn.jsdelivr.net",
    'img-src': "'self' data: https://* http://*",
    'font-src': "'self' https://fonts.gstatic.com",
    'object-src': "'self' data:",
}


Talisman(app, force_https=True, content_security_policy=csp)



# Database configuration for MariaDB
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}?charset=utf8mb4"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# User model definition
class User(db.Model):
    __tablename__ = 'users'  # 테이블 이름을 명시적으로 지정ㅋㅋㅋㅋ
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    instagram_id = db.Column(db.String(120), unique=True, nullable=True)
    access_token = db.Column(db.String(200), nullable=True)
    thread_account_id = db.Column(db.String(120), nullable=True)
    thread_access_token = db.Column(db.String(500), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# InstagramAPI 인스턴스 생성 (전역 변수)
instagram_api = InstagramAPI()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/instagram-converter')
def instagram_converter():
    return render_template('instagram_converter.html')

@app.route('/content-conversion')
def content_conversion():
    return render_template('content_conversion.html')

@app.route('/content-management')
def content_management():
    return render_template('content_management.html')

@app.route('/statistics')
def statistics():
    return render_template('statistics.html')

@app.route('/my-page')
def my_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user = User.query.get(session['user_id'])
    if not user:
        session.pop('user_id', None)
        return redirect(url_for('login'))
        
    instagram_linked = bool(user.instagram_id and user.access_token)
    thread_linked = bool(user.thread_account_id and user.thread_access_token)
    
    return render_template('my_page.html', 
                         user=user, 
                         instagram_linked=instagram_linked,
                         thread_linked=thread_linked)

@app.route('/fetch_posts', methods=['POST'])
def fetch_posts():
    if 'user_id' not in session:
        return jsonify({"error": "Login required"}), 401
        
    user = User.query.get(session['user_id'])
    if not user or not user.access_token:
        return jsonify({"error": "Instagram authentication required"}), 401

    app.logger.debug("Fetching posts...")
    try:
        # 데이터베이스에 저장된 사용자의 액세스 토큰 사용
        instagram_api.set_access_token(user.access_token)
        media_items = instagram_api.get_user_media()
        app.logger.debug(f"Media items fetched: {media_items}")
        formatted_posts = instagram_api.format_posts(media_items)
        app.logger.debug(f"Formatted posts: {formatted_posts}")
        return jsonify({"posts": formatted_posts})
    except Exception as e:
        app.logger.error(f"Error fetching posts: {str(e)}")
        return jsonify({"error": str(e)}), 400

@app.route('/convert', methods=['POST'])
def convert():
    try:
        data = request.json
        app.logger.info(f"Received data: {data}")
        if not data:
            return jsonify({"error": "No JSON data received"}), 400

        caption = data.get('caption')
        target_platform = data.get('targetPlatform', 'Instagram')
        has_image = data.get('hasImage', False)

        if not caption:
            return jsonify({"error": "Missing caption"}), 400

        # RAG 변환
        rag_converter = RAGConverter()
        converted_post = rag_converter.generate_enhanced_post(
            original_post=caption,
            target_platform=target_platform,
            has_image=has_image
        )
        
        return jsonify({
            "success": True,
            "ragConvertedPost": converted_post
        })

    except Exception as e:
        app.logger.error(f"Error in /convert route: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/fetch_instagram_stats', methods=['GET'])
def fetch_instagram_stats():
    if 'instagram_access_token' not in session:
        return jsonify({"error": "Instagram authentication required"}), 401
        
    try:
        # 세션의 액세스 토큰으로 API 인스턴스 업데이트
        instagram_api.set_access_token(session['instagram_access_token'])
        stats = instagram_api.get_user_statistics(limit=30)  # 최근 30개 게시물 기준
        return jsonify(stats)
    except Exception as e:
        app.logger.error(f"Error fetching Instagram stats: {str(e)}")
        return jsonify({"error": "통계를 가져오는 데 실패했습니다. 잠시 후 다시 시도해주세요."}), 500

@app.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy_policy.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    app.logger.error(f"Internal Server Error: {str(e)}")
    return render_template('500.html'), 500

@app.route('/auth/instagram')
def instagram_auth():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': '로그인이 필요합니다.'})
    
    try:
        user = db.session.get(User, session['user_id'])
        if not user:
            return jsonify({'success': False, 'error': '사용자를 찾을 수 없습니다.'})
        
        # 이미 다른 사용자가 해당 instagram_id를 사용하고 있는지 확인
        existing_user = User.query.filter_by(instagram_id=os.getenv('USER_ID')).first()
        if existing_user:
            # 이미 연동된 계정이 있다면 해당 연동을 해제
            existing_user.instagram_id = None
            existing_user.access_token = None
            db.session.commit()
        
        # 현재 사용자에게 instagram 정보 설정
        instagram_id = os.getenv('USER_ID')
        access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN')
        
        user.instagram_id = instagram_id
        user.access_token = access_token
        db.session.commit()
        
        # 세션에도 저장
        session['instagram_access_token'] = access_token
        session['instagram_user_id'] = instagram_id
        
        return jsonify({
            'success': True,
            'message': 'Instagram 계정이 성공적으로 연동되었습니다.'
        })
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Instagram auth error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Instagram 연동 중 오류가 발생했습니다.'
        })

# Instagram OAuth 콜백 (프로덕션 환경용)
@app.route('/auth/instagram/callback')
def instagram_callback():
    """Instagram OAuth 콜백 처리"""
    if os.getenv('PRODUCTION') != 'True':
        return redirect(url_for('my_page'))
        
    error = request.args.get('error')
    if error:
        return f"Authentication failed: {error}"

    code = request.args.get('code')
    if not code:
        return "No code provided"

    try:
        instagram_api = InstagramAPI()
        auth_data = instagram_api.authenticate(code)
        
        # 사용자 정보를 세션에 저장
        session['instagram_access_token'] = auth_data['access_token']
        session['instagram_user_id'] = auth_data['user_id']
        
        # DB에도 저장
        if 'user_id' in session:
            user = User.query.get(session['user_id'])
            if user:
                user.instagram_id = auth_data['user_id']
                user.access_token = auth_data['access_token']
                db.session.commit()
        
        return redirect(url_for('my_page'))
    except Exception as e:
        app.logger.error(f"Instagram callback error: {str(e)}")
        return f"Authentication failed: {str(e)}"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session.permanent = remember  # 로그인 상태 유지 설정
            return redirect(url_for('my_page'))
        else:
            return render_template('login.html', error='이메일 또는 비밀번호가 올바르지 않습니다.')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            return render_template('register.html', error='비밀번호가 일치하지 않습니다.')
        
        if User.query.filter_by(email=email).first():
            return render_template('register.html', error='이미 등록된 이메일입니다.')
            
        try:
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            # 회원가입 성공 후 로그인 페이지로 리다이렉트
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Registration error: {str(e)}")
            return render_template('register.html', error='회원가입 중 오류가 발생했습니다.')

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

# Thread 계정 관련 라우트 추가
@app.route('/check_thread_account')
def check_thread_account():
    if 'user_id' not in session:
        return jsonify({'linked': False, 'error': '로그인이 필요합니다.'})
    
    try:
        user = User.query.get(session['user_id'])
        if not user:
            return jsonify({'linked': False, 'error': '사용자를 찾을 수 없습니다.'})
        
        # Thread 계정 연동 여부 확인
        # 실제로는 User 모델에 thread_account_id 필드가 필요합니다
        return jsonify({
            'linked': bool(user.thread_account_id) if hasattr(user, 'thread_account_id') else False
        })
    except Exception as e:
        app.logger.error(f"Thread account check error: {str(e)}")
        return jsonify({'linked': False, 'error': str(e)}), 500

@app.route('/link_thread_account', methods=['POST'])
def link_thread_account():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': '로그인이 필요합니다.'})
    
    try:
        data = request.json
        thread_user_id = data.get('thread_user_id')
        
        if not thread_user_id:
            return jsonify({'success': False, 'error': 'Thread 사용자 ID가 필요합니다.'})
        
        user = User.query.get(session['user_id'])
        if not user:
            return jsonify({'success': False, 'error': '사용자를 찾을 수 없습니다.'})
        
        # Thread 계정 정보 저장 (.env 파일의 access token 사용)
        user.thread_account_id = thread_user_id
        user.thread_access_token = os.getenv('THREAD_ACCESS_TOKEN')  # 환경 변수에서 가져옴
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Thread account linking error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/unlink_thread_account', methods=['POST'])
def unlink_thread_account():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': '로그인이 필요합니다.'})
    
    try:
        user = User.query.get(session['user_id'])
        if not user:
            return jsonify({'success': False, 'error': '사용자를 찾을 수 없습니다.'})
        
        # Thread 계정 연동 해제
        user.thread_account_id = None
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Thread account unlinking error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/convert_all', methods=['POST'])
def convert_all():
    try:
        data = request.json
        app.logger.info(f"Received data for conversion: {data}")
        
        caption = data.get('caption')
        platforms = data.get('platforms', [])

        if not caption or not platforms:
            return jsonify({"error": "Caption and platforms are required"}), 400

        rag_converter = RAGConverter()
        conversions = {}
        
        # 각 플랫폼별로 개별 변환 수행
        for platform in platforms:
            try:
                app.logger.info(f"Converting for platform: {platform}")
                # 플랫폼별 독립적인 변환 수행
                converted = rag_converter.generate_enhanced_post(
                    original_post=caption,
                    target_platform=platform,
                    has_image=True
                )
                app.logger.info(f"Conversion result for {platform}: {converted}")
                
                # 변환 결과 저장
                conversions[platform] = converted
                
                # 메모리 초기화하여 다른 플랫폼 변환에 영향을 주지 않도록 함
                rag_converter.clear_memory()
                
            except Exception as e:
                app.logger.error(f"Error converting for {platform}: {str(e)}")
                conversions[platform] = f"변환 실패: {str(e)}"

        return jsonify({
            "success": True,
            "conversions": conversions
        })
    except Exception as e:
        app.logger.error(f"Conversion error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# 데이터베이스 초기화 함수
def init_db():
    with app.app_context():
        # 테이블이 없을 때만 생성
        db.create_all()
        app.logger.info('Database tables created successfully')

@app.route('/upload_to_thread', methods=['POST'])
def upload_to_thread():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': '로그인이 필요합니다.'}), 401
    
    try:
        user = User.query.get(session['user_id'])
        if not user or not user.thread_account_id or not user.thread_access_token:
            return jsonify({'success': False, 'error': 'Thread 계정이 연동되어 있지 않습니다.'}), 401

        data = request.json
        content = data.get('content')
        media_type = data.get('media_type', 'TEXT')

        if not content:
            return jsonify({'success': False, 'error': '내용이 필요합니다.'}), 400

        thread_api = ThreadAPI()
        thread_api.access_token = user.thread_access_token
        
        # 디버그 로깅 추가
        app.logger.debug(f"Attempting to post to Thread with user_id: {user.thread_account_id}")
        app.logger.debug(f"Content: {content}")
        
        result = thread_api.post_thread(
            user_id=user.thread_account_id,
            content=content,
            media_type=media_type
        )
        
        app.logger.debug(f"Thread post result: {result}")
        
        return jsonify({
            'success': True,
            'thread_id': result.get('id')
        })

    except Exception as e:
        app.logger.error(f"Thread upload error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

# Thread 인증 관련 라우트 추가
@app.route('/auth/thread')
def thread_auth():
    """Thread OAuth 인증"""
    client_id = os.getenv('THREADS_APP_ID')
    redirect_uri = os.getenv('THREADS_REDIRECT_URI')
    scope = 'threads_basic,threads_content_publish'  # 필요한 권한
    
    auth_url = (
        f"https://threads.net/oauth/authorize"
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&scope={scope}"
        f"&response_type=code"
    )
    
    return redirect(auth_url)

@app.route('/auth/thread/callback')
def thread_callback():
    """Thread OAuth 콜백 처리"""
    error = request.args.get('error')
    if error:
        app.logger.error(f"Thread auth error: {error}")
        return redirect(url_for('my_page'))

    code = request.args.get('code')
    if not code:
        return "No code provided"

    try:
        # 액세스 토큰 교환
        token_url = "https://graph.threads.net/oauth/access_token"
        token_data = {
            'client_id': os.getenv('THREADS_APP_ID'),
            'client_secret': os.getenv('THREADS_APP_SECRET'),
            'grant_type': 'authorization_code',
            'redirect_uri': os.getenv('THREADS_REDIRECT_URI'),
            'code': code
        }
        
        response = requests.post(token_url, data=token_data)
        token_info = response.json()
        
        if 'error' in token_info:
            raise Exception(token_info.get('error_message', 'Failed to get access token'))
        
        # 사용자 정보 저장
        if 'user_id' in session:
            user = User.query.get(session['user_id'])
            if user:
                user.thread_account_id = token_info['user_id']
                user.thread_access_token = token_info['access_token']  # 새로운 필드 필요
                db.session.commit()
        
        return redirect(url_for('my_page'))
        
    except Exception as e:
        app.logger.error(f"Thread callback error: {str(e)}")
        return f"Authentication failed: {str(e)}"

@app.route('/thread_statistics')
def thread_statistics():
    if 'user_id' not in session:
        return jsonify({'error': '로그인이 필요합니다.'}), 401
    
    try:
        user = User.query.get(session['user_id'])
        if not user or not user.thread_account_id:
            return jsonify({'error': 'Thread 계정이 연동되어 있지 않습니다.'}), 401

        # Thread API를 통해 통계 데이터 가져오기
        thread_api = ThreadAPI()
        thread_api.access_token = user.thread_access_token
        
        stats = thread_api.get_user_insights(user.thread_account_id)
        return jsonify(stats)
    except Exception as e:
        app.logger.error(f"Thread statistics error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/fetch_thread_posts')
def fetch_thread_posts():
    if 'user_id' not in session:
        return jsonify({'error': '로그인이 필요합니다.'}), 401
    
    try:
        user = User.query.get(session['user_id'])
        if not user or not user.thread_account_id:
            return jsonify({'error': 'Thread 계정이 연동되어 있지 않습니다.'}), 401

        thread_api = ThreadAPI()
        thread_api.access_token = user.thread_access_token
        
        # Thread 게시물 조회
        posts = thread_api.get_user_media(user.thread_account_id)
        
        # 각 게시물의 인사이트 조회
        for post in posts.get('data', []):
            insights = thread_api.get_media_insights(post['id'])
            post['likes'] = next((metric['values'][0]['value'] for metric in insights['data'] 
                                if metric['name'] == 'likes'), 0)
            post['replies'] = next((metric['values'][0]['value'] for metric in insights['data'] 
                                  if metric['name'] == 'replies'), 0)
            post['reposts'] = next((metric['values'][0]['value'] for metric in insights['data'] 
                                  if metric['name'] == 'reposts'), 0)
        
        # 전체 통계 조회
        stats = thread_api.get_user_insights(user.thread_account_id)
        
        return jsonify({
            'posts': posts.get('data', []),
            'stats': stats
        })
        
    except Exception as e:
        app.logger.error(f"Thread posts fetch error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/test-db')
def test_db():
    try:
        # 데이터베이스 연결 테스트
        users = User.query.all()
        return jsonify({
            'success': True,
            'user_count': len(users),
            'users': [{
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'instagram_id': user.instagram_id
            } for user in users]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

# if __name__ == '__main__': 블록을 맨 아래로 이동
if __name__ == '__main__':
    init_db()  # 데이터베이스 초기화 추가
    
    BASE_URL = os.getenv('BASE_URL', 'http://localhost:5000')
    app.logger.info(f"Base URL: {BASE_URL}")
    app.logger.info(f"Callback URL: {BASE_URL}/auth/instagram/callback")
    app.logger.info(f"Data Deletion URL: {BASE_URL}/data-deletion")
    app.logger.info(f"Privacy Policy URL: {BASE_URL}/privacy-policy")

    # 세션 설정 추가
    app.permanent_session_lifetime = timedelta(days=30)  # 세션 지 기간 설

    app.run(host='0.0.0.0', port=5000, debug=True)

