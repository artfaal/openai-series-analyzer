"""
AI Analyzer
Uses OpenAI API for series title recognition with web search
"""

import os
import json
from pathlib import Path
from typing import List, Dict
from openai import OpenAI
from dotenv import load_dotenv
from models.data_models import MediaFile
from config.prompts import AI_ANALYSIS_PROMPT

# Load environment variables
load_dotenv()


class AIAnalyzer:
    """Series analyzer via OpenAI API with web search"""

    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in .env file. Please add your API key.")

        self.client = OpenAI(api_key=self.api_key)
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o')  # Use gpt-4o or gpt-5 when available
        self.reasoning_effort = os.getenv('OPENAI_REASONING_EFFORT', 'medium')
        self.prompt_template = AI_ANALYSIS_PROMPT

    def analyze(
        self,
        files: List[MediaFile],
        dir_info: Dict,
        directory_name: str
    ) -> Dict:
        """
        Analyzes files using OpenAI API with web search

        Args:
            files: List of MediaFile objects
            dir_info: Information extracted from directory name
            directory_name: Directory name

        Returns:
            Dict with keys: title, year, season, total_episodes, needs_confirmation

        Raises:
            Exception: If OpenAI API request fails
        """
        print("\n🤖 Анализ через OpenAI API с веб-поиском...")

        # Group files for better presentation
        video_files = [f for f in files if f.file_type == 'video']
        subtitle_tracks = set(f.subtitle_track for f in files
                             if f.file_type == 'subtitle' and f.subtitle_track)

        file_summary = f"""
Директория: {directory_name}

Видео файлы ({len(video_files)} шт):
{chr(10).join([f"- {f.filename}" for f in video_files[:5]])}
{"..." if len(video_files) > 5 else ""}

Субтитры (треки): {', '.join(subtitle_tracks) if subtitle_tracks else 'не найдены'}

Информация из названия директории:
- Возможное название: {dir_info.get('title', 'не определено')}
- Сезон: {dir_info.get('season', 'не определён')}
- Релиз-группа: {dir_info.get('release_group', 'не определена')}
"""

        prompt = self.prompt_template.format(file_summary=file_summary)

        try:
            # Build request parameters
            request_params = {
                "model": self.model,
                "tools": [{"type": "web_search"}],
                "tool_choice": "auto",
                "input": prompt
            }

            # Add reasoning effort only if model supports it (o1, o3, gpt-5 models)
            if self.reasoning_effort and self.model in ['gpt-5', 'o1', 'o3', 'o1-preview', 'o3-mini']:
                request_params["reasoning"] = {"effort": self.reasoning_effort}

            response = self.client.responses.create(**request_params)

            # Extract JSON from output_text
            output_text = response.output_text.strip()

            # Remove markdown blocks if present
            if output_text.startswith('```'):
                output_text = output_text.split('```')[1]
                if output_text.startswith('json'):
                    output_text = output_text[4:]
                output_text = output_text.strip()

            # Extract only JSON part (sometimes AI adds explanations after JSON)
            # Find first { and last }
            first_brace = output_text.find('{')
            last_brace = output_text.rfind('}')

            if first_brace != -1 and last_brace != -1:
                json_text = output_text[first_brace:last_brace + 1]
            else:
                json_text = output_text

            result = json.loads(json_text)

            # Log if web search was used
            if hasattr(response, 'output') and response.output:
                for item in response.output:
                    if hasattr(item, 'type') and item.type == 'web_search_call':
                        print("   🌐 Использован веб-поиск")
                        break

            print("✅ Анализ завершён")
            return result

        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse JSON response from OpenAI API: {e}\nResponse: {output_text[:200]}"
            print(f"❌ {error_msg}")
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"OpenAI API request failed: {e}"
            print(f"❌ {error_msg}")
            raise Exception(error_msg)
