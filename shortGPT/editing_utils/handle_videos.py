import os
import random
import yt_dlp
import subprocess
import json

def getYoutubeVideoLink(url):
    # Determine if this is a shorts video and adjust format accordingly
    is_shorts = 'shorts' in url.lower()
    
    if is_shorts:
        # For shorts, prefer vertical formats but fall back gracefully
        format_selector = "best[height>=width]/best"
    else:
        # For regular videos, prefer landscape formats with reasonable resolution
        format_selector = "best[height<=1080]/best"
    
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "no_color": True,
        "no_call_home": True,
        "no_check_certificate": True,
        "format": format_selector
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            dictMeta = ydl.extract_info(
                url,
                download=False)
            return dictMeta['url'], dictMeta['duration']
    except Exception as e:
        raise Exception(f"Failed getting video link from the following video/url {url} {e.args[0]}")

def validate_video_file(video_path):
    """Validates that a video file is not corrupted and has valid metadata.
    
    Args:
        video_path (str): Path to the video file to validate.
        
    Returns:
        bool: True if video is valid, False otherwise.
    """
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            return False
            
        metadata = json.loads(result.stdout)
        
        # Check if format has duration
        if 'format' not in metadata or 'duration' not in metadata['format']:
            return False
            
        duration = float(metadata['format']['duration'])
        if duration <= 0:
            return False
            
        # Check if there's at least one video stream
        video_streams = [s for s in metadata.get('streams', []) if s.get('codec_type') == 'video']
        if not video_streams:
            return False
            
        return True
    except (subprocess.TimeoutExpired, json.JSONDecodeError, ValueError, KeyError):
        return False

def extract_random_clip_from_video(video_url, video_duration, clip_duration, output_file):
    """Extracts a clip from a video using a signed URL.
    Args:
        video_url (str): The signed URL of the video.
        video_duration (int): Duration of the video.
        start_time (int): The start time of the clip in seconds.
        clip_duration (int): The duration of the clip in seconds.
        output_file (str): The output file path for the extracted clip.
    """
    if not video_duration:
        raise Exception("Could not get video duration")
    if not video_duration*0.7 > 120:
        raise Exception("Video too short")
    
    max_attempts = 3
    for attempt in range(max_attempts):
        start_time = video_duration*0.15 + random.random()* (0.7*video_duration-clip_duration)
        
        # Remove existing file if it exists
        if os.path.exists(output_file):
            os.remove(output_file)
        
        command = [
            'ffmpeg',
            '-loglevel', 'error',
            '-ss', str(start_time),
            '-t', str(clip_duration),
            '-i', video_url,
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-avoid_negative_ts', 'make_zero',
            output_file
        ]
        
        try:
            subprocess.run(command, check=True, timeout=120)
            
            if not os.path.exists(output_file):
                if attempt == max_attempts - 1:
                    raise Exception("Random clip failed to be written")
                continue
                
            # Validate the output video file
            if validate_video_file(output_file):
                return output_file
            else:
                if attempt == max_attempts - 1:
                    raise Exception(f"Generated video clip is corrupted after {max_attempts} attempts")
                # Try again with a different random segment
                continue
                
        except subprocess.CalledProcessError as e:
            if attempt == max_attempts - 1:
                raise Exception(f"FFmpeg failed to extract clip: {e}")
            continue
        except subprocess.TimeoutExpired:
            if attempt == max_attempts - 1:
                raise Exception("FFmpeg timeout while extracting clip")
            continue
    
    raise Exception(f"Failed to extract valid video clip after {max_attempts} attempts")


def get_aspect_ratio(video_file):
    cmd = 'ffprobe -i "{}" -v quiet -print_format json -show_format -show_streams'.format(video_file)
#     jsonstr = subprocess.getoutput(cmd)
    jsonstr = subprocess.check_output(cmd, shell=True, encoding='utf-8')
    r = json.loads(jsonstr)
    # look for "codec_type": "video". take the 1st one if there are mulitple
    video_stream_info = [x for x in r['streams'] if x['codec_type']=='video'][0]
    if 'display_aspect_ratio' in video_stream_info and video_stream_info['display_aspect_ratio']!="0:1":
        a,b = video_stream_info['display_aspect_ratio'].split(':')
        dar = int(a)/int(b)
    else:
        # some video do not have the info of 'display_aspect_ratio'
        w,h = video_stream_info['width'], video_stream_info['height']
        dar = int(w)/int(h)
        ## not sure if we should use this
        #cw,ch = video_stream_info['coded_width'], video_stream_info['coded_height']
        #sar = int(cw)/int(ch)
    if 'sample_aspect_ratio' in video_stream_info and video_stream_info['sample_aspect_ratio']!="0:1":
        # some video do not have the info of 'sample_aspect_ratio'
        a,b = video_stream_info['sample_aspect_ratio'].split(':')
        sar = int(a)/int(b)
    else:
        sar = dar
    par = dar/sar
    return dar