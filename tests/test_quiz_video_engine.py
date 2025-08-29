import unittest
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock

from shortGPT.engine.quiz_video_engine import QuizVideoEngine
from shortGPT.audio.voice_module import VoiceModule
from shortGPT.config.languages import Language


class TestQuizVideoEngine(unittest.TestCase):
    """Test suite for QuizVideoEngine functionality."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a mock voice module
        self.mock_voice_module = Mock(spec=VoiceModule)
        self.mock_voice_module.generate_voice.return_value = "test_audio.wav"
        
        # Sample quiz script for testing
        self.sample_quiz_script = """[0.0-5.0] QUESTION: What is the capital of France?
[5.0-8.0] COUNTDOWN: 3-2-1
[8.0-12.0] ANSWER: 🇫🇷 Paris! The City of Light!
[12.0-15.0] CTA: Follow for more geography quizzes!"""
        
        # Create temporary directory for test assets
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up after each test method."""
        # Clean up temporary directory
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_initialization(self):
        """Test QuizVideoEngine initialization."""
        engine = QuizVideoEngine(
            voiceModule=self.mock_voice_module,
            quiz_script=self.sample_quiz_script,
            watermark="TestChannel",
            language=Language.ENGLISH
        )
        
        # Test that initialization sets correct properties
        self.assertEqual(engine._db_script, self.sample_quiz_script)
        self.assertEqual(engine._db_watermark, "TestChannel")
        self.assertEqual(engine._db_language, Language.ENGLISH.value)
        self.assertTrue(engine._db_format_vertical)  # Always vertical for TikTok
        self.assertEqual(engine._db_background_music_name, "")  # No background music
        
    def test_quiz_script_parsing(self):
        """Test parsing of time-stamped quiz script."""
        engine = QuizVideoEngine(
            voiceModule=self.mock_voice_module,
            quiz_script=self.sample_quiz_script
        )
        
        components = engine.get_quiz_components()
        
        # Test question parsing
        self.assertIsNotNone(components['question'])
        self.assertEqual(components['question']['start_time'], 0.0)
        self.assertEqual(components['question']['end_time'], 5.0)
        self.assertEqual(components['question']['content'], "What is the capital of France?")
        
        # Test countdown parsing
        self.assertIsNotNone(components['countdown'])
        self.assertEqual(components['countdown']['start_time'], 5.0)
        self.assertEqual(components['countdown']['end_time'], 8.0)
        self.assertEqual(components['countdown']['content'], "3-2-1")
        
        # Test answer parsing
        self.assertIsNotNone(components['answer'])
        self.assertEqual(components['answer']['start_time'], 8.0)
        self.assertEqual(components['answer']['end_time'], 12.0)
        self.assertEqual(components['answer']['content'], "🇫🇷 Paris! The City of Light!")
        
        # Test CTA parsing
        self.assertIsNotNone(components['cta'])
        self.assertEqual(components['cta']['start_time'], 12.0)
        self.assertEqual(components['cta']['end_time'], 15.0)
        self.assertEqual(components['cta']['content'], "Follow for more geography quizzes!")

    def test_countdown_segments_generation(self):
        """Test generation of individual countdown segments."""
        engine = QuizVideoEngine(
            voiceModule=self.mock_voice_module,
            quiz_script=self.sample_quiz_script
        )
        
        countdown_segments = engine.get_countdown_segments()
        
        # Should have 3 segments (3, 2, 1)
        self.assertEqual(len(countdown_segments), 3)
        
        # Test segment timings (3-second countdown split into 1-second segments)
        expected_segments = [
            (5.0, 6.0, '3'),
            (6.0, 7.0, '2'),
            (7.0, 8.0, '1')
        ]
        
        for i, (start, end, number) in enumerate(countdown_segments):
            expected_start, expected_end, expected_number = expected_segments[i]
            self.assertAlmostEqual(start, expected_start, places=1)
            self.assertAlmostEqual(end, expected_end, places=1)
            self.assertEqual(number, expected_number)

    def test_vertical_format_enforcement(self):
        """Test that QuizVideoEngine always enforces vertical format."""
        engine = QuizVideoEngine(
            voiceModule=self.mock_voice_module,
            quiz_script=self.sample_quiz_script
        )
        
        # Should always be vertical regardless of initialization
        self.assertTrue(engine._db_format_vertical)

    def test_no_background_music(self):
        """Test that QuizVideoEngine never includes background music."""
        engine = QuizVideoEngine(
            voiceModule=self.mock_voice_module,
            quiz_script=self.sample_quiz_script
        )
        
        # Should never have background music for TikTok compatibility
        self.assertEqual(engine._db_background_music_name, "")

    def test_malformed_script_handling(self):
        """Test handling of malformed quiz scripts."""
        malformed_script = """Some text without proper formatting
[INVALID] Not a valid timestamp
[0.0-5.0] QUESTION: Valid question"""
        
        engine = QuizVideoEngine(
            voiceModule=self.mock_voice_module,
            quiz_script=malformed_script
        )
        
        components = engine.get_quiz_components()
        
        # Should gracefully handle malformed lines
        self.assertIsNotNone(components['question'])
        self.assertEqual(components['question']['content'], "Valid question")
        
        # Invalid components should be None
        self.assertIsNone(components['countdown'])
        self.assertIsNone(components['answer'])
        self.assertIsNone(components['cta'])

    def test_empty_script_handling(self):
        """Test handling of empty quiz scripts."""
        engine = QuizVideoEngine(
            voiceModule=self.mock_voice_module,
            quiz_script=""
        )
        
        components = engine.get_quiz_components()
        countdown_segments = engine.get_countdown_segments()
        
        # All components should be None for empty script
        self.assertIsNone(components['question'])
        self.assertIsNone(components['countdown'])
        self.assertIsNone(components['answer'])
        self.assertIsNone(components['cta'])
        
        # No countdown segments should be generated
        self.assertEqual(len(countdown_segments), 0)

    @patch('shortGPT.engine.quiz_video_engine.EditingEngine')
    @patch('shortGPT.engine.quiz_video_engine.gpt_editing')
    @patch('shortGPT.engine.quiz_video_engine.audio_utils')
    @patch('shortGPT.engine.quiz_video_engine.get_asset_duration')
    @patch('shortGPT.engine.quiz_video_engine.getBestVideo')
    def test_rendering_with_quiz_steps(self, mock_get_video, mock_duration, 
                                      mock_audio, mock_gpt, mock_editing_engine):
        """Test that rendering includes all quiz-specific editing steps."""
        # Setup mocks
        mock_editing_instance = Mock()
        mock_editing_engine.return_value = mock_editing_instance
        mock_duration.return_value = ("test_audio.wav", 15.0)
        mock_get_video.return_value = "test_video.mp4"
        mock_gpt.getVideoSearchQueriesTimed.return_value = [[(0.0, 15.0), ["test", "video", "quiz"]]]
        mock_audio.audioToText.return_value = [{"start": 0.0, "end": 15.0, "text": "test script"}]
        mock_audio.speedUpAudio.return_value = "sped_up_audio.wav"
        
        # Create engine and set required database values
        engine = QuizVideoEngine(
            voiceModule=self.mock_voice_module,
            quiz_script=self.sample_quiz_script
        )
        
        # Mock database attributes that would normally be set by previous steps
        engine._db_audio_path = "test_audio.wav"
        engine._db_voiceover_duration = 15.0
        engine._db_timed_video_urls = [[(0.0, 15.0), "test_video.mp4"]]
        engine._db_watermark = "TestChannel"
        
        # Create a temporary directory for the test
        with tempfile.TemporaryDirectory() as temp_dir:
            engine.dynamicAssetDir = temp_dir + "/"
            
            # Call the rendering method
            engine._editAndRenderShort()
            
            # Verify that editing steps were added
            calls = mock_editing_instance.addEditingStep.call_args_list
            
            # Should have multiple editing steps added
            self.assertGreater(len(calls), 5)
            
            # Verify specific quiz editing steps were called
            step_types = [call[0][0] for call in calls]
            from shortGPT.editing_framework.editing_engine import EditingStep
            
            self.assertIn(EditingStep.ADD_QUIZ_QUESTION, step_types)
            self.assertIn(EditingStep.ADD_COUNTDOWN_OVERLAY, step_types)
            self.assertIn(EditingStep.ADD_QUIZ_ANSWER, step_types)
            self.assertIn(EditingStep.ADD_QUIZ_CTA, step_types)
            
            # Verify countdown was called 3 times (for 3, 2, 1)
            countdown_calls = [call for call in calls if call[0][0] == EditingStep.ADD_COUNTDOWN_OVERLAY]
            self.assertEqual(len(countdown_calls), 3)

    def test_inheritance_from_content_video_engine(self):
        """Test that QuizVideoEngine properly inherits from ContentVideoEngine."""
        from shortGPT.engine.content_video_engine import ContentVideoEngine
        
        engine = QuizVideoEngine(
            voiceModule=self.mock_voice_module,
            quiz_script=self.sample_quiz_script
        )
        
        # Should be an instance of ContentVideoEngine
        self.assertIsInstance(engine, ContentVideoEngine)
        
        # Should have inherited step dictionary
        self.assertIsInstance(engine.stepDict, dict)
        self.assertGreater(len(engine.stepDict), 0)

    def test_api_symmetry_with_content_video_engine(self):
        """Test that QuizVideoEngine maintains API symmetry with ContentVideoEngine."""
        from shortGPT.engine.content_video_engine import ContentVideoEngine
        
        # Get public methods from ContentVideoEngine
        content_engine_methods = [method for method in dir(ContentVideoEngine) 
                                if not method.startswith('_') and callable(getattr(ContentVideoEngine, method))]
        
        # Create QuizVideoEngine instance
        quiz_engine = QuizVideoEngine(
            voiceModule=self.mock_voice_module,
            quiz_script=self.sample_quiz_script
        )
        
        # Verify QuizVideoEngine has all public methods from ContentVideoEngine
        for method_name in content_engine_methods:
            self.assertTrue(hasattr(quiz_engine, method_name), 
                          f"QuizVideoEngine missing method: {method_name}")
            self.assertTrue(callable(getattr(quiz_engine, method_name)),
                          f"QuizVideoEngine method not callable: {method_name}")

    def test_clean_audio_script_generation(self):
        """Test generation of clean audio script for TTS."""
        engine = QuizVideoEngine(
            voiceModule=self.mock_voice_module,
            quiz_script=self.sample_quiz_script
        )
        
        clean_script = engine._generateCleanAudioScript()
        
        # Should contain the question
        self.assertIn("What is the capital of France?", clean_script)
        
        # Should contain countdown as words
        self.assertIn("Three. Two. One.", clean_script)
        
        # Should contain cleaned answer (without emoji and visual flair)
        self.assertIn("Paris", clean_script)
        self.assertNotIn("🇫🇷", clean_script)  # Emoji should be removed/replaced
        
        # Should contain CTA
        self.assertIn("Follow for more geography quizzes!", clean_script)

    def test_content_cleaning_for_audio(self):
        """Test cleaning of content for audio generation."""
        engine = QuizVideoEngine(
            voiceModule=self.mock_voice_module,
            quiz_script=self.sample_quiz_script
        )
        
        # Test emoji removal
        test_cases = [
            ("🇫🇷 Paris! The City of Light!", "Paris"),  # Should clean visual flair
            ("💀 206 bones! Amazing, right?", "206 bones"),  # Remove emoji and rhetorical
            ("🧮 30! Quick math!", "30"),  # Remove emoji and excitement
            ("🏆 Everything Everywhere All at Once!", "Everything Everywhere All at Once"),  # Keep title
            ("Follow for more quizzes!", "Follow for more quizzes!"),  # Keep as-is
        ]
        
        for input_text, expected_output in test_cases:
            cleaned = engine._cleanContentForAudio(input_text)
            self.assertEqual(cleaned, expected_output, 
                           f"Failed to clean '{input_text}' correctly")

    def test_quiz_timed_captions_generation(self):
        """Test generation of quiz-based timed captions."""
        engine = QuizVideoEngine(
            voiceModule=self.mock_voice_module,
            quiz_script=self.sample_quiz_script
        )
        
        # Mock the audio path to enable caption generation
        engine._db_audio_path = "dummy.wav"
        
        timed_captions = engine._generateQuizTimedCaptions()
        
        # Should have captions for all components except countdown
        expected_components = 3  # question, answer, cta (not countdown)
        self.assertEqual(len(timed_captions), expected_components)
        
        # Check timing matches quiz script
        caption_texts = [text for _, text in timed_captions]
        self.assertIn("What is the capital of France?", caption_texts)
        self.assertIn("🇫🇷 Paris! The City of Light!", caption_texts)
        self.assertIn("Follow for more geography quizzes!", caption_texts)
        
        # Countdown should not appear in captions (handled by overlay)
        countdown_in_captions = any("3-2-1" in text for _, text in timed_captions)
        self.assertFalse(countdown_in_captions)

    def test_audio_sync_with_complex_script(self):
        """Test audio synchronization with a more complex quiz script."""
        complex_script = """[0.0-6.0] QUESTION: Which movie won the 2023 Oscar for Best Picture?
[6.0-9.0] COUNTDOWN: 3-2-1
[9.0-15.0] ANSWER: 🏆 Everything Everywhere All at Once! What a journey!
[15.0-18.0] CTA: Comment your favorite movie below!"""
        
        engine = QuizVideoEngine(
            voiceModule=self.mock_voice_module,
            quiz_script=complex_script
        )
        
        # Test clean script generation
        clean_script = engine._generateCleanAudioScript()
        
        # Should handle longer content appropriately
        self.assertIn("Which movie won the 2023 Oscar for Best Picture?", clean_script)
        self.assertIn("Three. Two. One.", clean_script)
        self.assertIn("Everything Everywhere All at Once", clean_script)
        self.assertIn("Comment your favorite movie below", clean_script)
        
        # Should not contain emoji
        self.assertNotIn("🏆", clean_script)

    def test_timing_precision_with_countdown(self):
        """Test that countdown timing is precise and correct."""
        engine = QuizVideoEngine(
            voiceModule=self.mock_voice_module,
            quiz_script=self.sample_quiz_script
        )
        
        countdown_segments = engine.get_countdown_segments()
        
        # Should have exactly 3 segments
        self.assertEqual(len(countdown_segments), 3)
        
        # Check precise timing (3-second countdown split into 1-second segments)
        expected_times = [
            (5.0, 6.0, '3'),
            (6.0, 7.0, '2'),
            (7.0, 8.0, '1')
        ]
        
        for i, (start, end, number) in enumerate(countdown_segments):
            expected_start, expected_end, expected_number = expected_times[i]
            self.assertAlmostEqual(start, expected_start, places=1)
            self.assertAlmostEqual(end, expected_end, places=1)
            self.assertEqual(number, expected_number)

    def test_component_audio_file_generation(self):
        """Test that individual audio files are generated for each component."""
        engine = QuizVideoEngine(
            voiceModule=self.mock_voice_module,
            quiz_script=self.sample_quiz_script
        )
        
        # Simulate component audio file generation
        engine._generateComponentAudioFiles()
        
        # Should have component audio files
        self.assertTrue(hasattr(engine, '_db_component_audio_files'))
        component_files = engine._db_component_audio_files
        
        # Should have files for each component
        expected_components = ['question', 'countdown', 'answer', 'cta']
        for component in expected_components:
            self.assertIn(component, component_files)
            self.assertIn('path', component_files[component])
            self.assertIn('start_time', component_files[component])
            self.assertIn('end_time', component_files[component])
            self.assertIn('text', component_files[component])

    def test_no_audio_speedup_for_precision(self):
        """Test that quiz videos don't speed up audio to maintain precise timing."""
        engine = QuizVideoEngine(
            voiceModule=self.mock_voice_module,
            quiz_script=self.sample_quiz_script
        )
        
        # Set up audio path
        engine._db_temp_audio_path = "test_audio.wav"
        
        # Call speed up audio method
        engine._speedUpAudio()
        
        # Should preserve original audio timing
        self.assertEqual(engine._db_audio_path, "test_audio.wav")

    @patch('shortGPT.engine.quiz_video_engine.subprocess.run')
    def test_audio_trimming_functionality(self, mock_subprocess):
        """Test audio trimming for countdown segments."""
        engine = QuizVideoEngine(
            voiceModule=self.mock_voice_module,
            quiz_script=self.sample_quiz_script
        )
        
        # Test audio trimming
        input_path = "countdown_audio.wav"
        output_path = "countdown_3_audio.wav"
        start_time = 0.0
        end_time = 1.0
        
        engine._createTrimmedAudio(input_path, output_path, start_time, end_time)
        
        # Should call ffmpeg with correct parameters
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0][0]
        
        self.assertIn('ffmpeg', call_args)
        self.assertIn(input_path, call_args)
        self.assertIn(output_path, call_args)
        self.assertIn('-ss', call_args)
        self.assertIn('0.0', call_args)
        self.assertIn('-t', call_args)
        self.assertIn('1.0', call_args)


if __name__ == '__main__':
    unittest.main()