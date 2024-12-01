import requests
from typing import List, Dict, Any
import random
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.chains import RetrievalQA
from langchain.schema import Document
from typing import List, Dict, Any, Optional
import os
import time
from datetime import datetime, timedelta
from requests.exceptions import RequestException
import logging
from bson.objectid import ObjectId
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader, DirectoryLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler


load_dotenv()
logger = logging.getLogger(__name__)

class InstagramAPI:
    BASE_URL = "https://graph.instagram.com/v12.0"

    def __init__(self, access_token=None):
        self.access_token = access_token

    def set_access_token(self, access_token):
        """액세스 토큰을 설정하는 메서드"""
        self.access_token = access_token

    def get_user_media(self, limit: int = 10) -> List[Dict[str, Any]]:
        """사용자의 Instagram 미디어를 가져옵니다."""
        if not self.access_token:
            raise ValueError("Access token is not set")
            
        endpoint = f"{self.BASE_URL}/me/media"
        params = {
            "fields": "id,caption,media_type,media_url,thumbnail_url,permalink,timestamp",
            "access_token": self.access_token,
            "limit": limit
        }
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            return response.json().get("data", [])
        except requests.RequestException as e:
            print(f"Error fetching user media: {str(e)}")
            return []

    def format_posts(self, media_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """API 응답을 보기 좋게 포맷팅합니다."""
        formatted_posts = []
        for item in media_items:
            formatted_post = {
                "id": item.get("id"),
                "media_url": item.get("media_url") or item.get("thumbnail_url"),
                "caption": item.get("caption", "No caption"),
                "media_type": item.get("media_type"),
                "permalink": item.get("permalink"),
                "timestamp": item.get("timestamp")
            }
            formatted_posts.append(formatted_post)
        return formatted_posts

    def authenticate(self, code: str) -> Dict[str, str]:
        """Instagram OAuth 인증 코드로 액세스 토큰을 획득합니다."""
        token_url = "https://api.instagram.com/oauth/access_token"
        data = {
            "client_id": os.getenv("INSTAGRAM_CLIENT_ID"),
            "client_secret": os.getenv("INSTAGRAM_CLIENT_SECRET"),
            "grant_type": "authorization_code",
            "redirect_uri": os.getenv("INSTAGRAM_REDIRECT_URI"),
            "code": code
        }
        
        try:
            response = requests.post(token_url, data=data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Failed to authenticate: {str(e)}")

class ThreadAPI:
    def __init__(self):
        self.base_url = "https://graph.threads.net/v1.0"
        self.access_token = None

    def get_user_media(self, user_id):
        """사용자의 모든 Thread 게시물 조회"""
        try:
            endpoint = f"{self.base_url}/{user_id}/threads"
            params = {
                'fields': 'id,media_product_type,media_type,media_url,permalink,username,text,timestamp,shortcode,thumbnail_url,children,is_quote_post',
                'access_token': self.access_token
            }
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()

            # 각 게시물의 미디어 정보 처리
            posts = data.get('data', [])
            for post in posts:
                if post.get('media_type') in ['IMAGE', 'VIDEO', 'CAROUSEL_ALBUM']:
                    # 비디오인 경우 썸네일 URL 추가
                    if post.get('media_type') == 'VIDEO' and post.get('thumbnail_url'):
                        post['media_preview'] = post['thumbnail_url']
                    
                    # 캐러셀인 경우 모든 미디어 URL 수집
                    if post.get('media_type') == 'CAROUSEL_ALBUM' and post.get('children'):
                        post['carousel_media'] = [child.get('media_url') for child in post['children']['data']]

            return data
        except Exception as e:
            logger.error(f"Error fetching Thread media: {str(e)}")
            return {'data': []}

    def get_media_insights(self, media_id):
        """특정 Thread 게시물의 인사이트 조회"""
        endpoint = f"{self.base_url}/{media_id}/insights"
        params = {
            'metric': 'views,likes,replies,reposts,quotes,shares',
            'access_token': self.access_token
        }
        response = requests.get(endpoint, params=params)
        return response.json()

    def get_user_insights(self, user_id):
        """사용자의 Thread 계정 인사이트 조회"""
        try:
            endpoint = f"{self.base_url}/{user_id}/threads_insights"
            params = {
                'metric': 'views,likes,replies,reposts,quotes,followers_count',
                'period': 'day',  # 일별 데이터 요청
                'access_token': self.access_token
            }
            response = requests.get(endpoint, params=params)
            response_data = response.json()
            
            # 기본 통계 데이터 구조 초기화
            stats = {
                'total_posts': 0,
                'total_likes': 0,
                'total_replies': 0,
                'avg_likes': 0,
                'avg_replies': 0,
                'dates': [],
                'likes_data': [],
                'replies_data': []
            }

            # 게시물 수 조회
            posts_response = self.get_user_media(user_id)
            stats['total_posts'] = len(posts_response.get('data', []))

            # 최근 30일 데이터 생성
            current_date = datetime.now()
            for i in range(30):
                date = (current_date - timedelta(days=i)).strftime('%Y-%m-%d')
                stats['dates'].insert(0, date)
                stats['likes_data'].insert(0, random.randint(10, 100))  # 임시 데이터
                stats['replies_data'].insert(0, random.randint(5, 50))  # 임시 데이터

            # 총계 및 평균 계산
            stats['total_likes'] = sum(stats['likes_data'])
            stats['total_replies'] = sum(stats['replies_data'])
            stats['avg_likes'] = round(stats['total_likes'] / len(stats['likes_data']))
            stats['avg_replies'] = round(stats['total_replies'] / len(stats['replies_data']))

            return stats
        except Exception as e:
            logger.error(f"Error fetching Thread insights: {str(e)}")
            return {
                'total_posts': 0,
                'total_likes': 0,
                'total_replies': 0,
                'avg_likes': 0,
                'avg_replies': 0,
                'dates': [],
                'likes_data': [],
                'replies_data': []
            }

    def post_thread(self, user_id, content, media_type='TEXT', media_url=None):
        """Thread 게시물 작성"""
        endpoint = f"{self.base_url}/{user_id}/threads"
        data = {
            'text': content,
            'media_type': media_type,
            'access_token': self.access_token
        }
        
        if media_url:
            data['media_url'] = media_url
            
        response = requests.post(endpoint, json=data)
        return response.json()

def convert_post(caption: str, target_platform: str, has_image: bool) -> str:
    converted_post = caption

    if target_platform == "Twitter":
        converted_post = f"Check out my latest Instagram post! 📸\n\n{caption[:200]}..." if len(caption) > 200 else caption
        converted_post += "\n\n#Instagram #Social"
    elif target_platform == "LinkedIn":
        converted_post = f"I just shared a new post on Instagram! Here's a sneak peek:\n\n{caption}\n\nFollow me on Instagram for more updates!"
        converted_post += "\n\n#SocialMedia #Professional #Instagram"
    elif target_platform == "Facebook":
        converted_post = f"New Instagram Post Alert! 🚨\n\n{caption}\n\nHead over to my Instagram profile to see the full post and more content!"
    elif target_platform == "Thread":
        converted_post = f"Continuing from my recent Instagram post...\n\n{caption[:100]}...\n\nThoughts?"
    elif target_platform == "YouTube Community":
        converted_post = f"📸 Instagram Update 📸\n\n{caption[:150]}...\n\nCheck out my Instagram for the full post and more behind-the-scenes content!"

    if has_image:
        converted_post += "\n\n[Image from Instagram]"

    return converted_post

class RAGConverter:
    def __init__(self):
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in .env file")
        
        self.llm = ChatOpenAI(
            temperature=0.7,
            model_name="gpt-4o-mini",
            openai_api_key=openai_api_key,
            streaming=True,
            callbacks=[StreamingStdOutCallbackHandler()]
        )
        
        # 임베딩 모델 초기화 (ada-002 명시적 지정)
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=openai_api_key,
            model="text-embedding-ada-002"
        )
        
        # 개선된 텍스트 분할 전략
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,  # 청크 크기 조정
            chunk_overlap=50,
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", " ", ""]
        )
        
        # 메모리 초기화 (대화 이력 유지)
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )
        
        # 벡터 DB 초기화
        self.vector_store = self._initialize_vector_store()
        
        if self.vector_store:
            # 프롬프트 템플릿 정의
            self.qa_prompt = PromptTemplate(
                template="""당신은 소셜 미디어 마케팅 전문가입니다.
                
                주어진 컨텍스트를 기반으로 다음 콘텐츠를 변환해주세요:
                
                컨텍스트:
                {context}
                
                플랫폼: {platform}
                원본 콘텐츠: {question}
                이미지 포함 여부: {has_image}
                
                각 플랫폼의 특성을 고려하여 최적화된 콘텐츠를 생성해주세요.
                이전 대화 기록: {chat_history}
                """,
                input_variables=["context", "platform", "question", "has_image", "chat_history"]
            )
            
            # ConversationalRetrievalChain 설정
            self.qa_chain = ConversationalRetrievalChain.from_llm(
                llm=self.llm,
                retriever=self.vector_store.as_retriever(
                    search_type="mmr",
                    search_kwargs={
                        "k": 3,
                        "fetch_k": 5,
                        "lambda_mult": 0.7
                    }
                ),
                memory=self.memory,
                combine_docs_chain_kwargs={
                    "prompt": PromptTemplate(
                        template="""당신은 소셜 미디어 마케팅 전문가입니다.
                        
                        다음 문서들을 참고하여 주어진 콘텐츠를 변환해주세요:
                        
                        {context}
                        
                        질문: {question}
                        
                        각 플랫폼의 특성을 고려하여 최적화된 콘텐츠를 생성해주세요.
                        이전 대화 기록: {chat_history}
                        """,
                        input_variables=["context", "question", "chat_history"]
                    )
                },
                return_source_documents=True,
                verbose=True
            )

    def _initialize_vector_store(self):
        """벡터 저장소 초기화 및 문서 로드"""
        try:
            pdf_path = "./data/pdf"
            if not os.path.exists(pdf_path):
                os.makedirs(pdf_path)
                logger.info(f"Created directory: {pdf_path}")
            
            documents = []
            
            # PDF 파일 로드
            if os.path.exists(pdf_path):
                loader = DirectoryLoader(
                    pdf_path,
                    glob="**/*.pdf",
                    loader_cls=PyPDFLoader
                )
                pdf_documents = loader.load()
                documents.extend(pdf_documents)
                logger.info(f"Loaded {len(pdf_documents)} PDF documents")
            
            # 기본 마케팅 가이드 문서 추가
            marketing_docs = self._get_default_marketing_docs()
            documents.extend(marketing_docs)
            logger.info("Added default marketing documents")
            
            if not documents:
                logger.warning("No documents loaded")
                return None
            
            # 문서 분할
            texts = self.text_splitter.split_documents(documents)
            logger.info(f"Split documents into {len(texts)} chunks")
            
            # 벡터 저장소 생성
            store = Chroma.from_documents(
                documents=texts,
                embedding=self.embeddings,
                persist_directory="./data/vector_store"
            )
            store.persist()  # 벡터 저장소 영구 저장
            logger.info("Vector store initialized and persisted")
            
            return store
            
        except Exception as e:
            logger.error(f"Vector store initialization failed: {str(e)}")
            return None

    def _get_default_marketing_docs(self) -> List[Document]:
        """기본 마케팅 가이드 문서 생성"""
        return [
            Document(
                page_content="""
                Instagram 마케팅 가이드:
                - 감성적이고 시각적인 표현 사용
                - 해시태그는 5-10개가 적당
                - 이모지로 포인트 추가
                - 짧은 단락으로 구성
                """,
                metadata={"source": "default_guide", "platform": "instagram"}
            ),
            Document(
                page_content="""
                Facebook 마케팅 가이드:
                - 상세하고 친근한 톤 유지
                - 스토리텔링 방식으로 서술
                - 이모지 적절히 활용
                - 독자와의 상호작용 유도
                """,
                metadata={"source": "default_guide", "platform": "facebook"}
            ),
            Document(
                page_content="""
                Thread 마케팅 가이드:
                - 간결하면서도 대화를 유도하는 톤
                - 위트있 표현 사용
                - 해시태그 2-3개만 사용
                - 대화형 마무리
                """,
                metadata={"source": "default_guide", "platform": "thread"}
            )
        ]

    def generate_enhanced_post(self, original_post: str, target_platform: str, has_image: bool) -> str:
        try:
            if not self.vector_store:
                logger.warning("Vector store not initialized, falling back to basic conversion")
                return convert_post(original_post, target_platform, has_image)

            # 플랫폼별 프롬프트 템플릿 설정
            platform_prompts = {
                "Instagram": """
                    다음 콘텐츠를 Instagram 형식으로 변환해주세요:
                    - 감성적이고 시각적인 표현 사용
                    - 해시태그 5-10개 포함
                    - 이모지 자연스럽게 사용
                    - 짧은 단락으로 구성
                    
                    원본: {original_post}
                    """,
                "Facebook": """
                    다음 콘텐츠를 Facebook 형식으로 변환해주세요:
                    - 상세하고 친근한 톤 사용
                    - 스토리텔링 방식으로 서술
                    - 이모지 적절히 활용
                    - 독자와의 상호작용 유도
                    
                    원본: {original_post}
                    """,
                "Thread": """
                    다음 콘텐츠를 Thread 형식으로 변환해주세요:
                    - 간결하면서도 대화를 유도하는 톤
                    - 위트있는 표현 사용
                    - 해시태그 2-3개만 사용
                    - 대화형 마무리
                    
                    원본: {original_post}
                    """,
                "Blog": """
                    다음 콘텐츠를 블로그 형식으로 변환해주세요:
                    - 정보성 콘텐츠 강화
                    - 명확한 단락 구분
                    - 키워드 강조
                    - SEO를 위한 태그 활용
                    
                    원본: {original_post}
                    """
            }

            # 해당 플랫폼의 프롬프트 가져오기
            prompt_template = platform_prompts.get(target_platform)
            if not prompt_template:
                logger.warning(f"Unknown platform: {target_platform}")
                return convert_post(original_post, target_platform, has_image)

            # RAG 체인을 통한 응답 생성
            response = self.qa_chain({
                "question": prompt_template.format(original_post=original_post)
            })

            if not response or not response.get("answer"):
                logger.warning("No response from RAG chain")
                return convert_post(original_post, target_platform, has_image)

            # 응답에서 불필요한 텍스트 제거
            answer = response["answer"].strip()
            
            # 메타 텍스트 제거
            answer = self._clean_response(answer, target_platform)
            
            return answer

        except Exception as e:
            logger.error(f"Post generation failed: {str(e)}")
            return convert_post(original_post, target_platform, has_image)

    def _clean_response(self, response: str, platform: str) -> str:
        """응답에서 불필요한 메타 텍스트 제거"""
        # 제거할 프리픽스 패턴들
        prefixes_to_remove = [
            f"{platform} 마케팅 가이드에 맞춘 콘텐츠:",
            f"{platform} 콘텐츠 변환",
            f"{platform} 형식으로 변환된 콘텐츠:",
            "변환된 콘텐츠:",
            "###",
            "---"
        ]
        
        # 제거할 서픽스 패턴들
        suffixes_to_remove = [
            "이렇게 변환된 내용은",
            "이렇게 감성적이고",
            "---",
            "###"
        ]
        
        result = response
        
        # 프리픽스 제거
        for prefix in prefixes_to_remove:
            if result.startswith(prefix):
                result = result[len(prefix):].strip()
        
        # 서픽스 제거
        for suffix in suffixes_to_remove:
            if result.endswith(suffix):
                result = result[:-len(suffix)].strip()
        
        # 여러 줄의 공백을 하나의 줄바꿈으로 변경
        result = '\n'.join(line.strip() for line in result.splitlines() if line.strip())
        
        return result

    def add_pdf_document(self, pdf_path: str) -> bool:
        """새로운 PDF 문서를 벡터 저장소에 추가"""
        try:
            if not os.path.exists(pdf_path):
                logger.error(f"PDF file not found: {pdf_path}")
                return False
                
            loader = PyPDFLoader(pdf_path)
            pages = loader.load()
            texts = self.text_splitter.split_documents(pages)
            
            if not texts:
                logger.warning(f"No text extracted from PDF: {pdf_path}")
                return False
            
            if self.vector_store:
                self.vector_store.add_documents(texts)
                self.vector_store.persist()  # 변경사항 저장
                logger.info(f"Successfully added PDF document: {pdf_path}")
                return True
                
            logger.error("Vector store not initialized")
            return False
            
        except Exception as e:
            logger.error(f"Failed to add PDF document: {str(e)}")
            return False

    def clear_memory(self):
        """대화 기록 초기화"""
        try:
            self.memory.clear()
            logger.info("Conversation memory cleared")
        except Exception as e:
            logger.error(f"Failed to clear memory: {str(e)}")

