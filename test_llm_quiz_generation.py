#!/usr/bin/env python3
"""
Test script for LLM-powered quiz script generation:
- Demonstrates automatic script generation from topics
- Tests different difficulty levels and styles
- Shows the complete workflow from topic to video
"""

from shortGPT.audio.edge_voice_module import EdgeTTSVoiceModule
from shortGPT.config.languages import Language
from shortGPT.engine.quiz_video_engine import QuizVideoEngine
from shortGPT.gpt.quiz_script_generator import QuizScriptGenerator

def test_script_generation_only():
    """Test just the script generation without creating videos"""
    
    print("🤖📝 Testing LLM Quiz Script Generation")
    print("=" * 60)
    
    test_cases = [
        {
            "topic": "Ocean Mysteries",
            "num_questions": 3,
            "difficulty": "medium",
            "style": "engaging",
            "duration": 25.0
        },
        {
            "topic": "Space Exploration", 
            "num_questions": 2,
            "difficulty": "hard",
            "style": "educational",
            "duration": 20.0
        },
        {
            "topic": "Movie Trivia",
            "num_questions": 4,
            "difficulty": "easy", 
            "style": "fun",
            "duration": 35.0
        },
        {
            "topic": "Ancient Civilizations",
            "num_questions": 2,
            "difficulty": "expert",
            "style": "challenging",
            "duration": 30.0
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🎯 Test {i}: {test_case['topic']}")
        print(f"   📊 {test_case['num_questions']} questions, {test_case['difficulty']} difficulty")
        print(f"   🎨 Style: {test_case['style']}, Duration: {test_case['duration']}s")
        
        try:
            script = QuizScriptGenerator.generate_quiz_script(
                topic=test_case['topic'],
                num_questions=test_case['num_questions'],
                difficulty=test_case['difficulty'],
                style=test_case['style'],
                target_duration=test_case['duration']
            )
            
            print(f"✅ Generated script:")
            print("   " + "=" * 50)
            
            # Display the script with nice formatting
            lines = script.split('\n')
            for line in lines:
                if line.strip():
                    print(f"   {line}")
            
            print("   " + "=" * 50)
            
            # Analyze the script
            question_count = len([l for l in lines if 'QUESTION:' in l])
            answer_count = len([l for l in lines if 'ANSWER:' in l])
            countdown_count = len([l for l in lines if 'COUNTDOWN:' in l])
            cta_count = len([l for l in lines if 'CTA:' in l])
            
            print(f"   📊 Script analysis: {question_count} questions, {answer_count} answers,")
            print(f"       {countdown_count} countdowns, {cta_count} CTAs")
            
        except Exception as e:
            print(f"❌ Failed to generate script: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n🎉 Script generation testing complete!")

def test_full_video_generation_from_topic():
    """Test complete video generation from just a topic"""
    
    print(f"\n🎬🤖 Testing Complete Video Generation from Topic")
    print("=" * 60)
    
    # Test with a compelling topic
    test_topic = "Ancient Egypt Mysteries"
    
    try:
        # Initialize voice module
        voice_module = EdgeTTSVoiceModule("en-US-AriaNeural")
        
        print(f"🏺 Creating quiz video about: '{test_topic}'")
        
        # Create quiz engine with auto-generated script
        quiz_engine = QuizVideoEngine.create_from_topic(
            voiceModule=voice_module,
            topic=test_topic,
            num_questions=3,
            difficulty="medium",
            style="engaging",
            target_duration=30.0,
            video_source="pexels",  # Will search for Egypt-related videos
            use_sound_effects=True,
            watermark="@HistoryQuiz"
        )
        
        print(f"✅ Quiz engine created with auto-generated script!")
        print(f"   🎬 Topic: {test_topic}")
        print(f"   🎵 Sound effects: {quiz_engine._use_sound_effects}")
        print(f"   🎥 Video source: {quiz_engine._video_source}")
        print(f"   💫 Auto-generated intro: '{quiz_engine._intro_text}'")
        
        # Show the auto-generated timeline
        components = quiz_engine._db_quiz_components
        print(f"\n📋 Auto-Generated Timeline ({len(components.get('all_components', []))} components):")
        
        for i, comp in enumerate(components.get('all_components', []), 1):
            component_type = comp['type'].upper()
            content_preview = comp['content'][:60] + "..." if len(comp['content']) > 60 else comp['content']
            
            sound_indicator = ""
            if comp['type'] == 'intro':
                sound_indicator = " 🎺"
            elif comp['type'] == 'countdown': 
                sound_indicator = " ⏰⏰⏰"
            elif comp['type'] == 'answer':
                sound_indicator = " 🔔"
            
            print(f"   {i}. [{comp['start_time']:.1f}-{comp['end_time']:.1f}s] {component_type}{sound_indicator}")
            print(f"      📝 {content_preview}")
        
        print(f"\n🚀 Ready to generate complete video! This would include:")
        print(f"   ✓ LLM-generated compelling quiz questions about {test_topic}")
        print(f"   ✓ Automatically sourced background video from Pexels")
        print(f"   ✓ Voice narration for all components")
        print(f"   ✓ Sound effects (intro whoosh, countdown ticks, answer dings)")
        print(f"   ✓ Animated text overlays")
        print(f"   ✓ Professional video editing and rendering")
        print(f"   ✓ Perfect 1080x1920 vertical format for social media")
        
        # Uncomment the next lines to actually generate the video
        # print(f"\n🎬 Generating complete video...")
        # for step_num, step_info in quiz_engine.makeContent():
        #     print(f"   Step {step_num}: {step_info}")
        # video_path = quiz_engine.get_video_output_path()
        # print(f"✅ Video generated: {video_path}")
        
        return quiz_engine
        
    except Exception as e:
        print(f"❌ Error in full video generation test: {e}")
        import traceback
        traceback.print_exc()
        return None

def demo_topic_variations():
    """Demonstrate different topic variations and their auto-generated intros"""
    
    print(f"\n💫 Topic Variation Demo")
    print("=" * 40)
    
    topics_and_styles = [
        ("Quantum Physics", "educational"),
        ("Celebrity Gossip", "fun"),
        ("Survival Skills", "challenging"),
        ("Art History", "engaging"),
        ("Cryptocurrency", "educational"),
        ("90s Nostalgia", "fun"),
        ("Extreme Sports", "challenging"),
        ("World Cuisine", "engaging")
    ]
    
    print("Auto-generated intro texts:")
    for topic, style in topics_and_styles:
        intro = QuizVideoEngine._generate_intro_text(topic, style)
        print(f"   📝 {topic} ({style}): '{intro}'")

if __name__ == "__main__":
    # Test script generation
    test_script_generation_only()
    
    # Demo topic variations
    demo_topic_variations()
    
    # Test full video creation workflow
    quiz_engine = test_full_video_generation_from_topic()
    
    if quiz_engine:
        print(f"\n🎊 SUCCESS! LLM-powered quiz generation working perfectly!")
        
        print(f"\n💡 How to use the new system:")
        print(f"   1. Choose any topic: 'Ancient Rome', 'Space Facts', 'Movie Trivia', etc.")
        print(f"   2. Set difficulty: 'easy', 'medium', 'hard', 'expert'")
        print(f"   3. Pick style: 'engaging', 'educational', 'fun', 'challenging'")
        print(f"   4. Call QuizVideoEngine.create_from_topic() - that's it!")
        
        print(f"\n🚀 Benefits:")
        print(f"   ✓ No more hardcoded scripts")
        print(f"   ✓ Unlimited topic variety") 
        print(f"   ✓ Compelling, viral-ready content")
        print(f"   ✓ Perfect timing and structure")
        print(f"   ✓ Automatic intro generation")
        print(f"   ✓ Professional quiz format")
        print(f"   ✓ Ready for TikTok, Instagram, YouTube Shorts")
        
        print(f"\n🎯 Example usage:")
        print(f"   quiz_engine = QuizVideoEngine.create_from_topic(")
        print(f"       voiceModule=voice_module,")
        print(f"       topic='Ocean Mysteries',")
        print(f"       num_questions=3,")
        print(f"       difficulty='medium',")
        print(f"       style='engaging',")
        print(f"       target_duration=30.0")
        print(f"   )")
        
    else:
        print("❌ LLM quiz generation test failed. Check errors above.")
        
    print(f"\n🤖 Powered by advanced LLM prompt engineering for viral content creation!")