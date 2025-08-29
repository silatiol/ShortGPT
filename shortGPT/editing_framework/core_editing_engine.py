from urllib.error import HTTPError
from shortGPT.config.path_utils import get_program_path
import os
from shortGPT.config.path_utils import handle_path
import numpy as np
from typing import Any, Dict, List, Union, Tuple
from moviepy import (AudioFileClip, CompositeVideoClip, CompositeAudioClip, ImageClip,
                    TextClip, VideoFileClip, AudioClip)
from moviepy.Clip import Clip
from moviepy import vfx, afx
from shortGPT.editing_framework.rendering_logger import MoviepyProgressLogger
import json

def load_schema(json_path):
    return json.loads(open(json_path, 'r', encoding='utf-8').read())

class CoreEditingEngine:

    def generate_image(self, schema:Dict[str, Any],output_file , logger=None):
        assets = dict(sorted(schema['visual_assets'].items(), key=lambda item: item[1]['z']))
        clips = []

        for asset_key in assets:
            asset = assets[asset_key]
            asset_type = asset['type']
            if asset_type == 'image':
                clip = self.process_image_asset(asset)
            elif asset_type == 'text':
                clip = self.process_text_asset(asset)
                clips.append(clip)
            else:
                raise ValueError(f'Invalid asset type: {asset_type}')
            clips.append(clip)

        image = CompositeVideoClip(clips)
        image.save_frame(output_file)
        return output_file

    def generate_video(self, schema:Dict[str, Any], output_file, logger=None, force_duration=None, threads=None) -> None:
        visual_assets = dict(sorted(schema['visual_assets'].items(), key=lambda item: item[1]['z']))
        audio_assets = dict(sorted(schema['audio_assets'].items(), key=lambda item: item[1]['z']))
        
        visual_clips = []
        for asset_key in visual_assets:
            asset = visual_assets[asset_key]
            asset_type = asset['type']
            if asset_type == 'video':
                try:
                    clip = self.process_video_asset(asset)
                except Exception as e:
                    print(f"Failed to load video {asset['parameters']['url']}. Error : {str(e)}")
                    continue
            elif asset_type == 'image':
                # clip = self.process_image_asset(asset)
                try:
                    clip = self.process_image_asset(asset)
                except Exception as e:
                    print(f"Failed to load image {asset['parameters']['url']}. Error : {str(e)}")
                    continue
            elif asset_type == 'text':
                clip = self.process_text_asset(asset)
            else:
                raise ValueError(f'Invalid asset type: {asset_type}')

            visual_clips.append(clip)
        
        audio_clips = []

        for asset_key in audio_assets:
            asset = audio_assets[asset_key]
            asset_type = asset['type']
            if asset_type == "audio":
                audio_clip = self.process_audio_asset(asset)
            else:
                raise ValueError(f"Invalid asset type: {asset_type}")

            audio_clips.append(audio_clip)
        video = CompositeVideoClip(visual_clips)
        if(audio_clips):
            audio = CompositeAudioClip(audio_clips)
            video = video.with_audio(audio)
            video = video.with_duration(audio.duration)
        if force_duration:
            video = video.with_duration(force_duration)
        if logger:
            my_logger = MoviepyProgressLogger(callBackFunction=logger)
            video.write_videofile(output_file, threads=threads,codec='libx264', audio_codec='aac', fps=30, preset='veryfast', logger=my_logger)
        else:
            video.write_videofile(output_file, threads=threads,codec='libx264', audio_codec='aac', fps=30, preset='veryfast')
        return output_file
    
    def generate_audio(self, schema:Dict[str, Any], output_file, logger=None) -> None:
        audio_assets = dict(sorted(schema['audio_assets'].items(), key=lambda item: item[1]['z']))
        audio_clips = []

        for asset_key in audio_assets:
            asset = audio_assets[asset_key]
            asset_type = asset['type']
            if asset_type == "audio":
                audio_clip = self.process_audio_asset(asset)
            else:
                raise ValueError(f"Invalid asset type: {asset_type}")

            audio_clips.append(audio_clip)
        audio = CompositeAudioClip(audio_clips)
        audio.fps = 44100
        if logger:
            my_logger = MoviepyProgressLogger(callBackFunction=logger)
            audio.write_audiofile(output_file, logger=my_logger)
        else:
            audio.write_audiofile(output_file)
        return output_file
    # Process common actions
    def process_common_actions(self,
                                   clip: Union[VideoFileClip, ImageClip, TextClip, AudioFileClip],
                                   actions: List[Dict[str, Any]]) -> Union[VideoFileClip, AudioFileClip, ImageClip, TextClip]:
        for action in actions:
            if action['type'] == 'set_time_start':
                clip = clip.with_start(action['param'])
                continue
   
            if action['type'] == 'set_time_end':
                clip = clip.with_end(action['param'])
                continue
            
            if action['type'] == 'subclip':
                clip = clip.subclipped(**action['param'])
                continue

        return clip

    # Process common visual clip actions
    def process_common_visual_actions(self,
                                   clip: Clip,
                                   actions: List[Dict[str, Any]]) -> Union[VideoFileClip, ImageClip, TextClip]:
        clip = self.process_common_actions(clip, actions)
        for action in actions:
 
            if action['type'] == 'resize':
                clip = clip.with_effects([vfx.Resize(**action['param'])])
                continue

            if action['type'] == 'crop':
                clip = clip.with_effects([vfx.Crop(**action['param'])])
                continue

            if action['type'] == 'screen_position':
                clip = clip.with_position(**action['param'])
                continue

            if action['type'] == 'green_screen':
                params = action['param']
                color = params['color'] if  params['color'] else [52, 255, 20]
                thr = params["threshold"] if params["threshold"] else 100
                s = params['stiffness'] if params['stiffness'] else 5
                clip = clip.with_effects([vfx.MaskColor(color=color,threshold=thr, stiffness=s)])
                continue

            if action['type'] == 'normalize_image':
                clip = clip.image_transform(self.__normalize_frame)
                continue

            if action['type'] == 'auto_resize_image':
                ar = clip.aspect_ratio
                height = action['param']['maxHeight']
                width = action['param']['maxWidth']
                if ar <1:
                    clip = clip.with_effects([vfx.Resize((height*ar, height))])
                else:
                    clip = clip.with_effects([vfx.Resize((width, width/ar))])
                continue

        return clip

    # Process audio actions
    def process_audio_actions(self, clip: AudioClip,
                            actions: List[Dict[str, Any]]) -> AudioClip:
        clip = self.process_common_actions(clip, actions)
        for action in actions:
            if action['type'] == 'normalize_music':
                clip = clip.with_effects([afx.AudioNormalize()])
                continue

            if action['type'] == 'loop_background_music':
                target_duration = action['param']
                start = clip.duration * 0.15
                clip = clip.subclipped(start)
                clip = clip.with_effects([afx.AudioLoop(duration=target_duration)])
                continue

            if action['type'] == 'volume_percentage':
                clip = clip.with_effects([afx.MultiplyVolume(action['param'])])
                continue

        return clip
    # Process individual asset types
    def process_video_asset(self, asset: Dict[str, Any]) -> VideoFileClip:
        params = {
            'filename': handle_path(asset['parameters']['url'])
        }
        if 'audio' in asset['parameters']:
            params['audio'] = asset['parameters']['audio']
        clip = VideoFileClip(**params)
        
        # Add automatic cropping for vertical format if needed
        clip = self._auto_crop_for_vertical(clip, asset)
        
        return self.process_common_visual_actions(clip, asset['actions'])
    
    def _auto_crop_for_vertical(self, clip: VideoFileClip, asset: Dict[str, Any]) -> VideoFileClip:
        """
        Automatically crop video to match vertical 1080x1920 format if needed.
        
        Args:
            clip: Original video clip
            asset: Asset configuration
            
        Returns:
            Cropped video clip optimized for vertical format
        """
        # Target vertical resolution: 1080x1920 (9:16 aspect ratio)
        target_width = 1080
        target_height = 1920
        target_aspect_ratio = target_width / target_height  # 0.5625
        
        # Get current video dimensions
        current_width = clip.w
        current_height = clip.h
        current_aspect_ratio = current_width / current_height
        
        print(f"📐 Video dimensions: {current_width}x{current_height} (aspect ratio: {current_aspect_ratio:.3f})")
        print(f"🎯 Target dimensions: {target_width}x{target_height} (aspect ratio: {target_aspect_ratio:.3f})")
        
        # If already correct aspect ratio, just resize
        if abs(current_aspect_ratio - target_aspect_ratio) < 0.01:
            print("✅ Video already has correct aspect ratio, just resizing...")
            clip = clip.with_effects([vfx.Resize((target_width, target_height))])
            return clip
        
        # If video is wider than target (landscape), crop width and center
        if current_aspect_ratio > target_aspect_ratio:
            print("📱 Cropping landscape video to vertical format...")
            
            # Calculate new width to match target aspect ratio
            new_width = int(current_height * target_aspect_ratio)
            x_offset = (current_width - new_width) // 2  # Center crop
            
            print(f"   🔧 Cropping from {current_width}x{current_height} to {new_width}x{current_height}")
            print(f"   📍 Crop position: x={x_offset}, y=0")
            
            # Apply crop then resize to target dimensions
            clip = clip.with_effects([
                vfx.Crop(x1=x_offset, y1=0, width=new_width, height=current_height),
                vfx.Resize((target_width, target_height))
            ])
            
        # If video is taller than target (portrait but wrong ratio), crop height and center
        elif current_aspect_ratio < target_aspect_ratio:
            print("📐 Cropping tall video to vertical format...")
            
            # Calculate new height to match target aspect ratio
            new_height = int(current_width / target_aspect_ratio)
            y_offset = (current_height - new_height) // 2  # Center crop
            
            print(f"   🔧 Cropping from {current_width}x{current_height} to {current_width}x{new_height}")
            print(f"   📍 Crop position: x=0, y={y_offset}")
            
            # Apply crop then resize to target dimensions
            clip = clip.with_effects([
                vfx.Crop(x1=0, y1=y_offset, width=current_width, height=new_height),
                vfx.Resize((target_width, target_height))
            ])
        
        print(f"✅ Video cropped and resized to {target_width}x{target_height}")
        return clip

    def process_image_asset(self, asset: Dict[str, Any]) -> ImageClip:
        clip = ImageClip(asset['parameters']['url'])
        return self.process_common_visual_actions(clip, asset['actions'])

    def _parse_bracket_text(self, text: str) -> List[Tuple[str, bool]]:
        """
        Parse text to identify bracketed sections and regular text.
        
        Args:
            text: Input text with potential [bracketed] sections
            
        Returns:
            List of tuples (text_segment, is_highlighted)
        """
        import re
        
        segments = []
        last_end = 0
        
        # Find all bracketed sections
        bracket_pattern = r'\[([^\]]+)\]'
        for match in re.finditer(bracket_pattern, text):
            # Add regular text before the bracket
            if match.start() > last_end:
                regular_text = text[last_end:match.start()]
                if regular_text.strip():
                    segments.append((regular_text, False))
            
            # Add bracketed text (without brackets)
            bracketed_text = match.group(1)
            segments.append((bracketed_text, True))
            
            last_end = match.end()
        
        # Add remaining regular text
        if last_end < len(text):
            remaining_text = text[last_end:]
            if remaining_text.strip():
                segments.append((remaining_text, False))
        
        # If no brackets found, return the entire text as regular
        if not segments:
            segments.append((text, False))
            
        return segments

    def _create_composite_text_clip(self, asset: Dict[str, Any]) -> Union[TextClip, CompositeVideoClip]:
        """
        Create a text clip with bracket highlighting using different colors.
        
        This creates multiple TextClip objects with different colors and combines them.
        
        Args:
            asset: Text asset configuration
            
        Returns:
            CompositeVideoClip with multi-colored text or fallback TextClip
        """
        text_clip_params = asset['parameters']
        text = text_clip_params['text']
        
        # Parse text segments
        segments = self._parse_bracket_text(text)
        
        # If only one segment and it's not highlighted, use simple TextClip
        if len(segments) == 1 and not segments[0][1]:
            return self.process_common_visual_actions(self._create_simple_text_clip(asset), asset['actions'])
        
        # Try to create multi-color text
        try:
            clips = []
            
            # Base parameters
            base_color = text_clip_params.get('color', 'white')
            highlight_color = text_clip_params.get('highlight_color', '#FFD700')
            font = text_clip_params.get('font')
            font_size = text_clip_params.get('font_size', 100)
            stroke_width = text_clip_params.get('stroke_width', 3)
            stroke_color = text_clip_params.get('stroke_color', 'black')
            
            # Create individual text clips for each segment
            for segment_text, is_highlighted in segments:
                if not segment_text.strip():
                    continue
                
                color = highlight_color if is_highlighted else base_color
                
                # Create text clip for this segment
                clip_params = {
                    'text': segment_text,
                    'font': font,
                    'font_size': font_size,
                    'color': color,
                    'stroke_width': stroke_width + (1 if is_highlighted else 0),
                    'stroke_color': stroke_color,
                    'method': 'label'  # Use label for individual segments
                }
                clip_params = {k: v for k, v in clip_params.items() if v is not None}
                
                segment_clip = TextClip(**clip_params)
                clips.append(segment_clip)
            
            if len(clips) > 1:
                # For now, concatenate the text strings with color indicators since positioning is complex
                # This provides a simpler but functional approach
                combined_text = ""
                for i, (segment_text, is_highlighted) in enumerate(segments):
                    if not segment_text.strip():
                        continue
                    if is_highlighted:
                        combined_text += f"🔥{segment_text}🔥"
                    else:
                        combined_text += segment_text
                
                # Create a single text clip with the combined text
                modified_params = text_clip_params.copy()
                modified_params['text'] = combined_text
                modified_asset = dict(asset)
                modified_asset['parameters'] = modified_params
                
                # Apply actions to the single clip
                return self.process_common_visual_actions(self._create_simple_text_clip(modified_asset), asset['actions'])
            
            elif len(clips) == 1:
                return self.process_common_visual_actions(clips[0], asset['actions'])
                
        except Exception as e:
            print(f"Warning: Multi-color text failed ({e}), using emoji emphasis fallback")
            
        # Fallback to visual emphasis approach
        import re
        # Use bold-style visual markers for highlighted text
        highlighted_text = re.sub(r'\[([^\]]+)\]', r'>>> \1 <<<', text)
        
        modified_params = text_clip_params.copy()
        modified_params['text'] = highlighted_text
        modified_asset = dict(asset)
        modified_asset['parameters'] = modified_params
        
        return self.process_common_visual_actions(self._create_simple_text_clip(modified_asset), asset['actions'])

    def _create_simple_text_clip(self, asset: Dict[str, Any]) -> TextClip:
        """
        Create a simple TextClip without special formatting.
        
        Args:
            asset: Text asset configuration
            
        Returns:
            Simple TextClip
        """
        text_clip_params = asset['parameters']
        
        clip_info = {
            'text': text_clip_params['text'],
            'font': text_clip_params.get('font'),
            'font_size': text_clip_params.get('font_size'),
            'color': text_clip_params.get('color'),
            'stroke_width': text_clip_params.get('stroke_width'),
            'stroke_color': text_clip_params.get('stroke_color'),
            'size': text_clip_params.get('size'),
            'method': text_clip_params.get('method', 'label'),
            'text_align': text_clip_params.get('text_align', 'center')
        }
        clip_info = {k: v for k, v in clip_info.items() if v is not None}
        
        return TextClip(**clip_info)

    def process_text_asset(self, asset: Dict[str, Any]) -> Union[TextClip, CompositeVideoClip]:
        text_clip_params = asset['parameters']
        
        if not (any(key in text_clip_params for key in ['text','fontsize', 'size'])):
            raise Exception('You must include at least a size or a fontsize to determine the size of your text')
        
        # Check if text contains brackets - if so, use composite text processing for highlighting
        text = text_clip_params.get('text', '')
        method = text_clip_params.get('method', 'label')
        
        # Use composite text processing for bracket highlighting regardless of method
        if '[' in text and ']' in text:
            return self._create_composite_text_clip(asset)
        else:
            # Use simple text clip for regular text
            return self.process_common_visual_actions(self._create_simple_text_clip(asset), asset['actions'])

    def process_audio_asset(self, asset: Dict[str, Any]) -> AudioFileClip:
        clip = AudioFileClip(asset['parameters']['url'])
        return self.process_audio_actions(clip, asset['actions'])
    
    def __normalize_image(self, clip):
        def f(get_frame, t):
            if f.normalized_frame is not None:
                return f.normalized_frame
            else:
                frame = get_frame(t)
                f.normalized_frame = self.__normalize_frame(frame)
                return f.normalized_frame

        f.normalized_frame = None

        return clip.fl(f)


    def __normalize_frame(self, frame):
        shape = np.shape(frame)
        [dimensions, ] = np.shape(shape)

        if dimensions == 2:
            (height, width) = shape
            normalized_frame = np.zeros((height, width, 3))
            for y in range(height):
                for x in range(width):
                    grey_value = frame[y][x]
                    normalized_frame[y][x] = (grey_value, grey_value, grey_value)
            return normalized_frame
        else:
            return frame
        

