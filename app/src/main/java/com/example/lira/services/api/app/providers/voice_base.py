from abc import ABC, abstractmethod
from typing import Dict, Any

class VoiceProvider(ABC):
    @abstractmethod
    async def initiate_verification_call(
        self,
        call_id: str,
        supplier: Dict[str, Any],
        case: Dict[str, Any],
        contact_source: str
    ) -> Dict[str, Any]:
        """Initiates call workflow and returns initial provider reference"""
        pass

    @abstractmethod
    async def get_call_status(self, provider_call_id: str) -> Dict[str, Any]:
        """Polls or inspects current provider status"""
        pass
