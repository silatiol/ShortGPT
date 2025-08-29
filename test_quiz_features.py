#!/usr/bin/env python3
"""
Test script for the new QuizVideoEngine features:
1. Intro animation
2. Asset library video source
3. Pexels video source (fallback)
"""

from shortGPT.audio.edge_voice_module import EdgeTTSVoiceModule
from shortGPT.config.languages import Language
from shortGPT.engine.quiz_video_engine import QuizVideoEngine

def test_quiz_with_intro_and_asset():
    """Test quiz video with intro animation and asset library video"""
    
    # Sample quiz script - will be shifted by intro duration automatically
    quiz_script = """
[0.0-2.0] QUESTION: What's the capital of France?
[2.0-3.5] COUNTDOWN: 3-2-1
[3.5-5.5] ANSWER: Paris! 🇫🇷
[5.5-7.5] CTA: Like if you got it right!
"""
    
    # Initialize voice module
    voice_module = EdgeTTSVoiceModule("en-US-AriaNeural")
    
    print("Testing QuizVideoEngine with new features...")
    print("=" * 50)
    
    # Test with intro animation and asset library
    print("1. Testing with intro animation and asset library source...")
    try:
        quiz_engine = QuizVideoEngine(
            voiceModule=voice_module,
            quiz_script=quiz_script,
            intro_text="🧠 Geography Quiz Challenge! 🌍",
            intro_duration=2.5,
            video_source="asset_library",
            background_video_asset="subscribe animation",  # This should exist from the default setup
            watermark="@YourChannel"
        )
        
        print("✅ QuizVideoEngine initialized successfully with asset library!")
        print(f"   Intro text: {quiz_engine._intro_text}")
        print(f"   Intro duration: {quiz_engine._intro_duration}s")
        print(f"   Video source: {quiz_engine._video_source}")
        print(f"   Background asset: {quiz_engine._background_video_asset}")
        
        # Check if quiz components were parsed correctly with intro
        components = quiz_engine._db_quiz_components
        print(f"   Total components: {len(components.get('all_components', []))}")
        
        if 'intro' in components:
            intro = components['intro']
            print(f"   Intro component: '{intro['content']}' [{intro['start_time']}-{intro['end_time']}]")
        
        # Show that other components were shifted
        if components.get('all_components'):
            for comp in components['all_components'][:3]:  # Show first 3
                print(f"   Component: {comp['type']} [{comp['start_time']}-{comp['end_time']}] - {comp['content'][:30]}...")
        
    except Exception as e:
        print(f"❌ Error with asset library: {e}")
        print("This might be expected if the asset doesn't exist")
    
    print("\n" + "=" * 50)
    
    # Test with intro animation and Pexels (fallback)
    print("2. Testing with intro animation and Pexels source...")
    try:
        quiz_engine_pexels = QuizVideoEngine(
            voiceModule=voice_module,
            quiz_script=quiz_script,
            intro_text="🎯 Quick Geography Test! 🗺️",
            intro_duration=3.0,
            video_source="pexels",  # Default behavior
            watermark="@QuizMaster"
        )
        
        print("✅ QuizVideoEngine initialized successfully with Pexels!")
        print(f"   Intro text: {quiz_engine_pexels._intro_text}")
        print(f"   Intro duration: {quiz_engine_pexels._intro_duration}s")
        print(f"   Video source: {quiz_engine_pexels._video_source}")
        
    except Exception as e:
        print(f"❌ Error with Pexels: {e}")
    
    print("\n" + "=" * 50)
    
    # Test without intro (original behavior)
    print("3. Testing without intro (original behavior)...")
    try:
        quiz_engine_original = QuizVideoEngine(
            voiceModule=voice_module,
            quiz_script=quiz_script,
            video_source="pexels"
        )
        
        print("✅ QuizVideoEngine initialized successfully without intro!")
        print(f"   Video source: {quiz_engine_original._video_source}")
        
        # Check components weren't shifted
        components = quiz_engine_original._db_quiz_components
        if components.get('all_components'):
            first_comp = components['all_components'][0]
            print(f"   First component starts at: {first_comp['start_time']}s (should be 0.0)")
        
    except Exception as e:
        print(f"❌ Error with original behavior: {e}")

if __name__ == "__main__":
    test_quiz_with_intro_and_asset()
    print("\n🎉 Feature testing completed!")
    print("\nTo create an actual video, call makeContent() on the quiz engine.")
    print("Example:")
    print("for step_num, step_info in quiz_engine.makeContent():")
    print("    print(f'Step {step_num}: {step_info}')")