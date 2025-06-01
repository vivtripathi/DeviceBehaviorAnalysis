from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel
from sklearn.ensemble import IsolationForest
import numpy as np

class UserBehavior(BaseModel):
    session_id: str
    mouse_movements: List[Dict[str, float]] = []
    keyboard_patterns: List[Dict[str, float]] = []
    navigation_patterns: List[Dict[str, str]] = []
    timestamp: datetime = datetime.utcnow()

class BehaviorAnalyzer:
    def __init__(self):
        self.model = IsolationForest(contamination=0.1, random_state=42)
        self.feature_names = [
            'avg_mouse_speed',
            'typing_speed',
            'session_duration',
            'navigation_count'
        ]
    
    def extract_features(self, behavior: UserBehavior) -> np.ndarray:
        """Extract numerical features from behavior data."""
        features = {
            'avg_mouse_speed': self._calculate_avg_mouse_speed(behavior.mouse_movements),
            'typing_speed': self._calculate_typing_speed(behavior.keyboard_patterns),
            'session_duration': self._calculate_session_duration(behavior.timestamp),
            'navigation_count': len(behavior.navigation_patterns)
        }
        return np.array([features[name] for name in self.feature_names])
    
    def _calculate_avg_mouse_speed(self, movements: List[Dict[str, float]]) -> float:
        if not movements:
            return 0.0
        speeds = [m.get('speed', 0.0) for m in movements]
        return sum(speeds) / len(speeds)
    
    def _calculate_typing_speed(self, patterns: List[Dict[str, float]]) -> float:
        if not patterns:
            return 0.0
        speeds = [p.get('speed', 0.0) for p in patterns]
        return sum(speeds) / len(speeds)
    
    def _calculate_session_duration(self, timestamp: datetime) -> float:
        return (datetime.utcnow() - timestamp).total_seconds()
    
    def train(self, behaviors: List[UserBehavior]):
        """Train the anomaly detection model."""
        X = np.array([self.extract_features(b) for b in behaviors])
        self.model.fit(X)
    
    def analyze(self, behavior: UserBehavior) -> Dict[str, float]:
        """Analyze behavior and return risk score."""
        features = self.extract_features(behavior).reshape(1, -1)
        anomaly_score = self.model.score_samples(features)[0]
        
        # Convert anomaly score to risk score (0-1 range, higher means more risky)
        risk_score = 1 - (anomaly_score - self.model.offset_) / abs(self.model.offset_)
        risk_score = max(0.0, min(1.0, risk_score))
        
        return {
            'risk_score': risk_score,
            'features': dict(zip(self.feature_names, features[0]))
        }