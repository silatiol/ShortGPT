#!/usr/bin/env python3
"""
Demo script showing QuizVideoEngine with proper audio synchronization.

This example demonstrates how the enhanced QuizVideoEngine:
1. Strips extra information from TTS 
2. Synchronizes audio with text components
3. Generates clean, properly timed quiz videos
"""

import sys
import os

# Add the parent directory to the Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shortGPT.engine.quiz_video_engine import QuizVideoEngine
from shortGPT.audio.edge_voice_module import EdgeTTSVoiceModule
from shortGPT.config.languages import Language


def create_geography_quiz():
    """Create a geography quiz with clean audio synchronization."""
    
    # Quiz script with precise timing for audio sync
    quiz_script = """[0.0-5.0] QUESTION: What is the capital of France?
[5.0-8.0] COUNTDOWN: 3-2-1
[8.0-12.0] ANSWER: 🇫🇷 Paris! The City of Light!
[12.0-15.0] CTA: Follow for more geography quizzes!"""
    
    print("=== Geography Quiz Demo ===")
    print("Original quiz script:")
    print(quiz_script)
    print("\n" + "="*50 + "\n")
    
    # Create voice module
    voice_module = EdgeTTSVoiceModule("en-US-AriaNeural")
    
    # Create quiz engine
    quiz_engine = QuizVideoEngine(
        voiceModule=voice_module,
        quiz_script=quiz_script,
        watermark="QuizMaster",
        language=Language.ENGLISH
    )
    
    # Show what the clean audio script will be
    print("Clean audio script (what TTS will speak):")
    clean_script = quiz_engine._generateCleanAudioScript()
    print(f"'{clean_script}'")
    print("\nNotice how:")
    print("- Emojis are cleaned (🇫🇷 → 'French' or removed)")
    print("- Visual flair is stripped ('The City of Light!' → just 'Paris')")
    print("- Countdown becomes 'Three. Two. One.'")
    print("- Only essential spoken content remains")
    print("\n" + "="*50 + "\n")
    
    # Show quiz components
    components = quiz_engine.get_quiz_components()
    print("Parsed quiz components:")
    for comp_type, data in components.items():
        if data:
            print(f"  {comp_type.upper()}: {data['start_time']}-{data['end_time']}s")
            print(f"    Original: '{data['content']}'")
            if comp_type != 'countdown':
                cleaned = quiz_engine._cleanContentForAudio(data['content'])
                print(f"    Audio: '{cleaned}'")
    print("\n" + "="*50 + "\n")
    
    # Show countdown segments
    countdown_segments = quiz_engine.get_countdown_segments()
    print("Countdown segments (precise timing):")
    for start, end, number in countdown_segments:
        print(f"  {number}: {start:.1f}-{end:.1f}s")
    
    return quiz_engine


def create_science_quiz():
    """Create a science quiz demonstrating emoji and content cleaning."""
    
    quiz_script = """[0.0-4.0] QUESTION: How many bones are in the human body?
[4.0-7.0] COUNTDOWN: 3-2-1
[7.0-11.0] ANSWER: 💀 206 bones! Amazing, right?
[11.0-14.0] CTA: Like if you learned something new!"""
    
    print("=== Science Quiz Demo ===")
    print("Original quiz script:")
    print(quiz_script)
    print("\n" + "="*50 + "\n")
    
    voice_module = EdgeTTSVoiceModule("en-US-AriaNeural")
    
    quiz_engine = QuizVideoEngine(
        voiceModule=voice_module,
        quiz_script=quiz_script,
        watermark="ScienceFacts",
        language=Language.ENGLISH
    )
    
    print("Clean audio script:")
    clean_script = quiz_engine._generateCleanAudioScript()
    print(f"'{clean_script}'")
    print("\nCleaning applied:")
    print("- 💀 emoji removed")
    print("- 'Amazing, right?' removed (visual rhetorical question)")
    print("- Core content preserved: '206 bones'")
    
    return quiz_engine