def main():
    try:
        # Initialize Instagram API
        instagram_api = InstagramAPI()

        # Fetch recent Instagram posts
        media_items = instagram_api.get_user_media(limit=5)
        formatted_posts = instagram_api.format_posts(media_items)

        print(f"Total posts fetched: {len(formatted_posts)}")
        for i, post in enumerate(formatted_posts, 1):
            print(f"\nPost {i}:")
            print(f"ID: {post['id']}")
            print(f"Type: {post['media_type']}")
            print(f"Caption: {post['caption'][:50]}..." if len(post['caption']) > 50 else f"Caption: {post['caption']}")
            print(f"Media URLs: {', '.join(post['media_urls'])}")
            print(f"Permalink: {post['permalink']}")
            print(f"Timestamp: {post['timestamp']}")

        # Instagram 통계 가져오기
        instagram_stats = instagram_api.get_user_statistics()
        print("\nInstagram Statistics:")
        print(f"Total Posts: {instagram_stats['total_posts']}")
        print(f"Post Types: {instagram_stats['post_types']}")
        print("Popular Hashtags:")
        for tag, count in instagram_stats['popular_hashtags']:
            print(f"  #{tag}: {count}")
        print("Peak Posting Hours:")
        for hour, count in instagram_stats['peak_posting_hours']:
            print(f"  {hour}:00 - {count} posts")

    except Exception as e:
        print(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    main()