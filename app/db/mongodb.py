from motor.motor_asyncio import AsyncIOMotorClient
from typing import Dict, List, Optional
from datetime import datetime
from app.core.device_fingerprint import DeviceFingerprint
from app.core.behavior_analysis import UserBehavior

class MongoDB:
    def __init__(self, connection_string: str):
        self.client = AsyncIOMotorClient(connection_string)
        self.db = self.client.device_analytics
        self.device_profiles = self.db.device_profiles
        self.behaviors = self.db.behaviors
    
    async def store_device_profile(self, fingerprint: DeviceFingerprint) -> str:
        """Store device fingerprint and return profile ID."""
        profile_data = fingerprint.to_dict()
        profile_data['created_at'] = datetime.utcnow()
        profile_data['updated_at'] = datetime.utcnow()
        
        result = await self.device_profiles.insert_one(profile_data)
        return str(result.inserted_id)
    
    async def update_device_profile(self, profile_id: str, fingerprint: DeviceFingerprint):
        """Update existing device profile."""
        profile_data = fingerprint.to_dict()
        profile_data['updated_at'] = datetime.utcnow()
        
        await self.device_profiles.update_one(
            {'_id': profile_id},
            {'$set': profile_data}
        )
    
    async def store_behavior(self, behavior: UserBehavior) -> str:
        """Store user behavior data and return behavior ID."""
        behavior_data = behavior.model_dump()
        behavior_data['created_at'] = datetime.utcnow()
        
        result = await self.behaviors.insert_one(behavior_data)
        return str(result.inserted_id)
    
    async def get_device_behaviors(self, session_id: str) -> List[Dict]:
        """Retrieve behavior history for a device."""
        cursor = self.behaviors.find({'session_id': session_id})
        return await cursor.to_list(length=None)
    
    async def get_device_profile(self, profile_id: str) -> Optional[Dict]:
        """Retrieve device profile by ID."""
        return await self.device_profiles.find_one({'_id': profile_id})
    
    async def get_similar_profiles(self, fingerprint: DeviceFingerprint, limit: int = 5) -> List[Dict]:
        """Find similar device profiles based on fingerprint attributes."""
        parsed_ua = fingerprint.parse_user_agent()
        
        query = {
            '$or': [
                {'ip_address': fingerprint.ip_address},
                {'parsed_user_agent.browser.family': parsed_ua['browser']['family']},
                {'parsed_user_agent.os.family': parsed_ua['os']['family']},
                {'screen_resolution': fingerprint.screen_resolution}
            ]
        }
        
        cursor = self.device_profiles.find(query).limit(limit)
        return await cursor.to_list(length=limit)