from typing import Dict, Optional
from user_agents import parse
from pydantic import BaseModel
from datetime import datetime

class DeviceFingerprint(BaseModel):
    user_agent: str
    ip_address: str
    screen_resolution: Optional[str] = None
    color_depth: Optional[int] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    platform: Optional[str] = None
    plugins: Optional[list] = None
    timestamp: datetime = datetime.utcnow()
    session_id: Optional[str] = None

    def parse_user_agent(self) -> Dict:
        """Parse user agent string to extract device information."""
        ua = parse(self.user_agent)
        return {
            "browser": {
                "family": ua.browser.family,
                "version": ua.browser.version_string
            },
            "os": {
                "family": ua.os.family,
                "version": ua.os.version_string
            },
            "device": {
                "family": ua.device.family,
                "brand": ua.device.brand,
                "model": ua.device.model
            },
            "is_mobile": ua.is_mobile,
            "is_tablet": ua.is_tablet,
            "is_pc": ua.is_pc
        }

    def to_dict(self) -> Dict:
        """Convert fingerprint to dictionary format with parsed user agent info."""
        base_dict = self.model_dump()
        base_dict["parsed_user_agent"] = self.parse_user_agent()
        return base_dict