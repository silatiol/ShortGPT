import os
import platform
import sys
import subprocess
import tempfile
import hashlib
import requests
from urllib.parse import urlparse
def search_program(program_name):
    try: 
        search_cmd = "where" if platform.system() == "Windows" else "which"
        return subprocess.check_output([search_cmd, program_name]).decode().strip()
    except subprocess.CalledProcessError:
        return None

def get_program_path(program_name):
    program_path = search_program(program_name)
    return program_path

def is_running_in_colab():
    return 'COLAB_GPU' in os.environ

def handle_path(path, extension = ".mp4"):
    if 'https' in path or 'http' in path:
        return download_video_locally(path, extension)
    return path

def download_video_locally(url, extension=".mp4"):
    """
    Download a video from a URL to a local temporary file.
    Uses caching based on URL hash to avoid re-downloading the same video.
    """
    try:
        # Create a hash of the URL to use as a cache key
        url_hash = hashlib.md5(url.encode()).hexdigest()
        
        # Create a cache directory if it doesn't exist
        cache_dir = os.path.join(tempfile.gettempdir(), "shortgpt_video_cache")
        os.makedirs(cache_dir, exist_ok=True)
        
        # Check if we already have this video cached
        cached_file = os.path.join(cache_dir, f"{url_hash}{extension}")
        if os.path.exists(cached_file) and os.path.getsize(cached_file) > 0:
            print(f"Using cached video: {cached_file}")
            return cached_file
        
        print(f"Downloading video from: {url}")
        
        # Download the video using requests (more reliable than ffmpeg for HTTPS)
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        # Save to cache file
        with open(cached_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        print(f"Video downloaded successfully: {cached_file}")
        return cached_file
        
    except Exception as e:
        print(f"Failed to download video from {url}: {e}")
        # Fallback: try using ffmpeg as before (in case the URL works with ffmpeg but not requests)
        try:
            temp_file = tempfile.NamedTemporaryFile(suffix=extension, delete=False)
            command = ['ffmpeg', '-y', '-i', url, temp_file.name]
            subprocess.run(command, check=True, capture_output=True)
            temp_file.close()
            print(f"Video downloaded via ffmpeg: {temp_file.name}")
            return temp_file.name
        except Exception as ffmpeg_error:
            print(f"FFmpeg download also failed: {ffmpeg_error}")
            # If both methods fail, return the original URL and let MoviePy try to handle it
            return url