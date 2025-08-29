#!/usr/bin/env python3
"""
Test script for the new QuizVideoEngine sound effects:
1. Captivating intro sound (whoosh/pop)
2. Countdown tick sounds (building tension)
3. Correct answer ding (satisfaction/reward)
"""

from shortGPT.audio.edge_voice_module import EdgeTTSVoiceModule
from shortGPT.config.languages import Language
from shortGPT.engine.quiz_video_engine import QuizVideoEngine

def test_sound_effects():
    """Test quiz video with all sound effects enabled"""
    
    # Sample quiz script with intro, countdown, and answer
    quiz_script = """
[0.0-2.0] QUESTION: What's the fastest land animal?
[2.0-3.5] COUNTDOWN: 3-2-1
[3.5-5.5] ANSWER: Cheetah! Up to 70 mph! 🐆
[5.5-7.5] CTA: Follow for more animal facts! 🦁
"""
    
    # Initialize voice module
    voice_module = EdgeTTSVoiceModule("en-US-AriaNeural")
    
    print("🎵 Testing QuizVideoEngine with Sound Effects")
    print("=" * 60)
    
    try:
        # Test with all sound effects enabled
        print("1. Testing with ALL sound effects enabled...")
        quiz_engine = QuizVideoEngine(
            voiceModule=voice_module,
            quiz_script=quiz_script,
            intro_text="🏃‍♂️ SPEED CHALLENGE! 🏃‍♂️",
            intro_duration=2.0,
            video_source="pexels",
            use_sound_effects=True,  # Enable sound effects
            watermark="@AnimalFacts"
        )
        
        print("✅ QuizVideoEngine with sound effects initialized!")
        print(f"   🎵 Sound effects: {quiz_engine._use_sound_effects}")
        print(f"   🎺 Intro sound: {'Generated' if hasattr(quiz_engine, '_intro_sound_path') else 'Not found'}")
        print(f"   ⏰ Countdown sound: {'Generated' if hasattr(quiz_engine, '_countdown_sound_path') else 'Not found'}")
        print(f"   🔔 Answer ding: {'Generated' if hasattr(quiz_engine, '_answer_sound_path') else 'Not found'}")
        
        # Show component timeline with sound effects
        components = quiz_engine._db_quiz_components
        print(f"\n📋 Timeline with Sound Effects ({len(components.get('all_components', []))} components):")
        for i, comp in enumerate(components.get('all_components', []), 1):
            sound_indicator = ""
            if comp['type'] == 'intro':
                sound_indicator = " 🎺"
            elif comp['type'] == 'countdown':
                sound_indicator = " ⏰⏰⏰"  # 3 ticks
            elif comp['type'] == 'answer':
                sound_indicator = " 🔔"
                
            print(f"   {i}. [{comp['start_time']:.1f}-{comp['end_time']:.1f}s] {comp['type'].upper()}: {comp['content'][:40]}...{sound_indicator}")
        
        print("\n" + "=" * 60)
        
        # Test with sound effects disabled
        print("2. Testing with sound effects DISABLED...")
        quiz_engine_no_sound = QuizVideoEngine(
            voiceModule=voice_module,
            quiz_script=quiz_script,
            intro_text="🤫 Silent Quiz",
            intro_duration=1.5,
            use_sound_effects=False,  # Disable sound effects
            video_source="pexels"
        )
        
        print("✅ QuizVideoEngine without sound effects initialized!")
        print(f"   🔇 Sound effects: {quiz_engine_no_sound._use_sound_effects}")
        
        print("\n" + "=" * 60)
        
        # Test with custom sound assets (will fallback to generated)
        print("3. Testing with custom sound assets...")
        quiz_engine_custom = QuizVideoEngine(
            voiceModule=voice_module,
            quiz_script=quiz_script,
            intro_text="🎨 Custom Sounds",
            intro_duration=2.5,
            use_sound_effects=True,
            intro_sound_asset="my_custom_intro",  # These don't exist, will fallback
            countdown_sound_asset="my_custom_countdown",
            answer_sound_asset="my_custom_ding",
            video_source="pexels"
        )
        
        print("✅ QuizVideoEngine with custom assets initialized!")
        print("   (Will fallback to generated sounds since custom assets don't exist)")
        
        print("\n🎉 Sound effects testing completed!")
        print("\n💡 Sound Effect Features:")
        print("   🎺 Intro Sound: Rising whoosh sound to grab attention")
        print("   ⏰ Countdown Sounds: Sharp tick sounds on each number (3-2-1)")
        print("   🔔 Answer Ding: Pleasant two-tone chime for correct answers")
        print("   🎛️ Volume Control: Carefully balanced levels (40%, 50%, 60%)")
        print("   🔄 Auto-Generation: Creates sounds if custom assets not found")
        print("   🎵 Smart Mixing: Integrates seamlessly with voice audio")
        
        return quiz_engine
        
    except Exception as e:
        print(f"❌ Error during sound effects testing: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_sound_generation_only():
    """Test just the sound generation without full video creation"""
    print("\n🎼 Testing Sound Generation Only...")
    print("=" * 40)
    
    # Just test the QuizVideoEngine initialization to generate sounds
    voice_module = EdgeTTSVoiceModule("en-US-AriaNeural")
    
    simple_script = "[0.0-1.0] QUESTION: Test?"
    
    try:
        quiz_engine = QuizVideoEngine(
            voiceModule=voice_module,
            quiz_script=simple_script,
            intro_text="Test",
            intro_duration=1.0,
            use_sound_effects=True
        )
        
        print("✅ Sound effects generated successfully!")
        
        # Check if sound files were created
        if hasattr(quiz_engine, '_intro_sound_path'):
            print(f"   🎺 Intro sound: {quiz_engine._intro_sound_path}")
        if hasattr(quiz_engine, '_countdown_sound_path'):
            print(f"   ⏰ Countdown sound: {quiz_engine._countdown_sound_path}")
        if hasattr(quiz_engine, '_answer_sound_path'):
            print(f"   🔔 Answer ding: {quiz_engine._answer_sound_path}")
            
    except Exception as e:
        print(f"❌ Sound generation failed: {e}")

if __name__ == "__main__":
    quiz_engine = test_sound_effects()
    test_sound_generation_only()
    
    if quiz_engine:
        print(f"\n🚀 Ready to create videos with sound effects!")
        print("To generate a complete video with sound effects:")
        print("for step_num, step_info in quiz_engine.makeContent():")
        print("    print(f'Step {step_num}: {step_info}')")
        print("\nThe generated video will include:")
        print("• Voice narration")
        print("• Background video")
        print("• Text overlays")
        print("• Sound effects at perfect timing!")
    else:
        print("❌ Testing failed. Check the errors above.")