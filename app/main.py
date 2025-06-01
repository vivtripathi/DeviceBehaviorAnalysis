from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Optional
from datetime import datetime
import os
from dotenv import load_dotenv

from app.core.device_fingerprint import DeviceFingerprint
from app.core.behavior_analysis import UserBehavior, BehaviorAnalyzer
from app.db.mongodb import MongoDB

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Device Behavior Analytics",
    description="API for device fingerprinting and behavior analysis",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
mongo_client = MongoDB(os.getenv("MONGODB_URI", "mongodb://localhost:27017"))
behavior_analyzer = BehaviorAnalyzer()

@app.post("/api/device/profile")
async def create_device_profile(request: Request) -> Dict:
    """Create or update device profile based on fingerprint."""
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "")
    
    fingerprint = DeviceFingerprint(
        ip_address=client_ip,
        user_agent=user_agent,
        session_id=request.headers.get("x-session-id")
    )
    
    # Store fingerprint and get profile ID
    profile_id = await mongo_client.store_device_profile(fingerprint)
    
    # Find similar profiles
    similar_profiles = await mongo_client.get_similar_profiles(fingerprint)
    
    return {
        "profile_id": profile_id,
        "similar_profiles_count": len(similar_profiles),
        "device_info": fingerprint.parse_user_agent()
    }

@app.post("/api/behavior/analyze")
async def analyze_behavior(behavior: UserBehavior) -> Dict:
    """Analyze user behavior and return risk assessment."""
    # Store behavior data
    behavior_id = await mongo_client.store_behavior(behavior)
    
    # Get historical behaviors for this session
    historical_behaviors = await mongo_client.get_device_behaviors(behavior.session_id)
    
    # Train model if we have enough data
    if len(historical_behaviors) >= 5:
        behavior_analyzer.train([UserBehavior(**b) for b in historical_behaviors])
    
    # Analyze current behavior
    analysis_result = behavior_analyzer.analyze(behavior)
    
    return {
        "behavior_id": behavior_id,
        "risk_score": analysis_result["risk_score"],
        "features": analysis_result["features"],
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/device/{profile_id}")
async def get_device_profile(profile_id: str) -> Dict:
    """Retrieve device profile and its behavior history."""
    profile = await mongo_client.get_device_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return profile