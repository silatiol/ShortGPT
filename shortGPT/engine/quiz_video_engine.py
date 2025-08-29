import datetime
import os
import re
import shutil
import json
import subprocess
from typing import List, Tuple, Dict, Any

from shortGPT.api_utils.pexels_api import getBestVideo
from shortGPT.audio import audio_utils
from shortGPT.audio.audio_duration import get_asset_duration
from shortGPT.audio.voice_module import VoiceModule
from shortGPT.config.asset_db import AssetDatabase
from shortGPT.config.languages import Language
from shortGPT.editing_framework.editing_engine import (EditingEngine,
                                                       EditingStep)
from shortGPT.editing_utils import captions
from shortGPT.engine.content_video_engine import ContentVideoEngine
from shortGPT.gpt import gpt_editing, gpt_translate, gpt_yt
from shortGPT.gpt.quiz_script_generator import QuizScriptGenerator
from shortGPT.api_utils.tiktok_upload import TikTokBusinessUploader, TikTokUploadConfig


class QuizVideoEngine(ContentVideoEngine):
    """
    QuizVideoEngine extends ContentVideoEngine to create quiz-style TikTok videos.
    
    Features:
    - Question headline display
    - 3-2-1 countdown overlay
    - Answer reveal with emoji
    - Final CTA (Call to Action)
    - Always outputs vertical 1080x1920 MP4
    - No background music (for trending TikTok sounds)
    """

    def __init__(self, voiceModule: VoiceModule, quiz_script: str, id="",
                 watermark=None, language: Language = Language.ENGLISH,
                 intro_text="", intro_duration=2.0, video_source="pexels",
                 background_video_asset=None, use_sound_effects=True,
                 intro_sound_asset=None, countdown_sound_asset=None,
                 answer_sound_asset=None, auto_upload_tiktok=False,
                 tiktok_title="", tiktok_description="", tiktok_hashtags=None):
        """
        Initialize QuizVideoEngine with quiz-specific configuration.
        
        Args:
            voiceModule: Voice synthesis module for audio generation
            quiz_script: Time-stamped quiz script with questions, countdown, answers, and CTA
            id: Optional unique identifier for the video
            watermark: Optional watermark text
            language: Language for the quiz (defaults to English)
            intro_text: Text for intro animation to capture attention (default: "")
            intro_duration: Duration of intro animation in seconds (default: 2.0)
            video_source: Source for background video - "pexels" or "asset_library" (default: "pexels")
            background_video_asset: Name of asset from library if using asset_library source (default: None)
            use_sound_effects: Enable sound effects (default: True)
            intro_sound_asset: Asset name for intro sound effect (default: auto-generated)
            countdown_sound_asset: Asset name for countdown sound effect (default: auto-generated)
            answer_sound_asset: Asset name for answer ding sound effect (default: auto-generated)
            auto_upload_tiktok: Automatically upload to TikTok after video generation (default: False)
            tiktok_title: Title for TikTok upload (default: auto-generated)
            tiktok_description: Description for TikTok upload (default: auto-generated)
            tiktok_hashtags: List of hashtags for TikTok upload (default: None)
        """
        # Always use vertical format and no background music for quiz videos
        super().__init__(
            voiceModule=voiceModule,
            script=quiz_script,
            background_music_name="",  # No background music for TikTok compatibility
            id=id,
            watermark=watermark,
            isVerticalFormat=True,  # Always vertical 1080x1920
            language=language
        )
        
        # Ensure no background music for TikTok compatibility
        if not id:  # Only set if not loading existing content
            self._db_background_music_name = ""
        
        # Store new configuration options
        self._intro_text = intro_text
        self._intro_duration = intro_duration
        self._video_source = video_source
        self._background_video_asset = background_video_asset
        self._use_sound_effects = use_sound_effects
        self._intro_sound_asset = intro_sound_asset
        self._countdown_sound_asset = countdown_sound_asset
        self._answer_sound_asset = answer_sound_asset
        
        # TikTok upload configuration
        self._auto_upload_tiktok = auto_upload_tiktok
        self._tiktok_title = tiktok_title
        self._tiktok_description = tiktok_description
        self._tiktok_hashtags = tiktok_hashtags or []
        self._tiktok_uploader = None  # Initialize when needed
        
        # Parse quiz script into structured components
        self._db_quiz_components = self._parse_quiz_script(quiz_script)
        
        # Initialize sound effects
        if self._use_sound_effects:
            self._setupSoundEffects()
    
    @classmethod
    def create_from_topic(cls, voiceModule: VoiceModule, topic: str,
                         num_questions: int = 3, difficulty: str = "medium",
                         style: str = "engaging", target_duration: float = 30.0,
                         intro_text: str = "", intro_duration: float = 2.0,
                         video_source: str = "pexels", background_video_asset=None,
                         use_sound_effects: bool = True, intro_sound_asset=None,
                         countdown_sound_asset=None, answer_sound_asset=None,
                         auto_upload_tiktok: bool = False, tiktok_title: str = "",
                         tiktok_description: str = "", tiktok_hashtags=None,
                         watermark=None, language: Language = Language.ENGLISH, id=""):
        """
        Create a QuizVideoEngine with auto-generated script from a topic.
        
        Args:
            voiceModule: Voice synthesis module for audio generation
            topic: Subject/theme for the quiz (e.g., "Geography", "Space Facts", "Movie Trivia")
            num_questions: Number of quiz questions to generate (1-5 recommended)
            difficulty: Difficulty level - "easy", "medium", "hard", "expert"
            style: Style of quiz - "engaging", "educational", "fun", "challenging"
            target_duration: Target video duration in seconds
            intro_text: Custom intro text (if empty, will be auto-generated based on topic)
            intro_duration: Duration of intro animation in seconds
            video_source: Source for background video - "pexels" or "asset_library"
            background_video_asset: Name of asset from library if using asset_library source
            use_sound_effects: Enable sound effects
            intro_sound_asset: Asset name for intro sound effect
            countdown_sound_asset: Asset name for countdown sound effect
            answer_sound_asset: Asset name for answer ding sound effect
            auto_upload_tiktok: Automatically upload to TikTok after video generation
            tiktok_title: Title for TikTok upload (auto-generated if empty)
            tiktok_description: Description for TikTok upload (auto-generated if empty)
            tiktok_hashtags: List of hashtags for TikTok upload
            watermark: Optional watermark text
            language: Language for the quiz
            id: Optional unique identifier for the video
            
        Returns:
            QuizVideoEngine instance with auto-generated compelling script
        """
        
        print(f"🎬🤖 Creating quiz video from topic: '{topic}'")
        print(f"   📊 {num_questions} {difficulty} questions, {style} style")
        print(f"   ⏱️  Target duration: {target_duration:.1f}s")
        
        # Generate compelling script using LLM
        try:
            quiz_script = QuizScriptGenerator.generate_quiz_script(
                topic=topic,
                num_questions=num_questions,
                difficulty=difficulty,
                style=style,
                target_duration=target_duration
            )
            
            print(f"✅ Quiz script generated successfully!")
            print(f"   📝 Script: {quiz_script}")
            
            # Auto-generate intro text if not provided
            if not intro_text:
                intro_text = cls._generate_intro_text(topic, style, difficulty)
                print(f"💫 Auto-generated intro: '{intro_text}'")
            
            # Auto-generate TikTok metadata if not provided
            if auto_upload_tiktok:
                if not tiktok_title:
                    tiktok_title = cls._generate_tiktok_title(topic, difficulty, style)
                if not tiktok_description:
                    tiktok_description = cls._generate_tiktok_description(topic, difficulty, style, num_questions)
                if not tiktok_hashtags:
                    tiktok_hashtags = cls._generate_tiktok_hashtags(topic, difficulty, style)
                
                print(f"📱 Auto-generated TikTok metadata:")
                print(f"   📝 Title: {tiktok_title}")
                print(f"   💬 Description: {tiktok_description[:50]}...")
                print(f"   #️⃣  Hashtags: {', '.join(tiktok_hashtags[:5])}")
            
            # Create and return the QuizVideoEngine instance
            return cls(
                voiceModule=voiceModule,
                quiz_script=quiz_script,
                intro_text=intro_text,
                intro_duration=intro_duration,
                video_source=video_source,
                background_video_asset=background_video_asset,
                use_sound_effects=use_sound_effects,
                intro_sound_asset=intro_sound_asset,
                countdown_sound_asset=countdown_sound_asset,
                answer_sound_asset=answer_sound_asset,
                auto_upload_tiktok=auto_upload_tiktok,
                tiktok_title=tiktok_title,
                tiktok_description=tiktok_description,
                tiktok_hashtags=tiktok_hashtags,
                watermark=watermark,
                language=language,
                id=id
            )
            
        except Exception as e:
            print(f"❌ Error generating script for topic '{topic}': {e}")
            print("📝 Using fallback script generation...")
            
            # Create a simple fallback script
            fallback_script = cls._create_simple_fallback_script(topic, target_duration)
            fallback_intro = f"🧠 {topic.upper()} CHALLENGE! 🧠"
            
            return cls(
                voiceModule=voiceModule,
                quiz_script=fallback_script,
                intro_text=fallback_intro,
                intro_duration=intro_duration,
                video_source=video_source,
                background_video_asset=background_video_asset,
                use_sound_effects=use_sound_effects,
                intro_sound_asset=intro_sound_asset,
                countdown_sound_asset=countdown_sound_asset,
                answer_sound_asset=answer_sound_asset,
                auto_upload_tiktok=auto_upload_tiktok,
                tiktok_title=tiktok_title or f"{topic} Quiz Challenge",
                tiktok_description=tiktok_description or f"Test your {topic} knowledge!",
                tiktok_hashtags=tiktok_hashtags or [topic.replace(" ", ""), "quiz", "challenge"],
                watermark=watermark,
                language=language,
                id=id
            )
    
    @staticmethod
    def _generate_intro_text(topic: str, style: str, difficulty: str) -> str:
        """Generate compelling intro text based on topic and style"""
        
        style_prefixes = {
            "engaging": ["🎯", "⚡", "🔥"],
            "educational": ["🧠", "📚", "🎓"], 
            "fun": ["🎉", "😄", "🎊"],
            "challenging": ["💀", "⚔️", "🏆"]
        }
        
        style_suffixes = {
            "engaging": ["QUIZ", "TEST", "CHALLENGE"],
            "educational": ["FACTS", "KNOWLEDGE", "LEARNING"],
            "fun": ["FUN", "PARTY", "GAME"],
            "challenging": ["CHALLENGE", "ULTIMATE TEST", "EXPERT LEVEL"]
        }
        
        prefix = style_prefixes.get(style, ["🎯"])[0]
        suffix = style_suffixes.get(style, ["QUIZ"])[0]
        
        return f"{topic.upper()} {difficulty} {suffix}!"
    
    @staticmethod
    def _generate_tiktok_title(topic: str, difficulty: str, style: str) -> str:
        """Generate compelling TikTok title"""
        
        difficulty_words = {
            "easy": ["Fun", "Quick", "Simple"],
            "medium": ["Challenging", "Test Your", "Can You Answer"],
            "hard": ["Ultimate", "Expert Level", "Mind-Bending"],
            "expert": ["Impossible", "Genius Level", "Master"]
        }
        
        style_words = {
            "engaging": ["Challenge", "Quiz", "Test"],
            "educational": ["Facts", "Knowledge", "Learning"],
            "fun": ["Game", "Trivia", "Fun Quiz"],
            "challenging": ["Ultimate Test", "Expert Challenge", "Brain Teaser"]
        }
        
        difficulty_word = difficulty_words.get(difficulty, ["Challenging"])[0]
        style_word = style_words.get(style, ["Quiz"])[0]
        
        return f"{difficulty_word} {topic} {style_word}!"
    
    @staticmethod
    def _generate_tiktok_description(topic: str, difficulty: str, style: str, num_questions: int) -> str:
        """Generate compelling TikTok description"""
        
        base_description = f"🧠 Think you know {topic}? Test yourself with these {difficulty} questions!\n\n"
        
        if style == "educational":
            base_description += f"📚 Learn fascinating {topic} facts while challenging your knowledge! "
        elif style == "fun":
            base_description += f"🎉 Have fun while testing your {topic} skills! "
        elif style == "challenging":
            base_description += f"💀 Only true {topic} experts can get these right! "
        else:
            base_description += f"🎯 How well do you really know {topic}? "
        
        base_description += f"\n\n💬 Comment your score out of {num_questions}!\n"
        base_description += f"🔔 Follow for more mind-blowing quizzes!\n"
        base_description += f"📲 Download WITZ for unlimited quiz challenges!"
        
        return base_description
    
    @staticmethod
    def _generate_tiktok_hashtags(topic: str, difficulty: str, style: str) -> List[str]:
        """Generate relevant TikTok hashtags"""
        
        hashtags = []
        
        # Topic-based hashtags
        topic_clean = topic.replace(" ", "").lower()
        hashtags.extend([topic_clean, f"{topic_clean}facts", f"{topic_clean}quiz"])
        
        # Difficulty hashtags
        difficulty_tags = {
            "easy": ["easyquiz", "beginners", "funfacts"],
            "medium": ["quiz", "challenge", "brainteaser"],
            "hard": ["hardquiz", "expertlevel", "mindchallenge"],
            "expert": ["impossiblequiz", "geniuslevel", "braingame"]
        }
        hashtags.extend(difficulty_tags.get(difficulty, ["quiz", "challenge"]))
        
        # Style hashtags
        style_tags = {
            "engaging": ["viral", "trending", "mustwatch"],
            "educational": ["learnontiktok", "education", "facts"],
            "fun": ["funny", "entertainment", "gameshow"],
            "challenging": ["difficult", "brainy", "smartpeople"]
        }
        hashtags.extend(style_tags.get(style, ["quiz"]))
        
        # General hashtags
        hashtags.extend([
            "quiz", "trivia", "challenge", "test", "knowledge",
            "braingame", "questions", "viral", "fyp", "foryoupage",
            "smartquiz", "witz", "quiztime", "brainchallenge"
        ])
        
        # Remove duplicates and limit to reasonable number
        unique_hashtags = list(dict.fromkeys(hashtags))[:15]
        
        return unique_hashtags
    
    @staticmethod 
    def _create_simple_fallback_script(topic: str, duration: float) -> str:
        """Create a simple fallback script if LLM generation completely fails"""
        return f"""[0.0-2.0] ANSWER: Ready for an amazing {topic} challenge?
[2.0-4.5] QUESTION: Can you answer this {topic} question?
[4.5-6.0] COUNTDOWN: 3-2-1
[6.0-8.5] ANSWER: Great job! That's an interesting {topic} fact!
[8.5-10.5] CTA: Like if you learned something new!
[10.5-12.0] CTA: Follow for more {topic} content!"""

    def makeContent(self):
        """
        Override makeContent to add TikTok upload functionality after video generation
        """
        # Call parent makeContent generator
        for step_num, step_info in super().makeContent():
            yield step_num, step_info
        
        # After video generation is complete, upload to TikTok if enabled
        if self._auto_upload_tiktok and self.isShortDone():
            yield "TikTok", "Uploading video to TikTok..."
            try:
                upload_result = self.upload_to_tiktok()
                if upload_result["success"]:
                    yield "TikTok", f"✅ TikTok upload successful! Video ID: {upload_result['video_id']}"
                else:
                    yield "TikTok", f"❌ TikTok upload failed: {upload_result['error']}"
            except Exception as e:
                yield "TikTok", f"❌ TikTok upload error: {str(e)}"

    def upload_to_tiktok(self, title: str = "", description: str = "", 
                        hashtags: List[str] = None, privacy: str = "PUBLIC_TO_EVERYONE") -> Dict[str, Any]:
        """
        Upload the generated video to TikTok using Business API
        
        Args:
            title: Custom title (uses auto-generated if empty)
            description: Custom description (uses auto-generated if empty)
            hashtags: Custom hashtags (uses auto-generated if empty)
            privacy: Privacy level for the video
            
        Returns:
            Dict containing upload result and metadata
        """
        
        if not self.isShortDone():
            return {
                "success": False,
                "error": "Video generation not complete yet",
                "video_id": None
            }
        
        video_path = self.get_video_output_path()
        if not video_path or not os.path.exists(video_path):
            return {
                "success": False,
                "error": f"Video file not found: {video_path}",
                "video_id": None
            }
        
        print(f"📱 Uploading quiz video to TikTok...")
        print(f"   🎬 Video: {os.path.basename(video_path)}")
        
        try:
            # Initialize TikTok uploader if not already done
            if not self._tiktok_uploader:
                self._tiktok_uploader = TikTokBusinessUploader()
                
                # Test connection first
                if not self._tiktok_uploader.test_connection():
                    return {
                        "success": False,
                        "error": "TikTok API connection failed. Check credentials.",
                        "video_id": None
                    }
            
            # Use provided metadata or fall back to auto-generated
            final_title = title or self._tiktok_title
            final_description = description or self._tiktok_description
            final_hashtags = hashtags or self._tiktok_hashtags
            
            # Create upload configuration
            upload_config = TikTokUploadConfig.create_upload_config(
                video_title=final_title,
                video_description=final_description,
                privacy=privacy,
                hashtags=final_hashtags,
                disable_comments=False,


            )
            
            print(f"   📝 Title: {final_title}")
            print(f"   💬 Description: {final_description[:50]}...")
            print(f"   #️⃣  Hashtags: {', '.join(final_hashtags[:5])}")
            
            # Upload the video
            upload_result = self._tiktok_uploader.upload_video(
                video_path=video_path,
                config=upload_config,
                max_retries=3
            )
            
            return upload_result
            
        except Exception as e:
            print(f"❌ TikTok upload exception: {e}")
            return {
                "success": False,
                "error": f"Upload exception: {str(e)}",
                "video_id": None
            }
    
    def check_tiktok_upload_status(self, video_id: str) -> Dict[str, Any]:
        """Check the status of a TikTok video upload"""
        
        try:
            if not self._tiktok_uploader:
                self._tiktok_uploader = TikTokBusinessUploader()
            
            return self._tiktok_uploader.get_upload_status(video_id)
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Status check exception: {str(e)}",
                "status": "error"
            }
    
    def set_tiktok_credentials(self, advertiser_id: str, access_token: str):
        """Set TikTok API credentials"""
        
        self._tiktok_uploader = TikTokBusinessUploader(
            advertiser_id=advertiser_id,
            access_token=access_token
        )

    def _setupSoundEffects(self):
        """
        Setup sound effects for quiz video. Creates default sound effects if custom ones aren't provided.
        """
        import os
        
        # Create sound effects directory if it doesn't exist
        sound_effects_dir = os.path.join(self.dynamicAssetDir, "sound_effects")
        os.makedirs(sound_effects_dir, exist_ok=True)
        
        # Setup intro sound (attention-grabbing whoosh/pop)
        if not self._intro_sound_asset:
            self._intro_sound_path = self._generateIntroSound(sound_effects_dir)
        else:
            try:
                self._intro_sound_path = AssetDatabase.get_asset_link(self._intro_sound_asset)
            except ValueError:
                print(f"Intro sound asset '{self._intro_sound_asset}' not found, generating default...")
                self._intro_sound_path = self._generateIntroSound(sound_effects_dir)
        
        # Setup countdown sound (tick/beep)
        if not self._countdown_sound_asset:
            self._countdown_sound_path = self._generateCountdownSound(sound_effects_dir)
        else:
            try:
                self._countdown_sound_path = AssetDatabase.get_asset_link(self._countdown_sound_asset)
            except ValueError:
                print(f"Countdown sound asset '{self._countdown_sound_asset}' not found, generating default...")
                self._countdown_sound_path = self._generateCountdownSound(sound_effects_dir)
        
        # Setup answer ding sound (success/correct chime)
        if not self._answer_sound_asset:
            self._answer_sound_path = self._generateAnswerSound(sound_effects_dir)
        else:
            try:
                self._answer_sound_path = AssetDatabase.get_asset_link(self._answer_sound_asset)
            except ValueError:
                print(f"Answer sound asset '{self._answer_sound_asset}' not found, generating default...")
                self._answer_sound_path = self._generateAnswerSound(sound_effects_dir)

    def _generateIntroSound(self, sound_dir: str) -> str:
        """Generate a captivating intro sound effect using FFmpeg."""
        import subprocess
        
        intro_sound_path = os.path.join(sound_dir, "intro_sound.wav")
        if os.path.exists(intro_sound_path):
            return intro_sound_path
            
        try:
            # Create an attention-grabbing whoosh sound with rising pitch
            subprocess.run([
                'ffmpeg', '-loglevel', 'error', '-y',
                '-f', 'lavfi',
                '-i', 'sine=frequency=220:duration=0.8',
                '-af', 'aeval=val(0)*sin(2*PI*t*220*(1+0.5*t)):c=same,volume=1',
                '-ar', '44100',
                intro_sound_path
            ], check=True)
            print(f"✅ Generated intro sound: {intro_sound_path}")
            return intro_sound_path
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to generate intro sound: {e}")
            return None

    def _generateCountdownSound(self, sound_dir: str) -> str:
        """Generate a countdown tick sound effect using FFmpeg."""
        import subprocess
        
        countdown_sound_path = os.path.join(sound_dir, "countdown_tick.wav")
        if os.path.exists(countdown_sound_path):
            return countdown_sound_path
            
        try:
            # Create a sharp tick sound (short high-pitched beep)
            subprocess.run([
                'ffmpeg', '-loglevel', 'error', '-y',
                '-f', 'lavfi',
                '-i', 'sine=frequency=800:duration=0.15',
                '-af', 'aeval=val(0)*exp(-t*8),volume=1',
                '-ar', '44100',
                countdown_sound_path
            ], check=True)
            print(f"✅ Generated countdown sound: {countdown_sound_path}")
            return countdown_sound_path
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to generate countdown sound: {e}")
            return None

    def _generateAnswerSound(self, sound_dir: str) -> str:
        """Generate a correct answer ding sound effect using FFmpeg."""
        import subprocess
        
        answer_sound_path = os.path.join(sound_dir, "answer_ding.wav")
        if os.path.exists(answer_sound_path):
            return answer_sound_path
            
        try:
            # Create a pleasant ding sound (two-tone chime)
            subprocess.run([
                'ffmpeg', '-loglevel', 'error', '-y',
                '-f', 'lavfi',
                '-i', 'sine=frequency=523:duration=0.4',  # C5 note
                '-f', 'lavfi',
                '-i', 'sine=frequency=659:duration=0.6',  # E5 note
                '-filter_complex', '[0]volume=1,adelay=0[a1];[1]volume=1,adelay=200[a2];[a1][a2]amix=inputs=2,volume=1',
                '-ar', '44100',
                answer_sound_path
            ], check=True)
            print(f"✅ Generated answer ding: {answer_sound_path}")
            return answer_sound_path
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to generate answer ding: {e}")
            return None

    def _addSoundEffectsToMix(self, audio_inputs: list, filter_parts: list, input_index: int) -> int:
        """
        Add sound effects to the audio mixing process.
        
        Args:
            audio_inputs: List of audio file paths to mix
            filter_parts: List of filter strings for FFmpeg
            input_index: Current input index for FFmpeg
            
        Returns:
            Updated input_index after adding sound effects
        """
        components = self._db_quiz_components
        all_components = components.get('all_components', [])
        
        for component in all_components:
            component_type = component['type']
            start_time = component['start_time']
            
            # Add intro sound effect
            if component_type == 'intro' and hasattr(self, '_intro_sound_path') and self._intro_sound_path:
                audio_inputs.append(self._intro_sound_path)
                delay_ms = int(start_time * 1000)
                filter_parts.append(f"[{input_index}:a]volume=0.7,adelay={delay_ms}|{delay_ms}[a{input_index}]")
                input_index += 1
                print(f"🔊 Added intro sound effect at {start_time:.1f}s")
            
            # Add countdown sound effects (one for each number: 3, 2, 1)
            elif component_type == 'countdown' and hasattr(self, '_countdown_sound_path') and self._countdown_sound_path:
                duration = component['end_time'] - start_time
                segment_duration = duration / 3
                
                # Add tick sound for each countdown number
                for i in range(3):
                    segment_start = start_time + (i * segment_duration)
                    audio_inputs.append(self._countdown_sound_path)
                    delay_ms = int(segment_start * 1000)
                    filter_parts.append(f"[{input_index}:a]volume=0.7,adelay={delay_ms}|{delay_ms}[a{input_index}]")
                    input_index += 1
                
                print(f"🔊 Added countdown sound effects at {start_time:.1f}s")
            
            # Add answer ding sound effect
            elif component_type == 'answer' and hasattr(self, '_answer_sound_path') and self._answer_sound_path:
                audio_inputs.append(self._answer_sound_path)
                delay_ms = int(start_time * 1000)
                filter_parts.append(f"[{input_index}:a]volume=0.7,adelay={delay_ms}|{delay_ms}[a{input_index}]")
                input_index += 1
                print(f"🔊 Added answer ding at {start_time:.1f}s")
        
        return input_index

    def _generateVideoUrls(self):
        """
        Override to support different video sources: Pexels API or Asset Library.
        Uses random crop for longer background videos.
        """
        if self._video_source == "asset_library" and self._background_video_asset:
            # Use specific asset from library
            try:
                video_url = AssetDatabase.get_asset_link(self._background_video_asset)
                print(f"Using asset library video: {self._background_video_asset} -> {video_url}")
                
                # Get video duration and quiz duration for random cropping
                video_duration = self._get_background_video_duration()
                quiz_duration = self._get_quiz_duration()
                
                # Calculate random segment timing for source video
                source_start_time, source_end_time = self._calculate_video_timing(video_duration, quiz_duration)
                
                print(f"Background video: {video_duration:.1f}s total, using {source_start_time:.1f}s - {source_end_time:.1f}s")
                
                # Extract the random video segment if needed
                final_video_url = self._extract_video_segment(video_url, source_start_time, source_end_time)
                
                # Create timed video URL list with TIMELINE positions (always start from 0)
                # Use the calculated duration from the video timing
                actual_duration = source_end_time - source_start_time
                self._db_timed_video_urls = [[[0.0, actual_duration], final_video_url]]
                
            except ValueError as e:
                print(f"Asset '{self._background_video_asset}' not found in library: {e}")
                print("Falling back to Pexels...")
                self._video_source = "pexels"
                super()._generateVideoUrls()
        else:
            # Use Pexels (default behavior)
            super()._generateVideoUrls()

    def _get_background_video_duration(self) -> float:
        """
        Get the duration of the background video asset.
        
        Returns:
            float: Duration in seconds
        """
        try:
            duration = AssetDatabase.get_asset_duration(self._background_video_asset)
            return float(duration) if duration else 0.0
        except Exception as e:
            print(f"Warning: Could not get duration for {self._background_video_asset}: {e}")
            return 0.0

    def _get_quiz_duration(self) -> float:
        """
        Calculate the total duration of the quiz.
        
        Returns:
            float: Total quiz duration in seconds
        """
        total_duration = 0.0
        
        # Use enhanced multi-component structure if available
        components = self._db_quiz_components
        all_components = components.get('all_components', [])
        
        if all_components:
            # Get the end time of the last component
            for component in all_components:
                if component.get('end_time', 0) > total_duration:
                    total_duration = component['end_time']
        else:
            # Fallback to old structure for backward compatibility
            for component_type, component_data in components.items():
                if component_data and isinstance(component_data, dict) and 'end_time' in component_data:
                    if component_data['end_time'] > total_duration:
                        total_duration = component_data['end_time']
        
        return total_duration

    def _calculate_video_timing(self, video_duration: float, quiz_duration: float) -> tuple[float, float]:
        """
        Calculate start and end times for background video, using random crop if video is longer.
        
        Args:
            video_duration: Total duration of background video in seconds
            quiz_duration: Duration of quiz in seconds
            
        Returns:
            tuple: (start_time, end_time) in seconds
        """
        # Handle case where quiz duration is not calculated yet (fallback to reasonable default)
        if quiz_duration <= 0:
            print(f"Quiz duration not available ({quiz_duration:.1f}s), using default 30s segment")
            quiz_duration = 30.0  # Default quiz duration
        
        # If video is shorter than or equal to quiz, use entire video
        if video_duration <= quiz_duration or video_duration == 0.0:
            print(f"Background video ({video_duration:.1f}s) <= quiz duration ({quiz_duration:.1f}s), using full video")
            return 0.0, video_duration if video_duration > 0 else quiz_duration
        
        # Video is longer than quiz - use random crop
        import random
        
        # Ensure we have enough buffer (don't start too close to the end)
        max_start_time = video_duration - quiz_duration
        
        # Add some safety margin (10% of video duration or 5 seconds, whichever is smaller)
        safety_margin = min(video_duration * 0.1, 5.0)
        max_start_time = max(0, max_start_time - safety_margin)
        
        # Generate random start time
        start_time = random.uniform(0, max_start_time) if max_start_time > 0 else 0
        end_time = start_time + quiz_duration
        
        print(f"Random crop: video {video_duration:.1f}s -> using segment {start_time:.1f}s to {end_time:.1f}s")
        
        return start_time, end_time

    def _get_background_video_timing(self, video_url: str, quiz_duration: float) -> tuple[float, float]:
        """
        Get the timing for background video in the final timeline.
        Always returns 0.0 to quiz_duration for proper timeline positioning.
        
        Args:
            video_url: URL of the background video
            quiz_duration: Duration of the quiz
            
        Returns:
            tuple: (timeline_start, timeline_end) - always starts from 0.0
        """
        # Background video should always cover the full quiz timeline starting from 0.0
        timeline_start = 0.0
        timeline_end = quiz_duration
        
        print(f"Background video timeline timing: {timeline_start:.1f}s - {timeline_end:.1f}s")
        
        return timeline_start, timeline_end

    def _extract_video_segment(self, video_url: str, start_time: float, end_time: float) -> str:
        """
        Extract a segment from the background video using FFmpeg.
        
        Args:
            video_url: Original video URL
            start_time: Start time in seconds
            end_time: End time in seconds
            
        Returns:
            str: Path to the extracted video segment
        """
        import subprocess
        import os
        
        # If start_time is 0 and we're using the full duration, no need to extract
        duration = end_time - start_time
        if start_time == 0.0:
            print(f"Using full video from start (no extraction needed)")
            return video_url
        
        # Create output filename in the dynamic asset directory
        output_filename = f"background_segment_{start_time:.1f}s-{end_time:.1f}s.mp4"
        output_path = os.path.join(self.dynamicAssetDir, output_filename)
        
        # Remove existing file if it exists
        if os.path.exists(output_path):
            os.remove(output_path)
        
        print(f"Extracting video segment: {start_time:.1f}s - {end_time:.1f}s ({duration:.1f}s)")
        
        # FFmpeg command to extract and re-mux segment with safe container flags
        command = ['ffmpeg', '-loglevel', 'error']
        # If remote HTTP(S) source (e.g., googlevideo), make HTTP robust and disable connection reuse
        if isinstance(video_url, str) and video_url.startswith('http'):
            command += [
                '-protocol_whitelist', 'file,http,https,tcp,tls',
                '-reconnect', '1',
                '-reconnect_streamed', '1',
                '-reconnect_delay_max', '2',
                '-http_persistent', '0',
            ]
        command += [
            '-ss', str(start_time),            # Start time
            '-t', str(duration),               # Duration
            '-i', video_url,                   # Input video
            '-c:v', 'libx264',                 # Re-encode video for consistency
            '-preset', 'ultrafast',            # Fast encoding
            '-movflags', '+faststart',         # Write moov atom at beginning
            '-pix_fmt', 'yuv420p',             # Broad compatibility
            '-avoid_negative_ts', 'make_zero', # Handle timing issues
            '-y',                              # Overwrite output file
            output_path
        ]
        
        try:
            print(f"Running FFmpeg extraction...")
            subprocess.run(command, check=True, timeout=120)
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                # Validate with ffprobe; otherwise try fallback to local full download then segment again
                try:
                    probe = subprocess.run([
                        'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                        '-of', 'default=nw=1:nk=1', output_path
                    ], capture_output=True, text=True, check=True)
                    duration_str = probe.stdout.strip()
                    if duration_str and float(duration_str) > 0.1:
                        print(f"✅ Video segment extracted: {output_path} ({float(duration_str):.1f}s)")
                        return output_path
                except Exception:
                    pass
                # Fallback path: download full to local then cut locally
                print("⚠️  Extracted remote segment invalid. Attempting full local download then cut...")
                local_full = self._download_full_video(video_url)
                if local_full and os.path.exists(local_full):
                    try:
                        local_segment = os.path.join(self.dynamicAssetDir, f"background_segment_local_{start_time:.1f}s-{end_time:.1f}s.mp4")
                        if os.path.exists(local_segment):
                            os.remove(local_segment)
                        subprocess.run([
                            'ffmpeg','-loglevel','error',
                            '-ss', str(start_time), '-t', str(duration), '-i', local_full,
                            '-c:v','libx264','-preset','ultrafast','-movflags','+faststart','-pix_fmt','yuv420p','-y', local_segment
                        ], check=True)
                        # Validate
                        probe2 = subprocess.run([
                            'ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1', local_segment
                        ], capture_output=True, text=True, check=True)
                        d2 = probe2.stdout.strip()
                        if d2 and float(d2) > 0.1:
                            print(f"✅ Local segment extracted: {local_segment} ({float(d2):.1f}s)")
                            return local_segment
                    except Exception:
                        print("⚠️  Local segment cut failed; will fall back to local full video.")
                        return local_full
                # As last resort, use original URL
                print("⚠️  Falling back to original video URL.")
                return video_url
            else:
                print(f"⚠️  Extraction failed, using original video")
                # Try local full download as a fallback
                local_full = self._download_full_video(video_url)
                if local_full and os.path.exists(local_full):
                    return local_full
                return video_url
                
        except subprocess.CalledProcessError as e:
            print(f"⚠️  FFmpeg extraction failed: {e}")
            # Try local full download as a robust fallback for remote sources
            local_full = self._download_full_video(video_url)
            if local_full and os.path.exists(local_full):
                return local_full
            print(f"Falling back to original video")
            return video_url
        except subprocess.TimeoutExpired:
            print(f"⚠️  FFmpeg extraction timed out")
            local_full = self._download_full_video(video_url)
            if local_full and os.path.exists(local_full):
                return local_full
            print(f"Falling back to original video")
            return video_url

    def _download_full_video(self, video_url: str) -> str | None:
        """
        Download the full remote video to a local MP4 file to avoid HTTP streaming issues.
        Returns the local file path if successful, otherwise None.
        """
        import subprocess
        import os
        if not isinstance(video_url, str) or not video_url.startswith('http'):
            return None
        local_path = os.path.join(self.dynamicAssetDir, 'background_full.mp4')
        try:
            if os.path.exists(local_path):
                os.remove(local_path)
            cmd = [
                'ffmpeg','-loglevel','error',
                '-protocol_whitelist','file,http,https,tcp,tls',
                '-reconnect','1','-reconnect_streamed','1','-reconnect_delay_max','2',
                '-http_persistent','0',
                '-i', video_url,
                '-c:v','libx264','-preset','ultrafast','-movflags','+faststart','-pix_fmt','yuv420p','-y', local_path
            ]
            print("Downloading full background video locally to avoid HTTP issues...")
            subprocess.run(cmd, check=True, timeout=300)
            if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
                print(f"✅ Downloaded local background video: {local_path}")
                return local_path
        except Exception as e:
            print(f"⚠️  Full video download failed: {e}")
        return None

    def _parse_quiz_script(self, quiz_script: str) -> Dict[str, Any]:
        """
        Parse the time-stamped quiz script into structured components.
        
        Enhanced to support multiple questions, countdowns, answers, and CTAs.
        
        Expected format:
        [0.0-1.5] ANSWER: Ready for a new geo quiz?
        [1.5-3.0] QUESTION: What is the capital of France?
        [3.0-4.5] COUNTDOWN: 3-2-1
        [4.5-6.0] ANSWER: Paris! Amazing, right?
        [6.0-7.5] QUESTION: What is the capital of Italy?
        [7.5-9.0] COUNTDOWN: 3-2-1
        [9.0-10.5] ANSWER: Rome! Amazing, right?
        [15.0-18.0] CTA: Like if you learned something new!
        
        Args:
            quiz_script: Raw quiz script with timestamps
            
        Returns:
            Dictionary with parsed quiz components and timings
        """
        components = {
            'all_components': [],  # List of all components in order
            'questions': [],       # List of all questions
            'countdowns': [],      # List of all countdowns
            'answers': [],         # List of all answers
            'ctas': [],           # List of all CTAs
            'raw_script': quiz_script
        }
        
        lines = quiz_script.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Extract timestamp and content using regex
            timestamp_match = re.match(r'\[(\d+\.?\d*)-(\d+\.?\d*)\]\s*(\w+):\s*(.+)', line)
            if timestamp_match:
                start_time = float(timestamp_match.group(1))
                end_time = float(timestamp_match.group(2))
                component_type = timestamp_match.group(3).lower()
                content = timestamp_match.group(4)
                
                component = {
                    'start_time': start_time,
                    'end_time': end_time,
                    'content': content,
                    'type': component_type
                }
                
                # Add to appropriate lists
                components['all_components'].append(component)
                
                if component_type == 'question':
                    components['questions'].append(component)
                elif component_type == 'countdown':
                    components['countdowns'].append(component)
                elif component_type == 'answer':
                    components['answers'].append(component)
                elif component_type == 'cta':
                    components['ctas'].append(component)
        
        # Add intro animation if specified
        if self._intro_text and self._intro_duration > 0:
            # Shift all existing components by intro duration
            for component in components['all_components']:
                component['start_time'] += self._intro_duration
                component['end_time'] += self._intro_duration
            
            # Add intro component at the beginning
            intro_component = {
                'start_time': 0.0,
                'end_time': self._intro_duration,
                'content': self._intro_text,
                'type': 'intro'
            }
            components['all_components'].insert(0, intro_component)
            components['intro'] = intro_component
        
        # Sort all components by start time
        components['all_components'].sort(key=lambda x: x['start_time'])
        
        # For backward compatibility, keep the old format for single-question quizzes
        if len(components['questions']) == 1 and len(components['countdowns']) == 1 and len(components['answers']) == 1:
            components['question'] = components['questions'][0]
            components['countdown'] = components['countdowns'][0] 
            components['answer'] = components['answers'][0]
            if components['ctas']:
                components['cta'] = components['ctas'][0]
        
        return components

    def _generateCountdownSegments(self) -> List[Tuple[float, float, str]]:
        """
        Generate individual countdown segments (3, 2, 1) with precise timing.
        
        Returns:
            List of tuples with (start_time, end_time, number) for each countdown number
        """
        countdown_info = self._db_quiz_components.get('countdown')
        if not countdown_info:
            return []
        
        start_time = countdown_info['start_time']
        end_time = countdown_info['end_time']
        duration = end_time - start_time
        
        # Split countdown duration into 3 equal segments
        segment_duration = duration / 3
        
        countdown_segments = []
        for i, number in enumerate(['3', '2', '1']):
            segment_start = start_time + (i * segment_duration)
            segment_end = start_time + ((i + 1) * segment_duration)
            countdown_segments.append((segment_start, segment_end, number))
        
        return countdown_segments

    def _generateCountdownSegmentsForComponent(self, countdown_component: Dict[str, Any]) -> List[Tuple[float, float, str]]:
        """
        Generate individual countdown segments (3, 2, 1) for a specific countdown component.
        
        Args:
            countdown_component: Dictionary with countdown component info
            
        Returns:
            List of tuples with (start_time, end_time, number) for each countdown number
        """
        start_time = countdown_component['start_time']
        end_time = countdown_component['end_time']
        duration = end_time - start_time
        
        # Split countdown duration into 3 equal segments
        segment_duration = duration / 3
        
        countdown_segments = []
        for i, number in enumerate(['3', '2', '1']):
            segment_start = start_time + (i * segment_duration)
            segment_end = start_time + ((i + 1) * segment_duration)
            countdown_segments.append((segment_start, segment_end, number))
        
        return countdown_segments

    def _editAndRenderShort(self):
        """
        Override the rendering method to add quiz-specific editing steps with precise audio timing.
        """
        self.verifyParameters(voiceover_audio_url=self._db_audio_path)

        outputPath = self.dynamicAssetDir + "rendered_video.mp4"
        if not os.path.exists(outputPath):
            self.logger("Rendering quiz video: Starting automated editing...")
            videoEditor = EditingEngine()
            
            # Create a composite audio track with all components properly timed
            composite_audio_path = self._createCompositeAudioTrack()
            
            # Add the composite audio as the main voiceover
            videoEditor.addEditingStep(EditingStep.ADD_VOICEOVER_AUDIO, {
                'url': composite_audio_path
            })
            
            # Add background video for the entire quiz duration
            if self._db_timed_video_urls:
                # Use the first video but extend it to cover the entire quiz duration
                _, first_video_url = self._db_timed_video_urls[0]
                
                # Calculate total quiz duration from all components
                total_duration = 0.0
                components = self._db_quiz_components
                all_components = components.get('all_components', [])
                
                # Use the new all_components structure
                for component in all_components:
                    if component and isinstance(component, dict) and 'end_time' in component:
                        if component['end_time'] > total_duration:
                            total_duration = component['end_time']
                
                # Fallback to old structure for backward compatibility
                if total_duration == 0.0:
                    for component_type, component_data in components.items():
                        if component_data and isinstance(component_data, dict) and 'end_time' in component_data:
                            if component_data['end_time'] > total_duration:
                                total_duration = component_data['end_time']
                
                print(f"Adding background video for full duration: {total_duration:.1f}s")
                
                # Get background video timing (handles random crop for longer videos)
                bg_start, bg_end = self._get_background_video_timing(first_video_url, total_duration)
                
                # Add background video with calculated timing
                videoEditor.addEditingStep(EditingStep.ADD_BACKGROUND_VIDEO, {
                    'url': first_video_url,
                    'set_time_start': bg_start,
                    'set_time_end': bg_end
                })
            
            # Add text overlays for all components (questions, answers, CTAs)
            components = self._db_quiz_components
            all_components = components.get('all_components', [])
            
            for component in all_components:
                component_type = component['type']
                
                if component_type == 'intro':
                    videoEditor.addEditingStep(EditingStep.ADD_INTRO_ANIMATION, {
                        'text': component['content'].upper(),
                        'set_time_start': component['start_time'],
                        'set_time_end': component['end_time']
                    })
                elif component_type == 'question':
                    videoEditor.addEditingStep(EditingStep.ADD_QUIZ_QUESTION, {
                        'text': component['content'].upper(),
                        'set_time_start': component['start_time'],
                        'set_time_end': component['end_time']
                    })
                elif component_type == 'answer':
                    videoEditor.addEditingStep(EditingStep.ADD_QUIZ_ANSWER, {
                        'text': component['content'],
                        'set_time_start': component['start_time'],
                        'set_time_end': component['end_time']
                    })
                elif component_type == 'cta':
                    videoEditor.addEditingStep(EditingStep.ADD_QUIZ_CTA, {
                        'text': component['content'].upper(),
                        'set_time_start': component['start_time'],
                        'set_time_end': component['end_time']
                    })
                elif component_type == 'countdown':
                    # Handle countdown overlays with individual number segments
                    countdown_segments = self._generateCountdownSegmentsForComponent(component)
                    for start_time, end_time, number in countdown_segments:
                        videoEditor.addEditingStep(EditingStep.ADD_COUNTDOWN_OVERLAY, {
                            'text': number,
                            'set_time_start': start_time,
                            'set_time_end': end_time
                        })
            
            # Add watermark if provided
            if self._db_watermark:
                videoEditor.addEditingStep(EditingStep.ADD_WATERMARK, {
                    'text': self._db_watermark
                })
            
            # Render the final video
            videoEditor.renderVideo(outputPath, logger=self.logger if self.logger is not self.default_logger else None)

        self._db_video_path = outputPath

    def _createCompositeAudioTrack(self) -> str:
        """
        Create a composite audio track with all quiz components at their proper times.
        
        This creates a single audio file that spans the entire video duration,
        with each component audio placed at the exact specified timing.
        
        Returns:
            Path to the composite audio file
        """
        import subprocess
        import os
        
        # Calculate total video duration from quiz components
        total_duration = 0.0
        components = self._db_quiz_components
        all_components = components.get('all_components', [])
        
        # Use the new all_components structure
        for component in all_components:
            if component and isinstance(component, dict) and 'end_time' in component:
                if component['end_time'] > total_duration:
                    total_duration = component['end_time']
        
        # Fallback to old structure for backward compatibility
        if total_duration == 0.0:
            for component_type, component_data in components.items():
                if component_data and isinstance(component_data, dict) and 'end_time' in component_data:
                    if component_data['end_time'] > total_duration:
                        total_duration = component_data['end_time']
        
        # Create silent base audio track
        composite_audio_path = self.dynamicAssetDir + "composite_audio.wav"
        silent_audio_path = self.dynamicAssetDir + "silent_base.wav"
        
        # Generate silent audio for the full duration
        subprocess.run([
            'ffmpeg', '-loglevel', 'error', '-y',
            '-f', 'lavfi',
            '-i', f'anullsrc=channel_layout=stereo:sample_rate=44100',
            '-t', str(total_duration),
            silent_audio_path
        ], check=True)
        
        # Start with the silent base
        current_audio = silent_audio_path
        temp_counter = 0
        
        # Add each component audio at its specified time using simultaneous mixing
        if hasattr(self, '_db_component_audio_files'):
            # Collect all audio inputs and delays for simultaneous mixing
            audio_inputs = []
            filter_parts = []
            input_index = 1  # 0 is the silent base
            
            # Sort components by start time
            sorted_components = []
            for component_key, audio_info in self._db_component_audio_files.items():
                sorted_components.append((audio_info['start_time'], component_key, audio_info))
            
            sorted_components.sort(key=lambda x: x[0])
            
            for start_time, component_key, audio_info in sorted_components:
                component_type = audio_info['type']
                
                if component_type == 'countdown':
                    # Handle countdown segments individually - add each 1-second segment
                    countdown_component = audio_info['component']
                    countdown_duration = countdown_component['end_time'] - countdown_component['start_time']
                    segment_duration = countdown_duration / 3
                    
                    # Process each countdown segment (3, 2, 1)
                    for i in range(3):
                        segment_start_time = countdown_component['start_time'] + (i * segment_duration)
                        segment_start_in_audio = i * segment_duration
                        
                        # Create individual countdown segment file
                        countdown_segment_path = self.dynamicAssetDir + f"countdown_segment_{component_key}_{i}.wav"
                        
                        # Extract this segment from the countdown audio
                        subprocess.run([
                            'ffmpeg', '-loglevel', 'error', '-y',
                            '-i', audio_info['path'],
                            '-ss', str(segment_start_in_audio),
                            '-t', str(segment_duration),
                            countdown_segment_path
                        ], check=True)
                        
                        # Add to inputs for mixing
                        audio_inputs.append(countdown_segment_path)
                        delay_ms = int(segment_start_time * 1000)
                        filter_parts.append(f"[{input_index}:a]volume=0.9,adelay={delay_ms}|{delay_ms}[a{input_index}]")
                        input_index += 1
                else:
                    # Add regular component audio
                    audio_inputs.append(audio_info['path'])
                    delay_ms = int(audio_info['start_time'] * 1000)
                    filter_parts.append(f"[{input_index}:a]volume=0.9,adelay={delay_ms}|{delay_ms}[a{input_index}]")
                    input_index += 1
            
            # Add sound effects if enabled
            if self._use_sound_effects:
                input_index = self._addSoundEffectsToMix(audio_inputs, filter_parts, input_index)
            
            # Create ffmpeg command for simultaneous mixing
            if audio_inputs:
                ffmpeg_cmd = ['ffmpeg', '-loglevel', 'error', '-y', '-i', current_audio]
                
                # Add all audio inputs
                for audio_input in audio_inputs:
                    ffmpeg_cmd.extend(['-i', audio_input])
                
                # Build filter complex for simultaneous mixing
                filter_complex = ';'.join(filter_parts)
                
                # Add the amix part - mix the silent base with all delayed components
                amix_inputs = '[0:a]'
                for i in range(1, input_index):
                    amix_inputs += f'[a{i}]'
                
                # Create equal weights for all inputs to prevent volume division
                weights = ' '.join(['1.0'] * input_index)
                filter_complex += f';{amix_inputs}amix=inputs={input_index}:duration=longest:weights={weights}:normalize=0[out]'
                
                ffmpeg_cmd.extend(['-filter_complex', filter_complex, '-map', '[out]', composite_audio_path])
                
                print(f"Mixing {len(audio_inputs)} audio components simultaneously...")
                subprocess.run(ffmpeg_cmd, check=True)
                
                # Clean up temporary countdown segment files
                for i, audio_input in enumerate(audio_inputs):
                    if 'countdown_segment_' in audio_input and os.path.exists(audio_input):
                        os.remove(audio_input)
                
                # Update current_audio to point to the final composite
                current_audio = composite_audio_path
        
        # Final composite audio with normalization
        if current_audio != composite_audio_path:
            # If we didn't create the composite directly, apply normalization
            if current_audio != silent_audio_path:
                subprocess.run([
                    'ffmpeg', '-loglevel', 'error', '-y',
                    '-i', current_audio,
                    '-filter:a', 'loudnorm=I=-20:LRA=11:TP=-2:linear=true',
                    composite_audio_path
                ], check=True)
            else:
                # If no components were added, use the silent track
                if os.path.exists(composite_audio_path):
                    os.remove(composite_audio_path)
                os.rename(silent_audio_path, composite_audio_path)
        else:
            # Composite was created directly, apply final normalization in place
            temp_normalized = self.dynamicAssetDir + "temp_final_normalized.wav"
            subprocess.run([
                'ffmpeg', '-loglevel', 'error', '-y',
                '-i', composite_audio_path,
                '-filter:a', 'loudnorm=I=-16:LRA=11:TP=-1.5',
                temp_normalized
            ], check=True)
            os.replace(temp_normalized, composite_audio_path)
        
        # Clean up temporary files
        for i in range(temp_counter):
            temp_file = self.dynamicAssetDir + f"temp_composite_{i}.wav"
            if os.path.exists(temp_file) and temp_file != composite_audio_path:
                os.remove(temp_file)
        
        if os.path.exists(silent_audio_path) and silent_audio_path != composite_audio_path:
            os.remove(silent_audio_path)
        
        print(f"Created composite audio track: {composite_audio_path} (duration: {total_duration}s)")
        return composite_audio_path

    def _addCountdownToComposite(self, current_audio: str, countdown_audio_info: Dict[str, Any], temp_counter: int) -> str:
        """
        Add countdown audio segments to the composite track with precise timing.
        """
        import subprocess
        
        countdown_segments = self._generateCountdownSegments()
        countdown_duration = countdown_audio_info['end_time'] - countdown_audio_info['start_time']
        
        result_audio = current_audio
        
        # Add each countdown segment with precise timing
        for i, (start_time, end_time, number) in enumerate(countdown_segments):
            # Calculate which part of the countdown audio to use
            segment_start_in_audio = (i / 3) * countdown_duration
            required_segment_duration = (end_time - start_time)
            original_segment_duration = countdown_duration / 3
            
            # Extract the specific countdown segment
            raw_segment_path = self.dynamicAssetDir + f"raw_countdown_{number}_audio.wav"
            subprocess.run([
                'ffmpeg', '-loglevel', 'error', '-y',
                '-i', countdown_audio_info['path'],
                '-ss', str(segment_start_in_audio),
                '-t', str(original_segment_duration),
                raw_segment_path
            ], check=True)
            
            # Speed up the segment to fit exact timeframe if needed
            segment_audio_path = self.dynamicAssetDir + f"countdown_{number}_audio.wav"
            
            if original_segment_duration > required_segment_duration:
                speed_factor = original_segment_duration / required_segment_duration
                print(f"   Speeding up countdown '{number}': {original_segment_duration:.2f}s → {required_segment_duration:.2f}s (factor: {speed_factor:.2f}x)")
                
                subprocess.run([
                    'ffmpeg', '-loglevel', 'error', '-y',
                    '-i', raw_segment_path,
                    '-filter:a', f'atempo={speed_factor:.3f}',
                    segment_audio_path
                ], check=True)
            else:
                # Copy as-is if it already fits
                subprocess.run([
                    'ffmpeg', '-loglevel', 'error', '-y',
                    '-i', raw_segment_path,
                    '-c', 'copy',
                    segment_audio_path
                ], check=True)
            
            # Clean up raw segment
            if os.path.exists(raw_segment_path):
                os.remove(raw_segment_path)
            
            # Add this segment to the composite with volume normalization
            temp_output = self.dynamicAssetDir + f"temp_composite_{temp_counter + i}.wav"
            
            subprocess.run([
                'ffmpeg', '-loglevel', 'error', '-y',
                '-i', result_audio,
                '-i', segment_audio_path,
                '-filter_complex', 
                f"[1:a]volume=2.0,adelay={int(start_time * 1000)}|{int(start_time * 1000)}[delayed];"
                f"[0:a][delayed]amix=inputs=2:duration=longest[out]",
                '-map', '[out]',
                temp_output
            ], check=True)
            
            result_audio = temp_output
        
        return result_audio

    def _getAudioDuration(self, audio_path: str) -> float:
        """
        Get the duration of an audio file in seconds.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Duration in seconds, or 0.0 if unable to determine
        """
        try:
            result = subprocess.run([
                'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                '-of', 'csv=p=0', audio_path
            ], capture_output=True, text=True, check=True)
            
            duration_str = result.stdout.strip()
            if duration_str:
                return float(duration_str)
            else:
                return 0.0
                
        except (subprocess.CalledProcessError, ValueError, FileNotFoundError):
            # Fallback: try using get_asset_duration from audio_utils
            try:
                from shortGPT.audio.audio_duration import get_asset_duration
                _, duration = get_asset_duration(audio_path, False)
                return duration
            except:
                return 0.0

    def _addCountdownAudioSegments(self, videoEditor: EditingEngine, countdown_audio_info: Dict[str, Any]):
        """
        Add countdown audio segments with precise timing.
        
        The countdown audio file contains "Three. Two. One." but we need to split it
        into individual segments that match the visual countdown timing.
        """
        countdown_segments = self._generateCountdownSegments()
        countdown_duration = countdown_audio_info['end_time'] - countdown_audio_info['start_time']
        
        # Create individual countdown audio files for perfect sync
        for i, (start_time, end_time, number) in enumerate(countdown_segments):
            # Calculate which part of the countdown audio to use
            segment_start_in_audio = (i / 3) * countdown_duration
            segment_end_in_audio = ((i + 1) / 3) * countdown_duration
            
            # Create a trimmed audio file for this countdown number
            trimmed_audio_path = self.dynamicAssetDir + f"countdown_{number}_audio.wav"
            self._createTrimmedAudio(
                countdown_audio_info['path'], 
                trimmed_audio_path, 
                segment_start_in_audio, 
                segment_end_in_audio
            )
            
            # Add the trimmed audio at the exact timing
            videoEditor.addEditingStep(EditingStep.INSERT_AUDIO, {
                'url': trimmed_audio_path,
                'set_time_start': start_time,
                'set_time_end': end_time
            })

    def _createTrimmedAudio(self, input_path: str, output_path: str, start_time: float, end_time: float):
        """
        Create a trimmed audio file using ffmpeg.
        
        Args:
            input_path: Path to the input audio file
            output_path: Path for the output trimmed audio file
            start_time: Start time in seconds for trimming
            end_time: End time in seconds for trimming
        """
        import subprocess
        
        duration = end_time - start_time
        
        try:
            subprocess.run([
                'ffmpeg', '-loglevel', 'error', '-y',
                '-i', input_path,
                '-ss', str(start_time),
                '-t', str(duration),
                '-c', 'copy',
                output_path
            ], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Warning: Could not trim audio file. Using original file. Error: {e}")
            # Fallback: copy the original file
            import shutil
            shutil.copy2(input_path, output_path)

    def get_quiz_components(self) -> Dict[str, Any]:
        """
        Get the parsed quiz components for inspection or debugging.
        
        Returns:
            Dictionary containing all parsed quiz components with timings
        """
        return self._db_quiz_components
        
    def get_countdown_segments(self) -> List[Tuple[float, float, str]]:
        """
        Get the generated countdown segments for inspection or debugging.
        
        Returns:
            List of countdown segments with timing information
        """
        return self._generateCountdownSegments()

    def _generateTempAudio(self):
        """
        Override audio generation to create individual audio files for each quiz component.
        
        This ensures perfect timing synchronization by generating separate audio files
        for each component and inserting them at exact specified times.
        """
        if self._db_temp_audio_path:
            return
        
        # Generate individual audio files for each component
        self._generateComponentAudioFiles()
        
        # Create a placeholder main audio file (will be replaced by component audio in rendering)
        placeholder_script = "Quiz video"
        self._db_temp_audio_path = self.voiceModule.generate_voice(
            placeholder_script, self.dynamicAssetDir + "temp_audio_path.wav"
        )
        
    def _generateComponentAudioFiles(self):
        """
        Generate separate audio files for each quiz component with precise timing.
        Enhanced to handle multiple questions, countdowns, answers, and CTAs.
        """
        components = self._db_quiz_components
        component_audio_files = {}
        
        print("Generating individual audio files for each quiz component...")
        
        # Process all components from the enhanced structure
        all_components = components.get('all_components', [])
        
        for i, component in enumerate(all_components):
            component_type = component['type']
            
            # Clean the content for audio
            if component_type == 'countdown':
                audio_text = "Three. Two. One."
            else:
                audio_text = self._cleanContentForAudio(component['content'])
            
            if audio_text:
                # Handle translation if needed
                if self._db_language != Language.ENGLISH.value:
                    audio_text = gpt_translate.translateContent(audio_text, self._db_language)
                
                # Generate unique audio filename for each component
                audio_filename = f"{component_type}_{i}_audio.wav"
                audio_path = self.dynamicAssetDir + audio_filename
                component_key = f"{component_type}_{i}"
                
                print(f"Generating {component_key} audio: '{audio_text}'")
                raw_audio_path = self.dynamicAssetDir + f"raw_{component_key}_audio.wav"
                self.voiceModule.generate_voice(audio_text, raw_audio_path)
                
                # Calculate required duration from script timing
                required_duration = component['end_time'] - component['start_time']
                
                # Speed up audio to fit the exact timeframe and normalize volume
                normalized_audio_path = self.dynamicAssetDir + f"normalized_{component_key}_audio.wav"
                
                # First normalize the raw audio
                subprocess.run([
                    'ffmpeg', '-loglevel', 'error', '-y',
                    '-i', raw_audio_path,
                    '-filter:a', 'loudnorm=I=-20:LRA=11:TP=-2:linear=true',
                    normalized_audio_path
                ], check=True)
                
                # Get actual duration of the normalized audio
                actual_duration = self._getAudioDuration(normalized_audio_path)
                
                if actual_duration > 0:
                    # Calculate speed factor to fit in required timeframe
                    speed_factor = actual_duration / required_duration
                    
                    if speed_factor > 1.0:  # Only speed up if audio is longer than timeframe
                        print(f"   Speeding up {component_key} audio: {actual_duration:.2f}s → {required_duration:.2f}s (factor: {speed_factor:.2f}x)")
                        
                        # Apply speed adjustment while maintaining pitch
                        subprocess.run([
                            'ffmpeg', '-loglevel', 'error', '-y',
                            '-i', normalized_audio_path,
                            '-filter:a', f'atempo={speed_factor:.3f}',
                            audio_path
                        ], check=True)
                    else:
                        # Audio already fits, just copy the normalized version
                        subprocess.run([
                            'ffmpeg', '-loglevel', 'error', '-y',
                            '-i', normalized_audio_path,
                            '-c', 'copy',
                            audio_path
                        ], check=True)
                        print(f"   {component_key} audio fits timeframe: {actual_duration:.2f}s ≤ {required_duration:.2f}s")
                else:
                    # Fallback: just copy normalized audio
                    subprocess.run([
                        'ffmpeg', '-loglevel', 'error', '-y',
                        '-i', normalized_audio_path,
                        '-c', 'copy',
                        audio_path
                    ], check=True)
                
                # Clean up temporary files
                if os.path.exists(raw_audio_path):
                    os.remove(raw_audio_path)
                if os.path.exists(normalized_audio_path):
                    os.remove(normalized_audio_path)
                
                # Store the audio file path with timing info
                component_audio_files[component_key] = {
                    'path': audio_path,
                    'start_time': component['start_time'],
                    'end_time': component['end_time'],
                    'text': audio_text,
                    'type': component_type,
                    'component': component
                }
        
        # Store component audio files for use in rendering
        self._db_component_audio_files = component_audio_files

    def _generateCleanAudioScript(self) -> str:
        """
        Generate a clean script for TTS by extracting only the spoken content
        from quiz components in proper timing order.
        
        Returns:
            Clean script without timestamps or component labels, properly formatted for TTS
        """
        components = self._db_quiz_components
        
        # Build the script in chronological order
        script_parts = []
        
        # Collect all components with their start times for proper ordering
        timed_components = []
        
        for component_type in ['question', 'countdown', 'answer', 'cta']:
            component = components.get(component_type)
            if component:
                timed_components.append((component['start_time'], component_type, component['content']))
        
        # Sort by start time to ensure proper order
        timed_components.sort(key=lambda x: x[0])
        
        # Build the clean script
        for start_time, component_type, content in timed_components:
            if component_type == 'countdown':
                # For countdown, speak the numbers with pauses
                script_parts.append("Three. Two. One.")
            else:
                # For other components, clean the content
                clean_content = self._cleanContentForAudio(content)
                if clean_content:
                    script_parts.append(clean_content)
        
        return " ".join(script_parts)

    def _cleanContentForAudio(self, content: str) -> str:
        """
        Clean content for audio generation by removing visual-only elements.
        
        Args:
            content: Raw content from quiz component
            
        Returns:
            Cleaned content suitable for TTS
        """
        # Remove or replace emojis with descriptive text where appropriate
        emoji_replacements = {
            '🇫🇷': 'French',
            '[': '',
            ']': '',
            '🎨': '',
            '🏆': '',
            '🧮': '',
            '💀': '',
            '🎉': '',
            '✨': '',
            '💡': '',
            '🌟': '',
            '🔥': '',
            '💯': '',
            '👑': '',
            '🚀': '',
            '⭐': '',
            '🌍': '',
            '🎯': '',
            '💎': '',
            '🎪': '',
        }
        
        cleaned = content
        for emoji, replacement in emoji_replacements.items():
            cleaned = cleaned.replace(emoji, replacement)
        
        # Remove extra exclamation marks (keep one maximum)
        cleaned = re.sub(r'!+', '!', cleaned)
        
        # Clean up extra spaces
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # Remove phrases that are purely visual cues
        visual_phrases = [
            'The City of Light!',  # Keep just "Paris"
            'Amazing, right?',     # Remove rhetorical questions that are visual
            'Quick math!',         # Remove visual excitement
        ]
        
        for phrase in visual_phrases:
            if phrase in cleaned:
                # Keep the core answer, remove the visual flair
                if 'Paris! The City of Light!' in cleaned:
                    cleaned = cleaned.replace('Paris! The City of Light!', 'Paris')
                elif phrase in cleaned:
                    cleaned = cleaned.replace(phrase, '').strip()
        
        return cleaned

    def _timeCaptions(self):
        """
        Override caption timing to use quiz component timing instead of whisper analysis.
        
        This ensures text overlays appear exactly when specified in the quiz script,
        rather than trying to sync with the continuous audio track.
        """
        # Still generate whisper analysis for audio validation
        self.verifyParameters(audioPath=self._db_audio_path)
        whisper_analysis = audio_utils.audioToText(self._db_audio_path)
        
        # Generate timed captions based on quiz components, not whisper timing
        self._db_timed_captions = self._generateQuizTimedCaptions()
        
        # Store whisper analysis for debugging if needed
        self._db_whisper_analysis = whisper_analysis

    def _generateQuizTimedCaptions(self) -> List[Tuple[Tuple[float, float], str]]:
        """
        Generate timed captions based on quiz component timing rather than audio analysis.
        Enhanced to support multiple questions, countdowns, answers, and CTAs.
        
        Returns:
            List of tuples with timing and text for captions
        """
        timed_captions = []
        components = self._db_quiz_components
        
        # Use enhanced multi-component structure
        all_components = components.get('all_components', [])
        
        # If no multi-component structure, fall back to single-component for backward compatibility
        if not all_components:
            for component_type in ['question', 'countdown', 'answer', 'cta']:
                component = components.get(component_type)
                if component:
                    all_components.append({
                        'type': component_type,
                        'start_time': component['start_time'],
                        'end_time': component['end_time'],
                        'content': component['content']
                    })
        
        # Process all components
        for component in all_components:
            component_type = component['type']
            start_time = component['start_time']
            end_time = component['end_time']
            content = component['content']
            
            if component_type == 'countdown':
                # Don't add captions for countdown (handled by countdown overlay)
                continue
            else:
                # For other components, use the content as caption
                # Split long content into chunks if needed
                max_len = 15 if self._db_format_vertical else 30
                if len(content) <= max_len:
                    timed_captions.append(((start_time, end_time), content))
                else:
                    # Split content into smaller chunks with proportional timing
                    words = content.split()
                    chunk_size = max_len // 8  # Approximate words per chunk
                    duration = end_time - start_time
                    
                    chunks = []
                    for i in range(0, len(words), chunk_size):
                        chunk_words = words[i:i + chunk_size]
                        chunks.append(' '.join(chunk_words))
                    
                    if chunks:
                        chunk_duration = duration / len(chunks)
                        for i, chunk in enumerate(chunks):
                            chunk_start = start_time + (i * chunk_duration)
                            chunk_end = start_time + ((i + 1) * chunk_duration)
                            timed_captions.append(((chunk_start, chunk_end), chunk))
        
        return timed_captions

    def _speedUpAudio(self):
        """
        Override speed up audio to handle component-based audio files.
        
        Since quiz videos use precise timing, we don't speed up individual components
        to maintain perfect synchronization with visual elements.
        """
        if self._db_audio_path:
            return
            
        # For quiz videos, we don't speed up audio to maintain precise timing
        # The composite audio will be created during rendering with exact timing
        self._db_audio_path = self._db_temp_audio_path
        
        print("Quiz audio timing preserved - no speed adjustment applied for precise sync")