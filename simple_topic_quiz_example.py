#!/usr/bin/env python3
"""
Simple example showing how to create quiz videos from any topic using LLM generation.
Just specify a topic and the system generates compelling quiz content automatically!
"""

from shortGPT.audio.edge_voice_module import EdgeTTSVoiceModule
from shortGPT.engine.quiz_video_engine import QuizVideoEngine

def create_quiz_from_topic(topic: str):
    """
    Create a complete quiz video from just a topic name.
    
    Args:
        topic: Any subject you want to create a quiz about
    """
    
    print(f"🚀 Creating quiz video about: '{topic}'")
    
    # Initialize voice module
    voice_module = EdgeTTSVoiceModule("en-US-AriaNeural")
    
    # Create quiz engine with auto-generated script - it's that simple!
    quiz_engine = QuizVideoEngine.create_from_topic(
        voiceModule=voice_module,
        topic=topic,                    # 🎯 Just specify your topic!
        num_questions=3,                # How many questions?
        difficulty="extreme",            # easy/medium/hard/expert
        style="engaging",               # engaging/educational/fun/challenging
        target_duration=30.0,           # Video length in seconds
        video_source="pexels",          # Auto-finds relevant background videos
        use_sound_effects=True,         # Adds intro/countdown/answer sounds
        watermark="@QuizMaster"         # Your brand watermark
    )
    
    print(f"✅ Quiz engine created with LLM-generated content!")
    print(f"   🎬 Topic: {topic}")
    print(f"   💫 Auto-generated intro: '{quiz_engine._intro_text}'")
    
    # Show what was auto-generated
    components = quiz_engine._db_quiz_components
    print(f"\n📋 Auto-Generated Content Preview:")
    
    for i, comp in enumerate(components.get('all_components', [])[:5], 1):  # Show first 5
        content_preview = comp['content'][:50] + "..." if len(comp['content']) > 50 else comp['content']
        print(f"   {i}. [{comp['start_time']:.1f}s] {comp['type'].upper()}: {content_preview}")
    
    print(f"\n🎬 To generate the complete video:")
    print(f"   for step_num, step_info in quiz_engine.makeContent():")
    print(f"       print(f'Step {{step_num}}: {{step_info}}')")
    print(f"   video_path = quiz_engine.get_video_output_path()")
    
    return quiz_engine

if __name__ == "__main__":
    # Examples of different topics you can use
    example_topics = [
        "Ocean Mysteries",
        "Space Exploration", 
        "Ancient Egypt",
        "Movie Trivia",
        "Science Facts",
        "World Geography",
        "Food Culture",
        "Technology History",
        "Animal Kingdom",
        "Art Masterpieces"
    ]
    
    print("🤖 LLM-Powered Quiz Video Generation")
    print("=" * 50)
    print("Create engaging quiz videos from ANY topic!")
    print()
    
    # Demo with one topic
    selected_topic = "Ocean Mysteries"
    quiz_engine = create_quiz_from_topic(selected_topic)
    
    print(f"\n💡 Try these other topics:")
    for topic in example_topics:
        if topic != selected_topic:
            print(f"   • {topic}")
    
    print(f"\n🎯 Usage is simple:")
    print(f"   1. Pick any topic")
    print(f"   2. Call QuizVideoEngine.create_from_topic()")
    print(f"   3. Generate video with quiz_engine.makeContent()")
    print(f"   4. Done! ✨")
    
    print(f"\n🚀 The LLM automatically creates:")
    print(f"   ✓ Compelling quiz questions")
    print(f"   ✓ Surprising facts and answers")
    print(f"   ✓ Perfect timing structure")
    print(f"   ✓ Engaging intro animations")
    print(f"   ✓ Viral-ready content")
    print(f"   ✓ Professional quiz format")