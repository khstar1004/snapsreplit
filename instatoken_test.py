import requests
import os
from dotenv import load_dotenv
from typing import List, Dict, Any

load_dotenv()

class InstagramAPI:
    BASE_URL = "https://graph.instagram.com/v12.0"

    def __init__(self, access_token: str):
        self.access_token = access_token

    def get_user_media(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        사용자의 Instagram 미디어를 가져옵니다.
        """
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
        """
        API 응답을 보기 좋게 포맷팅합니다.
        """
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

def main():
    access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN')
    if not access_token:
        print("Error: INSTAGRAM_ACCESS_TOKEN not found in .env file")
        return

    instagram_api = InstagramAPI(access_token)
    media_items = instagram_api.get_user_media(limit=10)  # 최근 10개의 게시물 가져오기
    
    if not media_items:
        print("No posts found or error occurred while fetching posts.")
        return

    formatted_posts = instagram_api.format_posts(media_items)

    print(f"Total posts fetched: {len(formatted_posts)}")
    for i, post in enumerate(formatted_posts, 1):
        print(f"\nPost {i}:")
        print(f"ID: {post['id']}")
        print(f"Type: {post['media_type']}")
        print(f"Caption: {post['caption'][:50]}..." if len(post['caption']) > 50 else f"Caption: {post['caption']}")
        print(f"URL: {post['media_url']}")
        print(f"Permalink: {post['permalink']}")
        print(f"Timestamp: {post['timestamp']}")

if __name__ == "__main__":
    main()