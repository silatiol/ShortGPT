#!/usr/bin/env python3
"""
Complete test to generate a quiz video with all sound effects:
1. Intro whoosh sound with animation
2. Countdown tick sounds (3-2-1)
3. Answer ding sound for correct answer
4. All integrated with voice narration and background video
"""

from shortGPT.audio.edge_voice_module import EdgeTTSVoiceModule
from shortGPT.config.languages import Language
from shortGPT.engine.quiz_video_engine import QuizVideoEngine

def generate_quiz_with_sound_effects():
    """Generate a complete quiz video with sound effects"""
    
    # Sample quiz script
    quiz_script = """
[0.0-3.0] QUESTION: Which planet is known as the Red Planet?
[3.0-4.5] COUNTDOWN: 3-2-1
[4.5-7.0] ANSWER: Mars! Named for its rusty red color! 🔴
[7.0-9.0] CTA: Like if you got it right! 🚀
"""
    
    # Initialize voice module
    voice_module = EdgeTTSVoiceModule("en-US-AriaNeural")
    
    print("🎬🎵 Generating Complete Quiz Video with Sound Effects")
    print("=" * 65)
    
    try:
        # Create quiz engine with all features including sound effects
        quiz_engine = QuizVideoEngine(
            voiceModule=voice_module,
            quiz_script=quiz_script,
            intro_text="🚀 SPACE QUIZ CHALLENGE! 🌟",
            intro_duration=2.5,
            video_source="pexels",
            use_sound_effects=True,  # Enable all sound effects
            watermark="@SpaceQuizMaster"
        )
        
        print("✅ QuizVideoEngine with sound effects initialized!")
        print(f"   📝 Intro: '{quiz_engine._intro_text}' ({quiz_engine._intro_duration}s)")
        print(f"   🎥 Video source: {quiz_engine._video_source}")
        print(f"   🎵 Sound effects: {quiz_engine._use_sound_effects}")
        print(f"   💧 Watermark: {quiz_engine._db_watermark}")
        
        # Show detailed timeline with sound effects
        components = quiz_engine._db_quiz_components
        print(f"\n📋 Complete Timeline ({len(components.get('all_components', []))} components):")
        
        for i, comp in enumerate(components.get('all_components', []), 1):
            sound_desc = ""
            if comp['type'] == 'intro':
                sound_desc = " + 🎺 Rising whoosh sound"
            elif comp['type'] == 'countdown':
                sound_desc = " + ⏰ Tick sound on each number (3-2-1)"
            elif comp['type'] == 'answer':
                sound_desc = " + 🔔 Pleasant ding chime"
                
            print(f"   {i}. [{comp['start_time']:.1f}-{comp['end_time']:.1f}s] {comp['type'].upper()}")
            print(f"      📝 Text: {comp['content']}")
            print(f"      🎙️ Voice narration{sound_desc}")
            print()
        
        print("🎬 Starting complete video generation with sound effects...")
        print("⚠️  This will create voice audio, download background video, generate sound effects,")
        print("    mix all audio tracks, add visual overlays, and render the final video.")
        print()
        
        # Generate the complete video
        step_count = 0
        for step_num, step_info in quiz_engine.makeContent():
            step_count += 1
            print(f"   Step {step_count}: {step_info}")
        
        # Get the output path
        video_path = quiz_engine.get_video_output_path()
        print(f"\n🎉 Complete video with sound effects generated successfully!")
        print(f"   📁 Output: {video_path}")
        
        print(f"\n🎯 Features included in this video:")
        print(f"   ✓ Intro animation with attention-grabbing whoosh sound")
        print(f"   ✓ Quiz question display")
        print(f"   ✓ Countdown with tick sounds building tension")
        print(f"   ✓ Answer reveal with satisfying ding sound")
        print(f"   ✓ Call-to-action overlay")
        print(f"   ✓ Background video from {quiz_engine._video_source}")
        print(f"   ✓ Voice narration mixed with sound effects")
        print(f"   ✓ Watermark throughout")
        print(f"   ✓ Vertical 1080x1920 format for social media")
        
        print(f"\n🎵 Sound Effects Details:")
        if hasattr(quiz_engine, '_intro_sound_path'):
            print(f"   🎺 Intro: {quiz_engine._intro_sound_path}")
        if hasattr(quiz_engine, '_countdown_sound_path'):
            print(f"   ⏰ Countdown: {quiz_engine._countdown_sound_path}")
        if hasattr(quiz_engine, '_answer_sound_path'):
            print(f"   🔔 Answer: {quiz_engine._answer_sound_path}")
        
        return video_path
        
    except Exception as e:
        print(f"❌ Error during video generation: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    video_path = generate_quiz_with_sound_effects()
    
    if video_path:
        print(f"\n🚀 SUCCESS! Your complete quiz video with sound effects is ready!")
        print(f"   {video_path}")
        
        print(f"\n🎊 What makes this special:")
        print(f"   • Grabs attention with intro animation + whoosh sound")
        print(f"   • Builds tension with countdown tick sounds")
        print(f"   • Rewards viewers with satisfying answer ding")
        print(f"   • Professional audio mixing balances all elements")
        print(f"   • Perfect for TikTok, Instagram Reels, YouTube Shorts")
        
        print(f"\n💡 Customization options for future videos:")
        print(f"   • Change intro_text for different themes")
        print(f"   • Adjust intro_duration (2-3 seconds recommended)")
        print(f"   • Use custom sound assets from your library")
        print(f"   • Disable sound effects with use_sound_effects=False")
        print(f"   • Mix with background video from asset library")
        
    else:
        print("❌ Video generation failed. Check the errors above.")
        
    print(f"\n🔊 Pro tip: The sound effects are carefully volume-balanced:")
    print(f"   • Intro sound: 40% volume (attention without overpowering)")
    print(f"   • Countdown ticks: 50% volume (tension building)")
    print(f"   • Answer ding: 60% volume (satisfying reward)")
    print(f"   • Voice narration: 100% volume (primary content)")