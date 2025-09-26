#!/usr/bin/env python3
"""
NovinIntelligence AI Bridge for iOS SDK

This script provides a bridge between the iOS SDK and the Python AI system.
It can be embedded in the iOS framework and called to process security assessments.
"""

import sys
import json
import os
from typing import Dict, Any, Optional

# Configure sys.path to include bundled libraries
_current_dir = os.path.dirname(__file__)
_parent_dir = os.path.dirname(_current_dir)
_lib_dir = os.path.join(_parent_dir, "python", "lib")
_site_packages = os.path.join(_lib_dir, "python3.13", "site-packages")

for path in (_current_dir, _lib_dir, _site_packages):
    if path not in sys.path:
        sys.path.insert(0, path)

try:
    from novin_intelligence.security import get_embedded_system_instance, SecurityConfig
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    print("Warning: novin_intelligence module not available, using fallback logic", file=sys.stderr)

class NovinAIBridge:
    def __init__(self, brand_config: Optional[Dict[str, Any]] = None):
        self.brand_config = brand_config or {}
        self.system = None

        if AI_AVAILABLE:
            try:
                self.system = get_embedded_system_instance(brand_config)
                print("✅ NovinAI bridge initialized with full AI system")
            except Exception as e:
                print(f"❌ Failed to initialize AI system: {e}", file=sys.stderr)
                AI_AVAILABLE = False

        if not AI_AVAILABLE:
            print("⚠️ Using fallback AI logic", file=sys.stderr)

    def process_request(self, request_json: str, client_id: str = "ios-client") -> str:
        """Process a security assessment request and return JSON result."""

        try:
            # Parse input
            request_data = json.loads(request_json)

            if AI_AVAILABLE and self.system:
                # Use the full Python AI system
                result = self.system.process_request(request_data, client_id)
                return json.dumps(result)
            else:
                # Use fallback logic
                return self._fallback_processing(request_data, client_id)

        except Exception as e:
            error_result = {
                "error": True,
                "errorType": "processing_failed",
                "message": f"AI processing failed: {str(e)}",
                "fallbackAssessment": {
                    "threatLevel": "standard",
                    "confidence": 0.0,
                    "reason": "ai_unavailable"
                }
            }
            return json.dumps(error_result)

    def _fallback_processing(self, request_data: Dict[str, Any], client_id: str) -> str:
        """Fallback processing when full AI system is unavailable."""

        # Simple rule-based assessment as fallback
        threat_score = 0.0
        factors = []

        # Process events
        for event in request_data.get('events', []):
            event_type = event.get('type', '')
            confidence = event.get('confidence', 0.0)

            if event_type == 'motion':
                threat_score += confidence * 0.4
                factors.append('motion_detected')
            elif event_type == 'face':
                threat_score += confidence * 0.8
                factors.append('face_recognition')
            elif event_type == 'door':
                threat_score += confidence * 0.7
                factors.append('door_sensor')
            elif event_type == 'sound':
                threat_score += confidence * 0.3
                factors.append('audio_detection')
            else:
                threat_score += confidence * 0.2
                factors.append('unknown_event')

        # Apply system mode
        system_mode = request_data.get('systemMode', 'home')
        if system_mode == 'away':
            threat_score *= 1.5
            factors.append('away_mode_multiplier')

        # Determine threat level
        if threat_score > 0.8:
            threat_level = 'critical'
        elif threat_score > 0.6:
            threat_level = 'elevated'
        elif threat_score > 0.3:
            threat_level = 'standard'
        else:
            threat_level = 'ignore'

        # Build response
        response = {
            "requestId": f"fallback-{hash(json.dumps(request_data, sort_keys=True)) % 1000000}",
            "clientId": client_id,
            "timestamp": "2025-01-01T00:00:00Z",  # Would use actual timestamp
            "threatAssessment": {
                "level": threat_level,
                "confidence": min(threat_score, 1.0),
                "probabilityDistribution": {
                    "ignore": max(0, 1.0 - threat_score),
                    "standard": min(threat_score, 0.4),
                    "elevated": min(max(threat_score - 0.4, 0), 0.4),
                    "critical": max(threat_score - 0.8, 0)
                }
            },
            "reasoning": {
                "primaryFactors": factors,
                "ruleApplied": None,
                "layerAnalysis": {}
            },
            "context": {
                "systemMode": system_mode,
                "location": request_data.get('location'),
                "crimeContext": {
                    "relevantCrimes": 0,
                    "crimeIndex": 0.0,
                    "escalationRequired": False
                },
                "deviceStatus": request_data.get('deviceInfo', {})
            },
            "processingTimeMs": 15.0,  # Simulated processing time
            "systemStatus": {
                "healthy": True,
                "fallbackActive": True
            }
        }

        return json.dumps(response)

def main():
    """Command-line interface for testing the bridge."""
    if len(sys.argv) < 2:
        print("Usage: novin_ai_bridge.py <command> [args...]", file=sys.stderr)
        print("Commands:", file=sys.stderr)
        print("  init <brand_config_json> - Initialize with brand config", file=sys.stderr)
        print("  process <request_json> - Process a security request", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]

    if command == "init":
        brand_config_json = sys.argv[2] if len(sys.argv) > 2 else "{}"
        try:
            brand_config = json.loads(brand_config_json)
            bridge = NovinAIBridge(brand_config)
            print("Bridge initialized successfully")
        except Exception as e:
            print(f"Failed to initialize bridge: {e}", file=sys.stderr)
            sys.exit(1)

    elif command == "process":
        if len(sys.argv) < 3:
            print("Error: process command requires request JSON", file=sys.stderr)
            sys.exit(1)

        request_json = sys.argv[2]
        bridge = NovinAIBridge()  # Use default config

        try:
            result = bridge.process_request(request_json)
            print(result)
        except Exception as e:
            print(f"Processing failed: {e}", file=sys.stderr)
            sys.exit(1)

    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
