import logging
from typing import Optional, Dict
from core.model import QwenVLModel

logger = logging.getLogger(__name__)


class MLService:
    def __init__(self, model: QwenVLModel):
        self.model = model
        # self.redis = redis_manager

    async def predict(
        self,
        text: str,
        image_base64: Optional[str] = None,
    ) -> Dict:
        try:
            response = await self.model.predict(text)

            return {"success": True, "output_data": response}
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return {"success": False, "output_data": f"Prediction failed: {e}"}
