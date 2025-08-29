import os
import time
import traceback

import gradio as gr

from gui.asset_components import AssetComponentsUtils
from gui.ui_abstract_component import AbstractComponentUI
from gui.ui_components_html import GradioComponentsHTML
from shortGPT.audio.edge_voice_module import EdgeTTSVoiceModule
from shortGPT.audio.eleven_voice_module import ElevenLabsVoiceModule
from shortGPT.config.api_db import ApiKeyManager
from shortGPT.config.languages import (EDGE_TTS_VOICENAME_MAPPING,
                                       ELEVEN_SUPPORTED_LANGUAGES,
                                       LANGUAGE_ACRONYM_MAPPING,
                                       Language)
from shortGPT.engine.quiz_video_engine import QuizVideoEngine
from shortGPT.gpt.quiz_script_generator import QuizScriptGenerator


class QuizAutomationUI(AbstractComponentUI):
    def __init__(self, shortGptUI: gr.Blocks):
        self.shortGptUI = shortGptUI
        self.embedHTML = '<div style="display: flex; overflow-x: auto; gap: 20px;">'
        self.progress_counter = 0
        self.quiz_automation = None

    def create_ui(self):
        with gr.Row(visible=False) as quiz_automation:
            with gr.Column():
                # Quiz topic input
                quiz_topic = gr.Textbox(
                    label="Quiz Topic", 
                    placeholder="e.g., Harry Potter, Geography, Science, History...",
                    value="Harry Potter",
                    interactive=True
                )
                
                # Difficulty dropdown
                difficulty = gr.Dropdown(
                    choices=["easy", "medium", "hard"],
                    label="Difficulty Level",
                    value="medium",
                    interactive=True
                )
                
                # Target duration
                target_duration = gr.Number(
                    label="Target Duration (seconds)",
                    minimum=15,
                    maximum=120,
                    value=30,
                    step=5,
                    interactive=True
                )
                
                # Background video selection (only from asset_library)
                background_video = gr.Dropdown(
                    choices=AssetComponentsUtils.getBackgroundVideoChoices(),
                    label="Background Video (from Asset Library)",
                    value=None,
                    interactive=True
                )
                
                # Refresh button for background videos
                refresh_videos_btn = gr.Button("🔄 Refresh Video List", size="sm")
                refresh_videos_btn.click(
                    lambda: gr.update(choices=AssetComponentsUtils.getBackgroundVideoChoices()),
                    outputs=[background_video]
                )
                
                # TTS Engine selection
                tts_engine = gr.Radio(
                    [AssetComponentsUtils.ELEVEN_TTS, AssetComponentsUtils.EDGE_TTS], 
                    label="Text to speech engine", 
                    value=AssetComponentsUtils.EDGE_TTS, 
                    interactive=True
                )
                self.tts_engine = tts_engine.value
                
                # TTS Configuration
                with gr.Column(visible=False) as eleven_tts:
                    language_eleven = gr.Radio(
                        [lang.value for lang in ELEVEN_SUPPORTED_LANGUAGES], 
                        label="Language", 
                        value="English", 
                        interactive=True
                    )
                    voice_eleven = AssetComponentsUtils.voiceChoice(provider=AssetComponentsUtils.ELEVEN_TTS)
                    
                with gr.Column(visible=True) as edge_tts:
                    language_edge = gr.Dropdown(
                        [lang.value.upper() for lang in Language], 
                        label="Language", 
                        value="ENGLISH", 
                        interactive=True
                    )
                    
                def tts_engine_change(x):
                    self.tts_engine = x
                    return gr.update(visible=x == AssetComponentsUtils.ELEVEN_TTS), gr.update(visible=x == AssetComponentsUtils.EDGE_TTS)
                
                tts_engine.change(tts_engine_change, tts_engine, [eleven_tts, edge_tts])

                # Advanced options
                with gr.Accordion("Advanced Options", open=False):
                    num_questions = gr.Number(
                        label="Number of Questions",
                        minimum=1,
                        maximum=10,
                        value=3,
                        step=1,
                        interactive=True
                    )
                    
                    quiz_style = gr.Dropdown(
                        choices=["engaging", "challenging", "educational", "fun"],
                        label="Quiz Style",
                        value="engaging",
                        interactive=True
                    )
                    
                    use_sound_effects = gr.Checkbox(
                        label="Use Sound Effects (default like test.py)",
                        value=True,
                        interactive=True
                    )
                    
                    watermark = gr.Textbox(
                        label="Watermark (optional)",
                        placeholder="@your_channel",
                        interactive=True
                    )
                    
                    intro_text = gr.Textbox(
                        label="Intro Text (optional)",
                        placeholder="🧙‍♂️ ULTIMATE QUIZ CHALLENGE! 🧙‍♂️",
                        interactive=True
                    )
                    
                    intro_duration = gr.Number(
                        label="Intro Duration (seconds)",
                        minimum=0,
                        maximum=5,
                        value=2.0,
                        step=0.1,
                        interactive=True
                    )

                # Step 1: Generate scripts
                generateScriptsBtn = gr.Button("📝 Generate Scripts (easy / medium / hard)", variant="primary")

                # Scripts preview and approval
                with gr.Accordion("Preview & approve scripts", open=False) as scripts_preview:
                    with gr.Row():
                        easy_script = gr.Textbox(label="Easy script", lines=10)
                        medium_script = gr.Textbox(label="Medium script", lines=10)
                        hard_script = gr.Textbox(label="Hard script", lines=10)
                    with gr.Row():
                        approve_easy = gr.Checkbox(label="Approve easy", value=True)
                        approve_medium = gr.Checkbox(label="Approve medium", value=True)
                        approve_hard = gr.Checkbox(label="Approve hard", value=True)

                # Step 2: Proceed to render approved videos
                proceedBtn = gr.Button("🎬 Generate Videos for Approved Scripts", variant="secondary")
                
                # Progress and output
                quiz_progress = gr.HTML()
                quiz_output = gr.HTML()
                quiz_file_output = gr.Files(label="Generated Videos", visible=False)

        def _setup_voice(tts_choice, lang_eleven, voice_eleven, lang_edge):
            if tts_choice == AssetComponentsUtils.ELEVEN_TTS:
                api_key = ApiKeyManager.get_api_key("ELEVENLABS_API_KEY")
                if not api_key:
                    raise ValueError("ElevenLabs API key not configured")
                voice_module = ElevenLabsVoiceModule(api_key=api_key, voiceName=voice_eleven)
                language = Language.ENGLISH if lang_eleven == "English" else Language.SPANISH
            else:
                language_map = {lang.value.upper(): lang for lang in Language}
                language = language_map.get(lang_edge, Language.ENGLISH)
                voice_name = EDGE_TTS_VOICENAME_MAPPING[language]['male']
                voice_module = EdgeTTSVoiceModule(voice_name)
            return voice_module, language

        def generate_scripts(topic, duration, tts_choice, lang_eleven, voice_eleven, lang_edge, num_q, style):
            try:
                self.progress_counter = 0
                
                # Validate inputs
                if not topic.strip():
                    return "❌ Please enter a quiz topic", "", None, None, None, None
                    
                # Setup voice module (validate TTS config early)
                voice_module, language = _setup_voice(tts_choice, lang_eleven, voice_eleven, lang_edge)

                # Generate 3 scripts in a single prompt to avoid duplicates
                scripts = QuizScriptGenerator.generate_multi_difficulty_scripts(
                    topic=topic,
                    num_questions=int(num_q),
                    style=style,
                    target_duration=float(duration),
                    language=language
                )

                # Populate preview boxes and open the accordion
                return (
                    "<h3 style='color: #1f77b4;'>✅ Scripts generated. Review and approve, then click 'Generate Videos'.</h3>",
                    "",
                    gr.update(visible=True, open=True),
                    scripts.get('easy', ''),
                    scripts.get('medium', ''),
                    scripts.get('hard', ''),
                )
            except Exception as e:
                return (
                    f"<h3 style='color: #e74c3c;'>❌ Error generating scripts: {str(e)}</h3>",
                    "",
                    gr.update(),
                    None,
                    None,
                    None,
                )

        def generate_quiz_videos(topic, diff, duration, bg_video, tts_choice, lang_eleven, voice_eleven, 
                               lang_edge, num_q, style, sound_fx, wm, intro_txt, intro_dur,
                               easy_s, med_s, hard_s, appr_e, appr_m, appr_h):
            try:
                self.progress_counter = 0
                
                # Validate inputs
                if not topic.strip():
                    return "❌ Please enter a quiz topic", "", None
                if not bg_video:
                    return "❌ Please select a background video from the asset library", "", None
                
                voice_module, language = _setup_voice(tts_choice, lang_eleven, voice_eleven, lang_edge)

                scripts_to_render = []
                if appr_e and (easy_s and easy_s.strip()):
                    scripts_to_render.append(("easy", easy_s.strip()))
                if appr_m and (med_s and med_s.strip()):
                    scripts_to_render.append(("medium", med_s.strip()))
                if appr_h and (hard_s and hard_s.strip()):
                    scripts_to_render.append(("hard", hard_s.strip()))

                if not scripts_to_render:
                    return "❌ No scripts approved. Approve at least one.", "", None

                def update_progress():
                    self.progress_counter += 1
                    progress_messages = [
                        "🎭 Preparing script...", 
                        "🎤 Synthesizing voice narration...",
                        "🎬 Processing background video...",
                        "🎵 Adding sound effects...",
                        "✨ Finalizing video..."
                    ]
                    if self.progress_counter < len(progress_messages):
                        return f"<h3 style='color: #1f77b4;'>{progress_messages[self.progress_counter]}</h3>"
                    return "<h3 style='color: #2ecc71;'>🎉 Quiz video generated successfully!</h3>"

                html_blocks = []
                file_paths = []

                for level, script in scripts_to_render:
                    # Prepare per-level intro if not provided
                    intro = intro_txt if (intro_txt and intro_txt.strip()) else QuizVideoEngine._generate_intro_text(topic, style, level)
                    intro_d = float(intro_dur) if (intro_txt and intro_txt.strip()) else 2.0

                    quiz_engine = QuizVideoEngine(
                        voiceModule=voice_module,
                        quiz_script=script,
                        video_source="asset_library",
                        background_video_asset=bg_video,
                        use_sound_effects=sound_fx,
                        answer_sound_asset="answer_sound" if sound_fx else None,
                        watermark=wm if (wm and wm.strip()) else None,
                        intro_text=intro,
                        intro_duration=intro_d,
                        language=language
                    )

                    for step_num, step_logs in quiz_engine.makeContent():
                        yield update_progress(), "", None
                        time.sleep(0.3)

                    video_path = quiz_engine.get_video_output_path()
                    if video_path and os.path.exists(video_path):
                        file_name = os.path.basename(video_path)
                        html_video = GradioComponentsHTML.get_html_video_template(video_path, f"{level.upper()} - {file_name}")
                        html_blocks.append(html_video)
                        file_paths.append(video_path)
                    else:
                        html_blocks.append(f"<div style='color:#e74c3c;'>❌ {level.upper()}: Video file not found</div>")

                yield (
                    "<h3 style='color: #2ecc71;'>✅ Rendering complete</h3>",
                    "<br/>".join(html_blocks),
                    gr.update(value=file_paths, visible=True)
                )
                    
            except Exception as e:
                error_message = str(e)
                stack_trace = traceback.format_exc()
                error_html = GradioComponentsHTML.get_html_error_template().format(
                    error_message=error_message,
                    stack_trace=stack_trace
                )
                yield (
                    "<h3 style='color: #e74c3c;'>❌ Error generating quiz video</h3>",
                    error_html,
                    None
                )

        generateScriptsBtn.click(
            generate_scripts,
            inputs=[
                quiz_topic, target_duration, tts_engine,
                language_eleven, voice_eleven, language_edge, num_questions, quiz_style,
            ],
            outputs=[quiz_progress, quiz_output, scripts_preview, easy_script, medium_script, hard_script]  
        )

        proceedBtn.click(
            generate_quiz_videos,
            inputs=[
                quiz_topic, difficulty, target_duration, background_video, tts_engine,
                language_eleven, voice_eleven, language_edge, num_questions, quiz_style,
                use_sound_effects, watermark, intro_text, intro_duration,
                easy_script, medium_script, hard_script, approve_easy, approve_medium, approve_hard,
            ],
            outputs=[quiz_progress, quiz_output, quiz_file_output]
        )

        self.quiz_automation = quiz_automation
        return self.quiz_automation