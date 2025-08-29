# Quiz Structure Guide for QuizVideoEngine

## Expected Format

The QuizVideoEngine expects a time-stamped quiz script with specific components in this format:

```
[start_time-end_time] COMPONENT_TYPE: Content text
```

## Required Components

### 1. QUESTION (Required)
The quiz question that appears at the top of the video.

**Format:**
```
[start_time-end_time] QUESTION: Your question text here?
```

**Example:**
```
[0.0-5.0] QUESTION: What is the capital of France?
```

### 2. COUNTDOWN (Required) 
The 3-2-1 countdown overlay that builds suspense.

**Format:**
```
[start_time-end_time] COUNTDOWN: 3-2-1
```

**Example:**
```
[5.0-8.0] COUNTDOWN: 3-2-1
```

### 3. ANSWER (Required)
The answer reveal with optional emoji and excitement.

**Format:**
```
[start_time-end_time] ANSWER: 🎉 Your answer with emoji!
```

**Example:**
```
[8.0-12.0] ANSWER: 🇫🇷 Paris! The City of Light!
```

### 4. CTA (Required)
Call-to-action to encourage engagement.

**Format:**
```
[start_time-end_time] CTA: Follow for more content!
```

**Example:**
```
[12.0-15.0] CTA: Follow for more geography quizzes!
```

## Complete Examples

### Example 1: Geography Quiz
```
[0.0-5.0] QUESTION: What is the capital of France?
[5.0-8.0] COUNTDOWN: 3-2-1
[8.0-12.0] ANSWER: 🇫🇷 Paris! The City of Light!
[12.0-15.0] CTA: Follow for more geography quizzes!
```

### Example 2: Science Quiz
```
[0.0-4.0] QUESTION: How many bones are in the human body?
[4.0-7.0] COUNTDOWN: 3-2-1
[7.0-11.0] ANSWER: 💀 206 bones! Amazing, right?
[11.0-14.0] CTA: Like if you learned something new!
```

### Example 3: History Quiz
```
[0.0-6.0] QUESTION: Who painted the Mona Lisa?
[6.0-9.0] COUNTDOWN: 3-2-1
[9.0-13.0] ANSWER: 🎨 Leonardo da Vinci! Master artist!
[13.0-16.0] CTA: Follow for more art history!
```

### Example 4: Pop Culture Quiz
```
[0.0-5.0] QUESTION: Which movie won the 2023 Oscar for Best Picture?
[5.0-8.0] COUNTDOWN: 3-2-1
[8.0-12.0] ANSWER: 🏆 Everything Everywhere All at Once!
[12.0-15.0] CTA: Comment your favorite movie!
```

### Example 5: Math Quiz
```
[0.0-4.0] QUESTION: What is 15% of 200?
[4.0-7.0] COUNTDOWN: 3-2-1
[7.0-10.0] ANSWER: 🧮 30! Quick math!
[10.0-13.0] CTA: Follow for daily math tips!
```

## Timing Guidelines

### Recommended Timing Structure:
- **Question Duration**: 4-6 seconds (enough to read and process)
- **Countdown Duration**: 3 seconds (1 second per number)
- **Answer Duration**: 3-5 seconds (time to reveal and celebrate)
- **CTA Duration**: 3-4 seconds (clear call-to-action)
- **Total Video Length**: 13-18 seconds (optimal for TikTok)

### Timing Best Practices:
1. **Question phase** should give viewers enough time to think
2. **Countdown phase** builds suspense - exactly 3 seconds works best
3. **Answer phase** should feel rewarding and celebratory
4. **CTA phase** should be clear and actionable

## Content Guidelines

### Question Tips:
- Keep questions simple and engaging
- Use topics that are relatable to your audience
- Make questions neither too easy nor too hard
- End with a question mark

### Answer Tips:
- Start with an emoji relevant to the topic
- Include exclamation points for excitement
- Add extra context when helpful
- Keep it concise but engaging

### CTA Tips:
- Use action words: "Follow", "Like", "Comment", "Share"
- Be specific: "Follow for more [topic] quizzes!"
- Create urgency or curiosity
- Match your content theme

## Technical Requirements

### Time Format:
- Use decimal seconds: `0.0`, `5.5`, `12.75`
- Start time must be less than end time
- No overlapping time ranges recommended
- Sequential timing works best

### Component Names:
- Must be UPPERCASE: `QUESTION`, `COUNTDOWN`, `ANSWER`, `CTA`
- Exact spelling required
- Case-sensitive

### Text Content:
- Support for emojis ✅
- Support for special characters
- Keep within reasonable length limits
- Avoid line breaks within components

## Common Mistakes to Avoid

1. **Wrong component names**: Using `question` instead of `QUESTION`
2. **Invalid timestamps**: Using `[5-8]` instead of `[5.0-8.0]`
3. **Missing components**: Skipping COUNTDOWN or CTA
4. **Overlapping times**: Having components with conflicting timeframes
5. **Too long content**: Text that won't fit on screen properly

## Usage Example

```python
from shortGPT.engine.quiz_video_engine import QuizVideoEngine
from shortGPT.audio.edge_voice_module import EdgeTTSVoiceModule

# Create voice module
voice_module = EdgeTTSVoiceModule("en-US-AriaNeural")

# Define quiz script
quiz_script = """[0.0-5.0] QUESTION: What is the capital of France?
[5.0-8.0] COUNTDOWN: 3-2-1
[8.0-12.0] ANSWER: 🇫🇷 Paris! The City of Light!
[12.0-15.0] CTA: Follow for more geography quizzes!"""

# Create quiz engine
quiz_engine = QuizVideoEngine(
    voiceModule=voice_module,
    quiz_script=quiz_script,
    watermark="YourChannel"
)

# Generate the video
for step, message in quiz_engine.makeContent():
    print(f"Step {step}: {message}")

# Get the output video path
video_path = quiz_engine.get_video_output_path()
print(f"Quiz video saved to: {video_path}")
```

This structure ensures optimal TikTok performance with engaging question-answer format, suspenseful countdown, and clear call-to-action!