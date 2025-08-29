#!/usr/bin/env python3
"""
Test script for enhanced caption features:
1. Emoji support in captions
2. Bracket highlighting with different colors
3. Bracket removal with preserved highlighting
"""

import os
import sys
sys.path.append('/home/silatiol/projects/ShortGPT')

from shortGPT.engine.quiz_video_engine import QuizVideoEngine
from shortGPT.audio.edge_voice_module import EdgeTTSVoiceModule

def test_enhanced_captions():
    """Test the enhanced caption system with emojis and bracket highlighting."""
    
    # Quiz script with emojis and bracket formatting
    enhanced_quiz_script = """
    {
        "intro": {
            "content": "🎯 Get ready for the ultimate [Geography Quiz]! 🌍",
            "duration": 3.0
        },
        "question_1": {
            "content": "What is the capital of [France]? 🇫🇷",
            "duration": 4.0
        },
        "countdown_1": {
            "content": "3-2-1",
            "duration": 2.0
        },
        "answer_1": {
            "content": "🇫🇷 [Paris]! The City of Light! ✨",
            "duration": 4.0
        },
        "question_2": {
            "content": "Which country has the most [time zones]? ⏰",
            "duration": 4.0
        },
        "countdown_2": {
            "content": "3-2-1",
            "duration": 2.0
        },
        "answer_2": {
            "content": "🇫🇷 [France] with 12 time zones! 🌍",
            "duration": 4.0
        },
        "cta": {
            "content": "Follow for more [geography quizzes]! 🎉📚",
            "duration": 3.0
        }
    }
    """
    
    # Create quiz engine
    quiz_engine = QuizVideoEngine(
        background_video_urls=[
            "https://videos.pexels.com/video-files/3571264/3571264-uhd_2560_1440_30fps.mp4"
        ],
        quiz_script=enhanced_quiz_script,
        voice_module=EdgeTTSVoiceModule(),
        video_search_terms=["geography world map"],
        output_name="Enhanced Captions Test",
        intro_text="🎯 Geography Quiz! 🌍",
        intro_duration=3.0,
        use_sound_effects=True
    )
    
    print("🎬 Creating quiz video with enhanced captions...")
    print("✨ Features being tested:")
    print("   📱 Emoji support in captions")
    print("   🎨 Bracket highlighting with gold color")
    print("   🚫 Bracket removal while preserving highlighting")
    print("   🔤 Mixed styling in single caption lines")
    
    try:
        # Generate the quiz video
        video_path = quiz_engine.makeContent()
        
        if video_path:
            print(f"✅ Enhanced caption test completed!")
            print(f"📹 Video saved to: {video_path}")
            print("\n🎯 Caption features tested:")
            print("   🌟 Emojis should appear in captions")
            print("   🎨 Text in [brackets] should be highlighted in gold")
            print("   📝 Brackets should be removed from display")
            print("   💫 Multiple styles should work in same caption")
        else:
            print("❌ Video generation failed")
            
    except Exception as e:
        print(f"❌ Error during video generation: {e}")
        import traceback
        traceback.print_exc()

def test_simple_bracket_highlighting():
    """Test simple bracket highlighting without full video generation."""
    
    print("\n🧪 Testing bracket text parsing...")
    
    # Import the core editing engine to test text parsing
    from shortGPT.editing_framework.core_editing_engine import CoreEditingEngine
    
    engine = CoreEditingEngine()
    
    test_texts = [
        "What is the capital of [France]? 🇫🇷",
        "🇫🇷 [Paris]! The City of Light! ✨",
        "Follow for more [geography quizzes]! 🎉📚",
        "Regular text without brackets 📚",
        "Multiple [highlighted] words in [different] places! 🎯"
    ]
    
    for text in test_texts:
        print(f"\nInput:  '{text}'")
        segments = engine._parse_bracket_text(text)
        print(f"Output: {segments}")
        
        for segment, is_highlighted in segments:
            color = "🟡" if is_highlighted else "⚪"
            print(f"  {color} '{segment}' {'(highlighted)' if is_highlighted else '(normal)'}")

if __name__ == "__main__":
    print("🎬 Enhanced Caption Features Test")
    print("=" * 50)
    
    # Run simple parsing test first
    test_simple_bracket_highlighting()
    
    # Ask user if they want to run full video test
    print("\n" + "=" * 50)
    choice = input("🎥 Run full video generation test? (y/n): ").lower().strip()
    
    if choice in ['y', 'yes']:
        test_enhanced_captions()
    else:
        print("✅ Parsing test completed! Full video test skipped.")
        
    print("\n🎉 Test completed!")