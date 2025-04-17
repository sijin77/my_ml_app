import asyncio
import base64
from io import BytesIO
import logging
from typing import Dict, List, Optional
import torch
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info
from PIL import Image

logger = logging.getLogger(__name__)


logger = logging.getLogger(__name__)


class QwenVLModel:
    def __init__(self, model_name: str = "Qwen/Qwen2-VL-2B-Instruct"):
        try:
            self.model = Qwen2VLForConditionalGeneration.from_pretrained(
                model_name,
                torch_dtype="auto",
                device_map="auto",
            )
            self.processor = AutoProcessor.from_pretrained(model_name)
        except Exception as e:
            logger.error(f"Initialization error: {e}")
            raise

    async def predict(self, text: str, image_base64: Optional[str] = None):
        """Основной метод для предсказаний"""
        try:

            # Обрабатываем через процессор
            inputs = self.processor(text=text, padding=True, return_tensors="pt")
            # inputs = inputs.to("cuda")

            # Генерируем ответ
            generated_ids = self.model.generate(**inputs, max_new_tokens=128)

            # Декодируем ответ
            response = self.processor.batch_decode(
                generated_ids, skip_special_tokens=True
            )[0]

            return response

        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return f"Error: {str(e)}"
