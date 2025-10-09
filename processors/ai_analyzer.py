"""
AI Analyzer
Использует OpenAI API для распознавания названий сериалов
"""

import os
import json
from pathlib import Path
from typing import List, Dict
import openai
from dotenv import load_dotenv
from models.data_models import MediaFile
from config.prompts import AI_SYSTEM_PROMPT, AI_USER_PROMPT_TEMPLATE

# Загрузка переменных окружения
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
openai.api_key = OPENAI_API_KEY


class AIAnalyzer:
    """Анализатор сериалов через OpenAI API"""

    def __init__(self):
        self.api_key = OPENAI_API_KEY
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o')
        self.temperature = float(os.getenv('OPENAI_TEMPERATURE', '0.3'))
        self.system_prompt = AI_SYSTEM_PROMPT
        self.user_prompt_template = AI_USER_PROMPT_TEMPLATE

    def analyze(
        self,
        files: List[MediaFile],
        dir_info: Dict,
        directory_name: str
    ) -> Dict:
        """
        Анализирует файлы с помощью OpenAI API

        Args:
            files: Список MediaFile объектов
            dir_info: Информация из названия директории
            directory_name: Название директории

        Returns:
            Dict с ключами: title, year, season, total_episodes, needs_confirmation
        """
        # Проверяем наличие API ключа
        if not self.api_key:
            print("\n⚠️  OpenAI API ключ не найден в .env файле, используем локальное распознавание")
            return self._get_fallback_result(dir_info, files)

        print("\n🤖 Анализ через OpenAI API...")

        # Группируем файлы для лучшего представления
        video_files = [f for f in files if f.file_type == 'video']
        subtitle_tracks = set(f.subtitle_track for f in files
                             if f.file_type == 'subtitle' and f.subtitle_track)

        file_summary = f"""
Директория: {directory_name}

Видео файлы ({len(video_files)} шт):
{chr(10).join([f"- {f.filename}" for f in video_files[:3]])}
{"..." if len(video_files) > 3 else ""}

Субтитры (треки): {', '.join(subtitle_tracks) if subtitle_tracks else 'не найдены'}

Информация из названия директории:
- Возможное название: {dir_info.get('title', 'не определено')}
- Сезон: {dir_info.get('season', 'не определён')}
- Релиз-группа: {dir_info.get('release_group', 'не определена')}
"""

        prompt = self.user_prompt_template.format(file_summary=file_summary)

        try:
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature
            )

            content = response.choices[0].message.content.strip()

            # Убираем markdown блоки если есть
            if content.startswith('```'):
                content = content.split('```')[1]
                if content.startswith('json'):
                    content = content[4:]
                content = content.strip()

            result = json.loads(content)
            print("✅ Анализ завершён")
            return result

        except json.JSONDecodeError as e:
            print(f"❌ Ошибка парсинга JSON: {e}")
            print(f"   Ответ API: {content[:200]}...")
            return self._get_fallback_result(dir_info, files)
        except Exception as e:
            print(f"❌ Ошибка при анализе: {e}")
            return self._get_fallback_result(dir_info, files)

    def _get_fallback_result(self, dir_info: Dict, files: List[MediaFile]) -> Dict:
        """Возвращает результат на основе локального анализа"""
        return {
            'title': dir_info.get('title', 'Unknown'),
            'year': None,
            'season': dir_info.get('season', 1),
            'total_episodes': len([f for f in files if f.file_type == 'video']),
            'needs_confirmation': True
        }
