import os
from dotenv import load_dotenv
import requests
from typing import Dict, Any, List

def load_env_variables():
    # 현재 작업 디렉토리에서 .env 파일 찾기
    env_path = os.path.join(os.getcwd(), '.env')
    
    # .env 파일 존재 여부 확인
    if os.path.exists(env_path):
        print(f".env 파일을 찾았습니다: {env_path}")
        # .env 파일 로드
        load_dotenv(env_path)
    else:
        print(".env 파일을 찾을 수 없습니다.")

    # 환경 변수 읽기
    access_token = os.getenv('THREAD_ACCESS_TOKEN')
    user_id = os.getenv('THREAD_USER_ID')

    # 환경 변수 확인
    print(f"THREAD_ACCESS_TOKEN: {'설정됨' if access_token else '설정되지 않음'}")
    print(f"THREAD_USER_ID: {user_id if user_id else '설정되지 않음'}")

    return access_token, user_id

class ThreadAPI:
    BASE_URL = "https://graph.threads.net/v1.0"

    def __init__(self, access_token: str, user_id: str):
        self.access_token = access_token
        self.user_id = user_id

    def _make_request(self, method: str, endpoint: str, params: Dict[str, Any] = None, data: Dict[str, Any] = None) -> Dict[str, Any]:
        url = f"{self.BASE_URL}/{endpoint}"
        params = params or {}
        params['access_token'] = self.access_token

        print(f"Making request to: {url}")
        print(f"With params: {params}")
        print(f"With data: {data}")

        try:
            response = requests.request(method, url, params=params, json=data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"API request failed: {e}")
            if response.text:
                print(f"Response content: {response.text}")
            raise

    def post_thread(self, content: str, media_type: str = "TEXT") -> Dict[str, Any]:
        creation_params = {
            "media_type": media_type,
            "text": content
        }

        creation_data = self._make_request("POST", f"{self.user_id}/threads", data=creation_params)
        
        if "id" not in creation_data:
            raise Exception(f"Failed to create media container: {creation_data}")

        creation_id = creation_data["id"]

        publish_data = self._make_request("POST", f"{self.user_id}/threads_publish", data={"creation_id": creation_id})

        if "id" not in publish_data:
            raise Exception(f"Failed to publish thread: {publish_data}")

        return publish_data

    def get_user_threads(self, limit: int = 10) -> List[Dict[str, Any]]:
        params = {
            "fields": "id,text,timestamp",
            "limit": limit
        }
        response = self._make_request("GET", f"{self.user_id}/threads", params=params)
        return response.get("data", [])

    def get_thread(self, thread_id: str) -> Dict[str, Any]:
        params = {
            "fields": "id,text,timestamp"
        }
        return self._make_request("GET", thread_id, params=params)

    def get_thread_insights(self, thread_id: str) -> Dict[str, Any]:
        params = {
            "metric": "views,likes,replies,reposts,quotes"
        }
        return self._make_request("GET", f"{thread_id}/insights", params=params)

    def get_user_insights(self) -> Dict[str, Any]:
        params = {
            "metric": "views,likes,replies,reposts,quotes,followers_count"
        }
        return self._make_request("GET", f"{self.user_id}/threads_insights", params=params)

def get_credentials():
    access_token, user_id = load_env_variables()

    if not access_token:
        access_token = input("Enter your Thread Access Token: ")
    if not user_id:
        user_id = input("Enter your Thread User ID: ")

    return access_token, user_id

def main():
    access_token, user_id = get_credentials()
    thread_api = ThreadAPI(access_token, user_id)

    print(f"Using USER_ID: {thread_api.user_id}")
    print(f"Access Token (first 10 characters): {thread_api.access_token[:10]}...")

    while True:
        print("\nOptions:")
        print("1. Post a new thread")
        print("2. Get recent threads")
        print("3. Get thread details")
        print("4. Get thread insights")
        print("5. Get user insights")
        print("6. Quit")

        choice = input("Enter your choice (1-6): ")

        if choice == '1':
            content = input("Enter your thread content: ")
            try:
                result = thread_api.post_thread(content)
                print(f"Posted thread with ID: {result.get('id', 'No ID')}")
            except Exception as e:
                print(f"Error posting thread: {str(e)}")

        elif choice == '2':
            try:
                threads = thread_api.get_user_threads(limit=5)
                print(f"Retrieved {len(threads)} threads:")
                for thread in threads:
                    print(f"- Thread ID: {thread.get('id', 'No ID')}")
                    print(f"  Text: {thread.get('text', 'No text')}")
                    print(f"  Timestamp: {thread.get('timestamp', 'No timestamp')}")
                    print("---")
            except Exception as e:
                print(f"Error getting threads: {str(e)}")

        elif choice == '3':
            thread_id = input("Enter thread ID: ")
            try:
                thread = thread_api.get_thread(thread_id)
                print(f"Thread details:")
                print(f"- ID: {thread.get('id', 'No ID')}")
                print(f"- Text: {thread.get('text', 'No text')}")
                print(f"- Timestamp: {thread.get('timestamp', 'No timestamp')}")
            except Exception as e:
                print(f"Error getting thread: {str(e)}")

        elif choice == '4':
            thread_id = input("Enter thread ID: ")
            try:
                insights = thread_api.get_thread_insights(thread_id)
                print("Thread insights:")
                for metric in insights.get('data', []):
                    print(f"- {metric.get('name')}: {metric.get('values', [{}])[0].get('value', 'N/A')}")
            except Exception as e:
                print(f"Error getting thread insights: {str(e)}")

        elif choice == '5':
            try:
                insights = thread_api.get_user_insights()
                print("User insights:")
                for metric in insights.get('data', []):
                    print(f"- {metric.get('name')}: {metric.get('values', [{}])[0].get('value', 'N/A')}")
            except Exception as e:
                print(f"Error getting user insights: {str(e)}")

        elif choice == '6':
            print("Goodbye!")
            break

        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()