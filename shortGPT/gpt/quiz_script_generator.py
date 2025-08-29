"""
Quiz Script Generator using LLM
Generates compelling quiz scripts with proper timing for the QuizVideoEngine
"""

from shortGPT.gpt.gpt_utils import llm_completion
import re
from typing import Dict, Any, Optional


class QuizScriptGenerator:
    """Generate compelling quiz scripts using LLM for any topic"""
    
    @staticmethod
    def generate_multi_difficulty_scripts(
        topic: str,
        num_questions: int = 3,
        style: str = "engaging",
        target_duration: float = 30.0,
    ) -> Dict[str, str]:
        """
        Generate three DISTINCT quiz scripts for a topic in a single LLM call:
        one each for easy, medium, and hard difficulties. Ensures no duplicate
        questions across the three scripts by instructing the model accordingly.

        Returns a dict with keys: "easy", "medium", "hard" and values being
        the processed scripts in the expected timestamped format.
        """
        # Compute one timing template to be reused for all difficulties
        timing = QuizScriptGenerator._calculate_timing(num_questions, target_duration)

        system_prompt = f"""You are an expert quiz content creator for viral short videos.
You must produce THREE complete scripts in one response: EASY, MEDIUM, and HARD.

GLOBAL REQUIREMENTS (apply to all three scripts):
1. Use EXACT timing format: [start-end] COMPONENT: content
2. Follow this structure and the timing specs strictly
3. All facts must be 100% accurate and verifiable; avoid disputed claims
4. No question overlap or paraphrased duplicates between difficulties
5. Style: {style}
6. Topic: {topic}
7. Questions/answers/CTAs must be fit the allowed timing, with reading time of around 150 words per minute. DO NOT use long sentences.
8. Add brief explanations to the answers to make them more engaging.
9. Use universally accepted facts, avoid current/volatile records
10. In CTA promote the app "Witz" with a link in bio.

TIMING (reuse for each difficulty):
- Intro: {timing['intro_duration']:.1f}s
- Question: {timing['question_duration']:.1f}s each
- Countdown: {timing['countdown_duration']:.1f}s (always "3-2-1")
- Answer: {timing['answer_duration']:.1f}s each
- Final CTAs total: {timing['final_cta_duration']:.1f}s

OUTPUT FORMAT (strict):
<<<EASY>>>
[timestamped lines for full script]
<<<MEDIUM>>>
[timestamped lines for full script]
<<<HARD>>>
[timestamped lines for full script]
Return ONLY the scripts in this exact marker-separated format, nothing else."""

        # Build a compact structure template we can reuse across the three scripts
        def build_structure_template() -> str:
            current_time = 0.0
            lines = []
            # Intro
            intro_end = current_time + timing['intro_duration']
            lines.append(f"[{current_time:.1f}-{intro_end:.1f}] CTA: [Compelling intro about {topic}, mentioning that there are {num_questions} questions]")
            current_time = intro_end
            # Questions
            for i in range(num_questions):
                q_end = current_time + timing['question_duration']
                lines.append(f"[{current_time:.1f}-{q_end:.1f}] QUESTION: [Question {i+1}]")
                current_time = q_end
                c_end = current_time + timing['countdown_duration']
                lines.append(f"[{current_time:.1f}-{c_end:.1f}] COUNTDOWN: 3-2-1")
                current_time = c_end
                a_end = current_time + timing['answer_duration']
                lines.append(f"[{current_time:.1f}-{a_end:.1f}] ANSWER: [Answer {i+1}]")
                current_time = a_end
                if i == 0:
                    lines.append(f"[{current_time:.1f}-{current_time + 1.5}] CTA: [View profile for quiz like this CTA]")
                    current_time = current_time + 1.5
            # CTAs
            cta_half = timing['final_cta_duration'] / 2
            cta1_end = current_time + cta_half
            lines.append(f"[{current_time:.1f}-{cta1_end:.1f}] CTA: [Engagement CTA]")
            cta2_end = cta1_end + cta_half
            lines.append(f"[{cta1_end:.1f}-{cta2_end:.1f}] CTA: [App/follow CTA]")
            return "\n".join(lines)

        structure_template = build_structure_template()

        user_prompt = f"""Create THREE complete {style} quiz scripts about: {topic}
- Each script must contain {num_questions} questions
- Difficulties: EASY, MEDIUM, HARD (in that order)
- Absolutely NO duplicate or paraphrased questions across scripts
- All questions must have single, unambiguous correct answers
- Add very short and brief explanations to the answers to make them more engaging.
- Fit the same timing template per script
- In CTA promote the app "Witz" with a link in bio.

Use this structure for EACH difficulty (timings reset to 0.0 for each script):
{structure_template}

Now output the three scripts separated by the exact markers: <<<EASY>>>, <<<MEDIUM>>>, <<<HARD>>>"""

        # Call LLM once
        combined = llm_completion(
            chat_prompt=user_prompt,
            system=system_prompt,
            temp=0.8,
            max_tokens=18000,
            remove_nl=False,
            gemini=True,
        )

        # Split by markers and post-process
        import re as _re
        parts = {
            'easy': '',
            'medium': '',
            'hard': ''
        }
        # Create safe splits
        # We expect markers as standalone lines; handle possible extra whitespace
        def extract_section(marker: str, text: str) -> Optional[str]:
            pattern = _re.compile(rf"<<<{marker}>>>\s*(.*?)\s*(?:(?:<<<|\Z))", _re.DOTALL | _re.IGNORECASE)
            m = pattern.search(text)
            return m.group(1).strip() if m else None

        easy_raw = extract_section('EASY', combined) or ''
        med_raw = extract_section('MEDIUM', combined) or ''
        hard_raw = extract_section('HARD', combined) or ''

        # Post-process each using existing validator
        parts['easy'] = QuizScriptGenerator._post_process_script(easy_raw, timing) if easy_raw else QuizScriptGenerator._create_fallback_script(f"{topic} (easy)", timing)
        parts['medium'] = QuizScriptGenerator._post_process_script(med_raw, timing) if med_raw else QuizScriptGenerator._create_fallback_script(f"{topic} (medium)", timing)
        parts['hard'] = QuizScriptGenerator._post_process_script(hard_raw, timing) if hard_raw else QuizScriptGenerator._create_fallback_script(f"{topic} (hard)", timing)

        return parts

    @staticmethod
    def generate_quiz_script(topic: str, 
                           num_questions: int = 3,
                           difficulty: str = "medium",
                           style: str = "engaging",
                           target_duration: float = 30.0) -> str:
        """
        Generate a compelling quiz script for the given topic.
        
        Args:
            topic: The subject/theme for the quiz (e.g., "Geography", "Space Facts", "Movie Trivia")
            num_questions: Number of quiz questions to generate (1-5 recommended)
            difficulty: Difficulty level - "easy", "medium", "hard", "expert"
            style: Style of quiz - "engaging", "educational", "fun", "challenging"
            target_duration: Target video duration in seconds
            
        Returns:
            Formatted quiz script with precise timing
        """
        
        # Calculate timing based on target duration and number of questions
        timing = QuizScriptGenerator._calculate_timing(num_questions, target_duration)
        
        # Create the system prompt for optimal quiz generation
        system_prompt = QuizScriptGenerator._create_system_prompt(timing, style, difficulty)
        
        # Create the user prompt with topic and requirements
        user_prompt = QuizScriptGenerator._create_user_prompt(
            topic, num_questions, difficulty, style, timing
        )
        
        try:
            # Generate the script using LLM
            print(f"🤖 Generating {difficulty} {style} quiz script about '{topic}'...")
            print(f"   📊 {num_questions} questions, ~{target_duration:.1f}s duration")
            
            script = llm_completion(
                chat_prompt=user_prompt,
                system=system_prompt,
                temp=0.9,  # Higher temperature for creativity
                max_tokens=15000,
                remove_nl=False,
                gemini=True # Keep formatting
            )
            
            # Post-process and validate the script
            processed_script = QuizScriptGenerator._post_process_script(script, timing)
            
            print(f"✅ Quiz script generated successfully!")
            return processed_script
            
        except Exception as e:
            print(f"❌ Error generating quiz script: {e}")
            # Return a fallback script
            return QuizScriptGenerator._create_fallback_script(topic, timing)
    
    @staticmethod
    def _calculate_timing(num_questions: int, target_duration: float) -> Dict[str, float]:
        """Calculate optimal timing for quiz components"""
        
        # Reserve time for intro and final CTA
        intro_duration = 5.0
        final_cta_duration = 8.0
        available_time = target_duration - intro_duration - final_cta_duration
        
        # Time per question cycle (question + countdown + answer)
        time_per_question = available_time / num_questions
        
        # Distribute time within each question cycle
        question_duration = time_per_question * 0.45  # 45% for question
        countdown_duration = 2  # Fixed countdown time
        answer_duration = time_per_question * 0.45 # 45% for answer
        padding = time_per_question * 0.1  # 10% padding
        
        return {
            'intro_duration': intro_duration,
            'question_duration': max(2.0, question_duration),
            'countdown_duration': countdown_duration,
            'answer_duration': max(2.0, answer_duration + padding),
            'final_cta_duration': final_cta_duration,
            'total_duration': target_duration
        }
    
    @staticmethod
    def _create_system_prompt(timing: Dict[str, float], style: str, difficulty: str) -> str:
        """Create the system prompt for LLM"""
        return f"""You are an expert quiz content creator specializing in viral social media videos. Your task is to create compelling, {style} quiz scripts that grab attention and keep viewers engaged.

CRITICAL REQUIREMENTS:
1. Use EXACT timing format: [start_time-end_time] COMPONENT_TYPE: content
2. Follow the precise structure and timing provided
3. ALL questions and answers MUST be 100% factually accurate and verifiable from authoritative sources
4. ONLY use well-established, universally accepted facts - avoid controversial or disputed information
5. Double and triple check every fact, date, number, and claim before including it
6. For numerical answers, use exact figures from verified sources
7. ALL questions must be 15 words or less
8. ALL answers must be 15 words or less
9. ALL CTA content must be 15 words or less
10. Make questions {difficulty} difficulty level
11. Use {style} tone throughout
12. Include engaging hooks, surprising facts, and compelling answers, but be concise.
13. Keep content concise but impactful
14. The length of the text should match the timing allowed, since a human will be reading it. Use short sentences or increase timings.
15. Prefer questions about concrete, objective facts rather than subjective or interpretive topics
16. Include sources in your internal verification but do not include them in the output


FACT VERIFICATION REQUIREMENTS:
- Geography: Use official government data, UN sources, or reputable atlases
- History: Use established historical consensus and verified dates
- Science: Use peer-reviewed sources and accepted scientific facts
- Sports: Use official league/organization records
- Pop culture: Use verified release dates, box office numbers, or award records
- Avoid: "Fastest", "biggest", "most popular" unless you can verify with current, authoritative data

TIMING SPECIFICATIONS:
- Intro duration: {timing['intro_duration']:.1f}s
- Question duration: {timing['question_duration']:.1f}s each
- Countdown duration: {timing['countdown_duration']:.1f}s (always "3-2-1")
- Answer duration: {timing['answer_duration']:.1f}s each
- Final CTA duration: {timing['final_cta_duration']:.1f}s

ENGAGEMENT TACTICS:
- Start with attention-grabbing intro
- Use VERIFIED facts
- End with strong call-to-action

OUTPUT FORMAT:
Return ONLY the formatted script with precise timestamps. No explanations or additional text."""

    @staticmethod
    def _create_user_prompt(topic: str, num_questions: int, difficulty: str, 
                          style: str, timing: Dict[str, float]) -> str:
        """Create the user prompt with specific requirements"""
        
        # Calculate cumulative timing
        current_time = 0.0
        
        # Build example timing structure
        example_structure = f"[{current_time:.1f}-{current_time + timing['intro_duration']:.1f}] CTA: [Compelling intro hook about {topic}, mentioning that there are {num_questions} questions]\n"
        current_time += timing['intro_duration']
        
        for i in range(num_questions):
            # Question
            question_start = current_time
            question_end = current_time + timing['question_duration']
            example_structure += f"[{question_start:.1f}-{question_end:.1f}] QUESTION: [Engaging question {i+1}]\n"
            current_time = question_end
            
            # Countdown
            countdown_start = current_time
            countdown_end = current_time + timing['countdown_duration']
            example_structure += f"[{countdown_start:.1f}-{countdown_end:.1f}] COUNTDOWN: 3-2-1\n"
            current_time = countdown_end
            
            # Answer
            answer_start = current_time
            answer_end = current_time + timing['answer_duration']
            example_structure += f"[{answer_start:.1f}-{answer_end:.1f}] ANSWER: [Exciting answer]\n"
            current_time = answer_end

            if i == 0:
                example_structure += f"[{current_time:.1f}-{current_time + 1.5}] CTA: [View profile for quiz like this CTA]\n"
                current_time = current_time + 1.5
        
        # Final CTAs
        cta_duration = timing['final_cta_duration'] / 2
        cta1_start = current_time
        cta1_end = current_time + cta_duration
        example_structure += f"[{cta1_start:.1f}-{cta1_end:.1f}] CTA: [Engagement call-to-action]\n"
        
        cta2_start = cta1_end
        cta2_end = cta2_start + cta_duration
        example_structure += f"[{cta2_start:.1f}-{cta2_end:.1f}] CTA: [App/follow call-to-action]"
        
        return f"""Create a compelling {style} quiz script about: {topic}

REQUIREMENTS:
- {num_questions} questions, {difficulty} difficulty
- Topic: {topic}
- Style: {style} and engaging
- Total duration: ~{timing['total_duration']:.1f} seconds
- Questions and answers must be 100% FACTUALLY CORRECT and VERIFIABLE
- Be creative with the questions and answers, but make sure they are factually correct.

STRUCTURE TO FOLLOW:
{example_structure}

CONTENT GUIDELINES:
- Intro: Hook viewers with excitement about the topic
- Questions: {difficulty} level, surprising/interesting facts
- CTAs: Encourage engagement and app downloads, link in bio
- App name is "witz"
- Questions must be at most 15 words
- Answers must be at most 15 words
- CTAs must be at most 15 words
- Text should be short and concise, use short sentences or increase timings.
- Use questions and answers that are appropriate length for the timing allowed.

CRITICAL ACCURACY REQUIREMENTS:
- ONLY use questions with answers that are UNIVERSALLY ACKNOWLEDGED as correct
- Avoid controversial, subjective, or debatable topics
- Use well-documented historical facts, scientific facts, or mathematical certainties
- Double-check all numerical data, dates, and statistics
- Prefer questions with single, unambiguous correct answers
- Avoid questions about current events, records that change frequently, or disputed claims
- When in doubt about accuracy, choose a different question
- All facts must be verifiable through multiple reliable sources

EXAMPLES OF RELIABLE QUESTION TYPES:
- Mathematical facts (e.g., "What is 7 x 8?")
- Basic geography (e.g., "What is the capital of France?")
- Well-established historical dates (e.g., "In what year did World War II end?")
- Scientific constants (e.g., "How many bones are in an adult human body?")
- Uncontested world records or measurements

Generate the complete script following this exact timing and format:"""

    @staticmethod
    def _post_process_script(script: str, timing: Dict[str, float]) -> str:
        """Post-process and validate the generated script"""
        
        # Clean up any formatting issues
        script = script.strip()
        
        # Ensure proper line breaks
        script = re.sub(r'\n+', '\n', script)
        
        # Validate timing format
        lines = script.split('\n')
        processed_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if line has proper timing format
            if re.match(r'^\[\d+\.\d+-\d+\.\d+\]', line):
                processed_lines.append(line)
            elif line.startswith('[') and ']' in line:
                # Try to fix minor formatting issues
                processed_lines.append(line)
            else:
                # Skip lines that don't match format
                continue
        
        result = '\n'.join(processed_lines)
        
        # Validate we have the minimum required components
        if 'ANSWER:' not in result or 'QUESTION:' not in result or 'COUNTDOWN:' not in result:
            print("⚠️  Generated script missing required components, using fallback...")
            return QuizScriptGenerator._create_fallback_script("General Knowledge", timing)
        
        return result
    
    @staticmethod
    def _create_fallback_script(topic: str, timing: Dict[str, float]) -> str:
        """Create a fallback script if LLM generation fails"""
        current_time = 0.0
        
        script_lines = []
        
        # Intro
        intro_end = current_time + timing['intro_duration']
        script_lines.append(f"[{current_time:.1f}-{intro_end:.1f}] ANSWER: 🧠 Ready for an amazing {topic} challenge?")
        current_time = intro_end
        
        # Sample question
        question_end = current_time + timing['question_duration']
        script_lines.append(f"[{current_time:.1f}-{question_end:.1f}] QUESTION: Can you answer this {topic} question?")
        current_time = question_end
        
        # Countdown
        countdown_end = current_time + timing['countdown_duration']
        script_lines.append(f"[{current_time:.1f}-{countdown_end:.1f}] COUNTDOWN: 3-2-1")
        current_time = countdown_end
        
        # Answer
        answer_end = current_time + timing['answer_duration']
        script_lines.append(f"[{current_time:.1f}-{answer_end:.1f}] ANSWER: Great job! 🎉 That's correct!")
        current_time = answer_end
        
        # CTAs
        cta_duration = timing['final_cta_duration'] / 2
        cta1_end = current_time + cta_duration
        script_lines.append(f"[{current_time:.1f}-{cta1_end:.1f}] CTA: Like if you learned something new!")
        current_time = cta1_end
        
        cta2_end = current_time + cta_duration
        script_lines.append(f"[{current_time:.1f}-{cta2_end:.1f}] CTA: Follow for more {topic} facts!")
        
        return '\n'.join(script_lines)


def test_script_generation():
    """Test the quiz script generator with different topics"""
    
    test_topics = [
        ("Space Facts", 2, "medium", "educational"),
        ("Movie Trivia", 3, "hard", "fun"),
        ("Geography", 2, "easy", "engaging"),
        ("Science Mysteries", 3, "expert", "challenging")
    ]
    
    print("🎬 Testing Quiz Script Generator")
    print("=" * 50)
    
    for topic, num_q, difficulty, style in test_topics:
        print(f"\n📝 Generating {difficulty} {style} quiz about '{topic}'...")
        
        try:
            script = QuizScriptGenerator.generate_quiz_script(
                topic=topic,
                num_questions=num_q,
                difficulty=difficulty,
                style=style,
                target_duration=25.0
            )
            
            print(f"✅ Generated script preview:")
            # Show first few lines
            lines = script.split('\n')[:3]
            for line in lines:
                print(f"   {line}")
            print(f"   ... ({len(script.split(chr(10)))} total lines)")
            
        except Exception as e:
            print(f"❌ Failed to generate script: {e}")
    
    print(f"\n🎉 Script generation testing complete!")


if __name__ == "__main__":
    test_script_generation()