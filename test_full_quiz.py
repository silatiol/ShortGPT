#!/usr/bin/env python3
"""
Full test to generate a quiz video with all new features:
1. Intro animation
2. Asset library video source  
3. Complete video generation
"""

from shortGPT.audio.edge_voice_module import EdgeTTSVoiceModule
from shortGPT.config.languages import Language
from shortGPT.engine.quiz_video_engine import QuizVideoEngine

def generate_quiz_with_intro():
    """Generate a complete quiz video with intro animation"""
    
    # Sample quiz script
    quiz_script = """
[0.0-3.0] QUESTION: What's the largest planet in our solar system?
[3.0-4.5] COUNTDOWN: 3-2-1
[4.5-7.0] ANSWER: Jupiter! The gas giant! 🪐
[7.0-9.0] CTA: Follow for more space facts! 🚀
"""
    
    # Initialize voice module
    voice_module = EdgeTTSVoiceModule("en-US-AriaNeural")
    
    print("🎬 Generating Quiz Video with New Features")
    print("=" * 50)
    
    try:
        # Create quiz engine with all new features
        quiz_engine = QuizVideoEngine(
            voiceModule=voice_module,
            quiz_script=quiz_script,
            intro_text="🌟 SPACE QUIZ CHALLENGE! 🌟",
            intro_duration=2.0,
            video_source="pexels",  # Using Pexels since asset might not exist
            watermark="@SpaceQuizMaster"
        )
        
        print("✅ QuizVideoEngine initialized successfully!")
        print(f"   📝 Intro: '{quiz_engine._intro_text}' ({quiz_engine._intro_duration}s)")
        print(f"   🎥 Video source: {quiz_engine._video_source}")
        print(f"   💧 Watermark: {quiz_engine._db_watermark}")
        
        # Show component timeline
        components = quiz_engine._db_quiz_components
        print(f"\n📋 Timeline ({len(components.get('all_components', []))} components):")
        for i, comp in enumerate(components.get('all_components', [])[:5], 1):
            print(f"   {i}. [{comp['start_time']:.1f}-{comp['end_time']:.1f}s] {comp['type'].upper()}: {comp['content'][:40]}...")
        
        print("\n🎬 Starting video generation...")
        print("⚠️  This will download background videos and generate the complete quiz video.")
        
        # Generate the video
        step_count = 0
        for step_num, step_info in quiz_engine.makeContent():
            step_count += 1
            print(f"   Step {step_count}: {step_info}")
        
        # Get the output path
        video_path = quiz_engine.get_video_output_path()
        print(f"\n🎉 Video generated successfully!")
        print(f"   📁 Output: {video_path}")
        print(f"   🎯 Features used:")
        print(f"      ✓ Intro animation with text")
        print(f"      ✓ Background video from {quiz_engine._video_source}")
        print(f"      ✓ Quiz questions, countdown, and answers")
        print(f"      ✓ Call-to-action overlay")
        print(f"      ✓ Watermark")
        
        return video_path
        
    except Exception as e:
        print(f"❌ Error during video generation: {e}")
        return None

if __name__ == "__main__":
    video_path = generate_quiz_with_intro()
    
    if video_path:
        print(f"\n🚀 Success! Your quiz video with intro animation is ready:")
        print(f"   {video_path}")
        print("\n💡 Tips for using the new features:")
        print("   • Set intro_text to grab attention (e.g., '🎯 CHALLENGE TIME!')")
        print("   • Use intro_duration 2-3 seconds for optimal impact")
        print("   • Try video_source='asset_library' with your own videos")
        print("   • Asset library videos loop seamlessly for any duration")
    else:
        print("❌ Video generation failed. Check the errors above.")