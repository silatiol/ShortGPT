"""
TikTok Business API Upload Module
Handles video uploads to TikTok using the Business API with proper error handling and optimization
"""

from __future__ import print_function
import os
import time
import hashlib
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

try:
    import business_api_client
    from business_api_client.rest import ApiException
    TIKTOK_SDK_AVAILABLE = True
except ImportError:
    print("⚠️  TikTok Business API SDK not installed. Run: pip install business-api-client")
    TIKTOK_SDK_AVAILABLE = False

from shortGPT.config.api_db import ApiKeyManager


@dataclass
class TikTokUploadConfig:
    """Configuration for TikTok video uploads"""
    advertiser_id: str
    access_token: str
    video_title: str
    video_description: str
    privacy_level: str = "PUBLIC_TO_EVERYONE"  # PUBLIC_TO_EVERYONE, MUTUAL_FOLLOW_FRIEND, SELF_ONLY
    disable_duet: bool = False
    disable_comment: bool = False
    disable_stitch: bool = False
    video_cover_timestamp_ms: int = 1000  # Cover frame timestamp
    brand_content_toggle: bool = False
    brand_organic_toggle: bool = False


class TikTokBusinessUploader:
    """
    Handles TikTok video uploads using Business API
    Supports automatic retries, progress tracking, and comprehensive error handling
    """
    
    def __init__(self, advertiser_id: Optional[str] = None, access_token: Optional[str] = None):
        """
        Initialize TikTok uploader
        
        Args:
            advertiser_id: TikTok advertiser ID (can be set later or from environment)
            access_token: TikTok access token (can be set later or from environment)
        """
        
        if not TIKTOK_SDK_AVAILABLE:
            raise ImportError("TikTok Business API SDK not available. Install with: pip install business-api-client")
        
        # Initialize API client
        self.configuration = business_api_client.Configuration()
        self.api_client = business_api_client.ApiClient(self.configuration)
        
        # Initialize API instances
        self.file_api = business_api_client.FileApi(self.api_client)
        self.creative_asset_api = business_api_client.CreativeAssetApi(self.api_client)
        self.tool_api = business_api_client.ToolApi(self.api_client)
        
        # Set credentials
        self.advertiser_id = advertiser_id or self._get_advertiser_id()
        self.access_token = access_token or self._get_access_token()
        
        if not self.advertiser_id or not self.access_token:
            raise ValueError("TikTok advertiser_id and access_token are required")
        
        print(f"🎬 TikTok Business API uploader initialized")
        print(f"   📊 Advertiser ID: {self.advertiser_id[:8]}...")
        print(f"   🔑 Access token configured: {bool(self.access_token)}")
    
    def _get_advertiser_id(self) -> str:
        """Get advertiser ID from API key manager or environment"""
        return (ApiKeyManager.get_api_key("TIKTOK_ADVERTISER_ID") or 
                os.environ.get("TIKTOK_ADVERTISER_ID", ""))
    
    def _get_access_token(self) -> str:
        """Get access token from API key manager or environment"""
        return (ApiKeyManager.get_api_key("TIKTOK_ACCESS_TOKEN") or 
                os.environ.get("TIKTOK_ACCESS_TOKEN", ""))
    
    def test_connection(self) -> bool:
        """
        Test TikTok API connection and credentials
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        
        try:
            print("🔍 Testing TikTok API connection...")
            
            # Test with language endpoint (lightweight test)
            response = self.tool_api.tool_language(
                advertiser_id=self.advertiser_id,
                access_token=self.access_token
            )
            
            print(f"✅ TikTok API connection successful!")
            print(f"   📍 Available languages: {len(response.data) if response.data else 0}")
            return True
            
        except ApiException as e:
            print(f"❌ TikTok API connection failed: {e}")
            print(f"   Status: {e.status}")
            print(f"   Reason: {e.reason}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error testing TikTok connection: {e}")
            return False
    
    def upload_video(self, video_path: str, config: TikTokUploadConfig, 
                    max_retries: int = 3) -> Dict[str, Any]:
        """
        Upload video to TikTok with comprehensive error handling
        
        Args:
            video_path: Path to the video file to upload
            config: Upload configuration including title, description, etc.
            max_retries: Maximum number of retry attempts
            
        Returns:
            Dict containing upload result and metadata
        """
        
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        if not self._validate_video_file(video_path):
            raise ValueError(f"Video file validation failed: {video_path}")
        
        print(f"🚀 Starting TikTok video upload...")
        print(f"   📹 Video: {os.path.basename(video_path)}")
        print(f"   📝 Title: {config.video_title}")
        print(f"   🔒 Privacy: {config.privacy_level}")
        
        upload_result = {
            "success": False,
            "video_id": None,
            "upload_url": None,
            "error": None,
            "metadata": {
                "file_path": video_path,
                "file_size": os.path.getsize(video_path),
                "upload_time": time.time(),
                "config": config
            }
        }
        
        for attempt in range(max_retries):
            try:
                print(f"📤 Upload attempt {attempt + 1}/{max_retries}")
                
                # Step 1: Upload video file
                video_upload_result = self._upload_video_file(video_path)
                
                if not video_upload_result["success"]:
                    raise Exception(f"Video file upload failed: {video_upload_result['error']}")
                
                video_id = video_upload_result["video_id"]
                print(f"✅ Video file uploaded successfully!")
                print(f"   🆔 Video ID: {video_id}")
                
                # Step 2: Create video post
                post_result = self._create_video_post(video_id, config)
                
                if not post_result["success"]:
                    raise Exception(f"Video post creation failed: {post_result['error']}")
                
                upload_result.update({
                    "success": True,
                    "video_id": video_id,
                    "post_id": post_result.get("post_id"),
                    "upload_url": post_result.get("upload_url"),
                    "metadata": {
                        **upload_result["metadata"],
                        "upload_duration": time.time() - upload_result["metadata"]["upload_time"],
                        "attempts": attempt + 1
                    }
                })
                
                print(f"🎉 TikTok video uploaded successfully!")
                print(f"   🆔 Video ID: {video_id}")
                print(f"   📱 Post ID: {post_result.get('post_id', 'N/A')}")
                
                return upload_result
                
            except ApiException as e:
                error_msg = f"TikTok API error (attempt {attempt + 1}): Status {e.status} - {e.reason}"
                print(f"❌ {error_msg}")
                
                if attempt == max_retries - 1:
                    upload_result["error"] = error_msg
                    break
                else:
                    wait_time = (attempt + 1) * 2  # Exponential backoff
                    print(f"⏳ Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    
            except Exception as e:
                error_msg = f"Upload error (attempt {attempt + 1}): {str(e)}"
                print(f"❌ {error_msg}")
                
                if attempt == max_retries - 1:
                    upload_result["error"] = error_msg
                    break
                else:
                    wait_time = (attempt + 1) * 2
                    print(f"⏳ Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
        
        print(f"💥 TikTok upload failed after {max_retries} attempts")
        return upload_result
    
    def _validate_video_file(self, video_path: str) -> bool:
        """Validate video file for TikTok upload requirements"""
        
        try:
            file_size = os.path.getsize(video_path)
            
            # TikTok Business API limits (may vary)
            max_size = 500 * 1024 * 1024  # 500MB
            min_size = 1024  # 1KB
            
            if file_size > max_size:
                print(f"❌ Video file too large: {file_size / (1024*1024):.1f}MB > {max_size / (1024*1024):.1f}MB")
                return False
            
            if file_size < min_size:
                print(f"❌ Video file too small: {file_size}B < {min_size}B")
                return False
            
            # Check file extension
            allowed_extensions = ['.mp4', '.mov', '.avi', '.mkv']
            file_ext = os.path.splitext(video_path)[1].lower()
            
            if file_ext not in allowed_extensions:
                print(f"❌ Unsupported video format: {file_ext}")
                return False
            
            print(f"✅ Video file validation passed")
            print(f"   📏 Size: {file_size / (1024*1024):.1f}MB")
            print(f"   📁 Format: {file_ext}")
            
            return True
            
        except Exception as e:
            print(f"❌ Video validation error: {e}")
            return False
    
    def _upload_video_file(self, video_path: str) -> Dict[str, Any]:
        """Upload video file to TikTok servers"""
        
        try:
            print(f"📤 Uploading video file...")
            
            # Read video file
            with open(video_path, 'rb') as video_file:
                video_data = video_file.read()
            
            # Prepare upload request
            upload_request = {
                'advertiser_id': self.advertiser_id,
                'access_token': self.access_token,
                'upload_type': 'UPLOAD_BY_FILE',  # Upload by file content
                'video_file': video_data,
                'video_signature': hashlib.md5(video_data).hexdigest()
            }
            
            # Upload using File API
            response = self.file_api.file_video_ad_upload(**upload_request)
            
            if response.code != 0:
                return {
                    "success": False,
                    "error": f"Upload failed: {response.message}",
                    "video_id": None
                }
            
            video_id = response.data.video_id if response.data else None
            
            return {
                "success": True,
                "video_id": video_id,
                "error": None
            }
            
        except ApiException as e:
            return {
                "success": False,
                "error": f"API Exception: {e.reason}",
                "video_id": None
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Upload Exception: {str(e)}",
                "video_id": None
            }
    
    def _create_video_post(self, video_id: str, config: TikTokUploadConfig) -> Dict[str, Any]:
        """Create TikTok video post using uploaded video"""
        
        try:
            print(f"📝 Creating TikTok post...")
            
            # Prepare post creation request
            post_request = {
                'advertiser_id': self.advertiser_id,
                'access_token': self.access_token,
                'video_id': video_id,
                'text': config.video_description,
                'privacy_level': config.privacy_level,
                'disable_duet': config.disable_duet,
                'disable_comment': config.disable_comment,
                'disable_stitch': config.disable_stitch,
                'video_cover_timestamp_ms': config.video_cover_timestamp_ms,
                'brand_content_toggle': config.brand_content_toggle,
                'brand_organic_toggle': config.brand_organic_toggle
            }
            
            # Create post using Creative Asset API
            response = self.creative_asset_api.creative_asset_create(**post_request)
            
            if response.code != 0:
                return {
                    "success": False,
                    "error": f"Post creation failed: {response.message}",
                    "post_id": None
                }
            
            post_id = response.data.post_id if response.data else None
            
            return {
                "success": True,
                "post_id": post_id,
                "upload_url": f"https://www.tiktok.com/@user/video/{post_id}" if post_id else None,
                "error": None
            }
            
        except ApiException as e:
            return {
                "success": False,
                "error": f"Post API Exception: {e.reason}",
                "post_id": None
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Post Exception: {str(e)}",
                "post_id": None
            }
    
    def get_upload_status(self, video_id: str) -> Dict[str, Any]:
        """Check upload status of a video"""
        
        try:
            response = self.file_api.file_video_ad_get(
                advertiser_id=self.advertiser_id,
                access_token=self.access_token,
                video_ids=[video_id]
            )
            
            if response.code != 0:
                return {
                    "success": False,
                    "error": f"Status check failed: {response.message}",
                    "status": "unknown"
                }
            
            video_data = response.data.list[0] if response.data and response.data.list else None
            
            if not video_data:
                return {
                    "success": False,
                    "error": "Video not found",
                    "status": "not_found"
                }
            
            return {
                "success": True,
                "video_id": video_id,
                "status": video_data.video_status,
                "processing_status": video_data.processing_status,
                "error": None
            }
            
        except ApiException as e:
            return {
                "success": False,
                "error": f"Status API Exception: {e.reason}",
                "status": "error"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Status Exception: {str(e)}",
                "status": "error"
            }
    
    @staticmethod
    def create_upload_config(video_title: str, video_description: str, 
                           privacy: str = "PUBLIC_TO_EVERYONE",
                           hashtags: List[str] = None, 
                           disable_comments: bool = False) -> TikTokUploadConfig:
        """
        Create upload configuration with smart defaults
        
        Args:
            video_title: Title for the video
            video_description: Description text
            privacy: Privacy level
            hashtags: List of hashtags to include
            disable_comments: Whether to disable comments
            
        Returns:
            TikTokUploadConfig object
        """
        
        # Add hashtags to description if provided
        if hashtags:
            hashtag_text = " ".join(f"#{tag.strip('#')}" for tag in hashtags)
            video_description = f"{video_description}\n\n{hashtag_text}"
        
        # Ensure description is within TikTok limits (usually 2200 characters)
        if len(video_description) > 2200:
            video_description = video_description[:2197] + "..."
        
        return TikTokUploadConfig(
            advertiser_id="",  # Will be set by uploader
            access_token="",   # Will be set by uploader
            video_title=video_title,
            video_description=video_description,
            privacy_level=privacy,
            disable_comment=disable_comments,
            disable_duet=False,
            disable_stitch=False,
            video_cover_timestamp_ms=1000,
            brand_content_toggle=False,
            brand_organic_toggle=False
        )


def test_tiktok_connection():
    """Test TikTok Business API connection"""
    
    print("🔧 Testing TikTok Business API Connection")
    print("=" * 50)
    
    try:
        uploader = TikTokBusinessUploader()
        success = uploader.test_connection()
        
        if success:
            print("✅ TikTok API is ready for video uploads!")
        else:
            print("❌ TikTok API connection failed. Check credentials.")
            
        return success
        
    except Exception as e:
        print(f"❌ TikTok connection test failed: {e}")
        return False


if __name__ == "__main__":
    # Test the TikTok connection
    test_tiktok_connection()