def create_math_quiz():
    """Create a math quiz with minimal visual elements."""
    
    quiz_script = """[0.0-4.0] QUESTION: What is 15% of 200?
[4.0-7.0] COUNTDOWN: 3-2-1
[7.0-10.0] ANSWER: 🧮 30! Quick math!
[10.0-13.0] CTA: Follow for daily math tips!"""
    
    print("=== Math Quiz Demo ===")
    print("Original quiz script:")
    print(quiz_script)
    print("\n" + "="*50 + "\n")
    
    voice_module = EdgeTTSVoiceModule("en-US-AriaNeural")
    
    quiz_engine = QuizVideoEngine(
        voiceModule=voice_module,
        quiz_script=quiz_script,
        watermark="MathDaily",
        language=Language.ENGLISH
    )
    
    print("Clean audio script:")
    clean_script = quiz_engine._generateCleanAudioScript()
    print(f"'{clean_script}'")
    print("\nCleaning applied:")
    print("- 🧮 emoji removed")
    print("- 'Quick math!' removed (visual excitement)")
    print("- Core answer preserved: '30'")
    
    return quiz_engine


def demonstrate_timing_precision():
    """Demonstrate how timing precision works."""
    
    quiz_script = """[0.0-6.0] QUESTION: Which movie won the 2023 Oscar for Best Picture?
[6.0-9.0] COUNTDOWN: 3-2-1
[9.0-13.0] ANSWER: 🏆 Everything Everywhere All at Once!
[13.0-16.0] CTA: Comment your favorite movie!"""
    
    print("=== Timing Precision Demo ===")
    print("Quiz script with 16-second total duration:")
    print(quiz_script)
    print("\n" + "="*50 + "\n")
    
    voice_module = EdgeTTSVoiceModule("en-US-AriaNeural")
    
    quiz_engine = QuizVideoEngine(
        voiceModule=voice_module,
        quiz_script=quiz_script,
        watermark="MovieQuiz",
        language=Language.ENGLISH
    )
    
    # Generate timed captions to show synchronization
    quiz_engine._db_audio_path = "dummy.wav"  # Simulate audio path for caption generation
    timed_captions = quiz_engine._generateQuizTimedCaptions()
    
    print("Generated timed captions (synced to quiz timing, not audio analysis):")
    for (start, end), text in timed_captions:
        print(f"  {start:.1f}-{end:.1f}s: '{text}'")
    
    print("\nKey improvements:")
    print("✅ Text appears exactly at specified times")
    print("✅ No dependency on audio analysis timing")
    print("✅ Perfect synchronization with quiz script")
    print("✅ Countdown handled separately with overlay")


def main():
    """Run all quiz demos to show audio synchronization features."""
    
    print("🎬 QuizVideoEngine Audio Synchronization Demo")
    print("=" * 60)
    print()
    
    # Run all demos
    create_geography_quiz()
    print("\n" + "="*60 + "\n")
    
    create_science_quiz()
    print("\n" + "="*60 + "\n")
    
    create_math_quiz()
    print("\n" + "="*60 + "\n")
    
    demonstrate_timing_precision()
    print("\n" + "="*60 + "\n")
    
    print("🎯 Summary of Audio Synchronization Features:")
    print()
    print("1. 🧹 CLEAN AUDIO GENERATION:")
    print("   - Strips emojis and visual-only elements")
    print("   - Removes rhetorical questions and excitement phrases")
    print("   - Preserves only essential spoken content")
    print()
    print("2. ⏰ PRECISE TIMING SYNC:")
    print("   - Text overlays appear at exact script times")
    print("   - No dependency on audio analysis timing")
    print("   - Component-based synchronization")
    print()
    print("3. 🎭 COUNTDOWN HANDLING:")
    print("   - Audio says 'Three. Two. One.'")
    print("   - Visual shows '3', '2', '1' with precise timing")
    print("   - Perfect synchronization between audio and visual")
    print()
    print("4. 🎨 VISUAL ENHANCEMENT:")
    print("   - Visual text can be more exciting (emojis, etc.)")
    print("   - Audio remains clear and professional")
    print("   - Best of both worlds for TikTok engagement")
    print()
    print("🚀 Ready for TikTok: Vertical 1080x1920, no background music!")


if __name__ == "__main__":
    main()