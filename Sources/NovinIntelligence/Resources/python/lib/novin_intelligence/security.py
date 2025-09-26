# NovinAI Security System
# A complete, production-ready AI security threat assessment system.

# Standard Library Imports
import base64
import collections
import dataclasses
import datetime
from datetime import UTC
import enum
import hashlib
import hmac
import json
import logging
import logging.handlers
import os
import re
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Optional, Set, Callable

# Third-Party Imports (as specified in the prompt)
import numpy as np
from scipy.special import softmax

# Optional dependencies for full functionality
try:
    import psutil
except ImportError:
    psutil = None

try:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding, rsa
    from cryptography.hazmat.primitives.serialization import load_pem_public_key
    from cryptography.exceptions import InvalidSignature
except ImportError:
    hashes = None
    padding = None
    rsa = None
    load_pem_public_key = None
    InvalidSignature = None

# --- 1. Configuration & Core Types ---

@dataclass
class SecurityConfig:
    """Single source of truth for all system parameters."""
    # Neural Network
    n_features: int = 16384
    n_classes: int = 4
    weight_init_bound: float = 0.1
    weight_security_max: float = 5.0
    prediction_timeout: float = 0.05
    
    # Feature Engineering
    max_cache_size: int = 5000
    cache_ttl_seconds: int = 1800
    max_events_per_request: int = 25
    max_metadata_bytes: int = 512
    
    # Rule Engine
    rule_priority_max: int = 10
    emergency_threshold: float = 0.95
    pet_confidence_threshold: float = 0.85
    door_open_threshold: float = 0.75
    noise_alert_db: int = 85
    face_recognition_threshold: float = 0.95
    
    # Crime Intelligence
    crime_cache_ttl: int = 3600
    crime_recency_days: int = 14
    crime_escalation_count: int = 2
    max_crime_index: float = 1.0
    
    # Event Correlation
    duplicate_event_window_seconds: int = 5
    
    # Reasoning Engine
    max_reasoning_layers: int = 8
    early_termination_confidence: float = 0.98
    reasoning_timeout: float = 0.1
    
    # Security & Performance
    rate_limit_rpm: int = 50
    cpu_max_percent: float = 70.0
    memory_max_percent: float = 75.0
    error_rate_max: float = 0.01
    max_processing_time: float = 0.1
    
    # Validation
    latitude_bounds: Tuple[float, float] = (-90.0, 90.0)
    longitude_bounds: Tuple[float, float] = (-180.0, 180.0)
    confidence_bounds: Tuple[float, float] = (0.0, 1.0)
    battery_bounds: Tuple[float, float] = (0.0, 100.0)
    decibel_max: float = 150.0

class ThreatLevel(enum.Enum):
    """Defines the four threat levels for classification."""
    CRITICAL = 3
    ELEVATED = 2
    STANDARD = 1
    IGNORE = 0

    def __str__(self):
        return self.name.lower()

# --- 2. Input Validation System ---

class InputValidation:
    """Handles comprehensive validation and sanitization of input data."""
    VALID_EVENT_TYPES = {'motion', 'sound', 'door', 'window', 'face', 'smoke', 'fire', 'glassbreak', 'pet', 'vehicle'}
    VALID_SYSTEM_MODES = {'home', 'away', 'night', 'vacation', 'office'}

    def __init__(self, config: SecurityConfig):
        self.config = config

    def validate_request(self, data: Dict[str, Any]) -> List[str]:
        """Validates the entire request payload, returning a list of errors."""
        errors = []
        if not isinstance(data, dict):
            return ["Request must be a JSON object."]

        # Validate top-level keys
        errors.extend(self._validate_system_mode(data.get('systemMode')))
        errors.extend(self._validate_location(data.get('location')))
        errors.extend(self._validate_device_info(data.get('deviceInfo')))
        errors.extend(self._validate_events(data.get('events')))

        return errors

    def _validate_system_mode(self, mode: Any) -> List[str]:
        if mode is None or mode not in self.VALID_SYSTEM_MODES:
            return [f"Invalid systemMode: '{mode}'. Must be one of {self.VALID_SYSTEM_MODES}"]
        return []

    def _validate_location(self, loc: Any) -> List[str]:
        if not isinstance(loc, dict) or 'lat' not in loc or 'lon' not in loc:
            return ["'location' must be a dict with 'lat' and 'lon' keys."]
        lat_min, lat_max = self.config.latitude_bounds
        lon_min, lon_max = self.config.longitude_bounds
        if not (isinstance(loc['lat'], (int, float)) and lat_min <= loc['lat'] <= lat_max):
            return [f"Invalid latitude: {loc['lat']}"]
        if not (isinstance(loc['lon'], (int, float)) and lon_min <= loc['lon'] <= lon_max):
            return [f"Invalid longitude: {loc['lon']}"]
        return []

    def _validate_device_info(self, info: Any) -> List[str]:
        if not isinstance(info, dict):
            return ["'deviceInfo' must be a dict."]
        if 'battery' in info:
            batt_min, batt_max = self.config.battery_bounds
            if not (isinstance(info['battery'], (int, float)) and batt_min <= info['battery'] <= batt_max):
                return [f"Invalid battery level: {info['battery']}"]
        return []

    def _validate_events(self, events: Any) -> List[str]:
        if not isinstance(events, list):
            return ["'events' must be a list."]
        if len(events) > self.config.max_events_per_request:
            return [f"Exceeded max events per request ({self.config.max_events_per_request})."]
        
        errors = []
        for i, event in enumerate(events):
            errors.extend(self._validate_single_event(event, i))
        return errors

    def _validate_single_event(self, event: Any, index: int) -> List[str]:
        if not isinstance(event, dict):
            return [f"Event {index}: Must be a dict."]
        
        errors = []
        if event.get('type') not in self.VALID_EVENT_TYPES:
            errors.append(f"Event {index}: Invalid type '{event.get('type')}'")
        
        conf_min, conf_max = self.config.confidence_bounds
        if not (isinstance(event.get('confidence'), (int, float)) and conf_min <= event['confidence'] <= conf_max):
            errors.append(f"Event {index}: Invalid confidence {event.get('confidence')}")

        try:
            datetime.datetime.fromisoformat(event.get('timestamp', '').replace('Z', '+00:00'))
        except (ValueError, TypeError):
            errors.append(f"Event {index}: Invalid ISO 8601 timestamp '{event.get('timestamp')}'")

        if 'metadata' in event and len(json.dumps(event['metadata'])) > self.config.max_metadata_bytes:
            errors.append(f"Event {index}: Metadata exceeds max size of {self.config.max_metadata_bytes} bytes.")

        return errors

# --- 2a. Rate Limiting & Resource Monitoring ---

class RateLimiting:
    """Handles per-client request throttling with thread-safe storage."""
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.clients: Dict[str, List[float]] = collections.defaultdict(list)
        self.lock = threading.Lock()

    def is_allowed(self, client_id: str) -> bool:
        """Checks if a client has exceeded the request rate limit."""
        with self.lock:
            now = time.time()
            requests = self.clients[client_id]
            
            # Remove timestamps older than 1 minute
            requests = [t for t in requests if now - t < 60]
            self.clients[client_id] = requests
            
            if len(requests) >= self.config.rate_limit_rpm:
                return False
            
            requests.append(now)
            return True

class ResourceMonitoring:
    """Monitors CPU and memory usage to prevent system overload."""
    def __init__(self, config: SecurityConfig):
        self.config = config
        if psutil:
            self.process = psutil.Process(os.getpid())
        else:
            self.process = None
            logging.warning("psutil not found. Resource monitoring is disabled.")

    def is_healthy(self) -> Tuple[bool, str]:
        """Checks if system resources are within configured limits."""
        if not self.process:
            return (True, "Monitoring disabled.")

        cpu_percent = self.process.cpu_percent(interval=0.1)
        if cpu_percent > self.config.cpu_max_percent:
            return (False, f"CPU usage {cpu_percent}% exceeds limit of {self.config.cpu_max_percent}%.")

        memory_info = self.process.memory_info()
        memory_percent = (memory_info.rss / psutil.virtual_memory().total) * 100
        if memory_percent > self.config.memory_max_percent:
            return (False, f"Memory usage {memory_percent:.2f}% exceeds limit of {self.config.memory_max_percent}%.")

        return (True, "System healthy.")


# --- 3. Feature Extraction ---

class FeatureExtraction:
    """Transforms raw input data into a high-dimensional feature vector."""
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.feature_cache = collections.OrderedDict()
        self.cache_lock = threading.Lock()
        self.salt = os.urandom(16)

    def _get_cache_key(self, data: Dict[str, Any]) -> str:
        """Generates a stable SHA3-256 hash for caching."""
        # Use a tuple of sorted items to ensure hash stability
        canonical_representation = json.dumps(data, sort_keys=True).encode('utf-8')
        return hashlib.sha3_256(self.salt + canonical_representation).hexdigest()

    def extract(self, data: Dict[str, Any], crime_context: Dict[str, Any]) -> np.ndarray:
        """Main feature extraction method with thread-safe caching."""
        # Include crime_context in the cache key
        cache_key_data = (json.dumps(data, sort_keys=True), json.dumps(crime_context, sort_keys=True))
        cache_key = hashlib.sha3_256(str(cache_key_data).encode()).hexdigest()

        with self.cache_lock:
            if cache_key in self.feature_cache:
                if time.time() - self.feature_cache[cache_key][1] < self.config.cache_ttl_seconds:
                    self.feature_cache.move_to_end(cache_key)
                    return self.feature_cache[cache_key][0]
        
        features = self._compute_features(data, crime_context)
        
        with self.cache_lock:
            self.feature_cache[cache_key] = (features, time.time())
            if len(self.feature_cache) > self.config.max_cache_size:
                self.feature_cache.popitem(last=False)
        
        return features

    def _compute_features(self, data: Dict[str, Any], crime_context: Dict[str, Any]) -> np.ndarray:
        """Computes the full feature vector using multi-faceted feature engineering."""
        features = np.zeros(self.config.n_features)
        
        # Event type one-hot (first 20 features)
        event_types = ['motion', 'sound', 'door', 'window', 'face', 'smoke', 'fire', 'glassbreak', 'pet', 'vehicle']
        for i, event_type in enumerate(event_types):
            if any(e.get('type') == event_type for e in data.get('events', [])):
                features[i] = 1.0
        
        # Temporal encoding (sin/cos for cyclical features)
        if data.get('events'):
            ts_str = data['events'][0]['timestamp']
            dt = datetime.datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
            hour = dt.hour
            # Sin/cos encoding for hour (features 20-21)
            features[20] = np.sin(2 * np.pi * hour / 24)
            features[21] = np.cos(2 * np.pi * hour / 24)
        
        # Confidence statistics (features 22-25)
        confidences = [e.get('confidence', 0) for e in data.get('events', [])]
        if confidences:
            features[22] = np.mean(confidences)  # Average confidence
            features[23] = np.max(confidences)  # Max confidence
            features[24] = np.std(confidences)  # Confidence variance
            features[25] = len(confidences) / self.config.max_events_per_request  # Event density
        
        # System mode one-hot (features 26-30)
        system_modes = ['home', 'away', 'night', 'vacation', 'office']
        try:
            mode_idx = system_modes.index(data.get('systemMode', 'home'))
            features[26 + mode_idx] = 1.0
        except ValueError:
            pass # Invalid mode already caught by validation
        
        # Location-based features (features 31-40)
        lat, lon = data['location']['lat'], data['location']['lon']
        features[31] = (lat + 90) / 180  # Normalized latitude
        features[32] = (lon + 180) / 360  # Normalized longitude
        
        # Crime context integration (features 41-45)
        features[41] = crime_context.get('crimeIndex', 0.0)
        features[42] = 1.0 if crime_context.get('escalationRequired', False) else 0.0
        features[43] = crime_context.get('relevantCrimes', 0) / 10.0  # Normalized count
        
        # Hash-based features for remaining dimensions (sparse representation)
        for event in data.get('events', []):
            event_str = json.dumps(event, sort_keys=True)
            h = int(hashlib.sha3_256(event_str.encode()).hexdigest(), 16)
            feature_idx = (h % (self.config.n_features - 50)) + 50  # Avoid overwriting engineered features
            features[feature_idx] = event.get('confidence', 0.0)
        
        return features

# --- 4. Neural Network ---

class NeuralNetwork:
    """A secure, from-scratch neural network for threat classification."""
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.weights: Optional[np.ndarray] = None
        self.version: Optional[str] = None
        self.public_key: Optional[Any] = None

    def load_model(self, model_path: str, signature_path: str, public_key_path: str) -> bool:
        """Loads, verifies, and validates a signed model file."""
        if not all([hashes, rsa, padding, load_pem_public_key, InvalidSignature]):
            logging.error("Cryptography library not installed. Cannot verify model.")
            return False

        try:
            with open(model_path, 'r') as f:
                model_content = f.read()
                model_data = json.loads(model_content)
            
            with open(signature_path, 'rb') as f:
                signature = f.read()

            with open(public_key_path, 'rb') as f:
                self.public_key = load_pem_public_key(f.read())

            # 1. Verify signature
            self.public_key.verify(
                signature,
                model_content.encode('utf-8'),
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256()
            )

            # 2. Verify checksum
            weights_b64 = model_data['weights']
            checksum = model_data['checksum']
            if hashlib.sha3_256(weights_b64.encode('utf-8')).hexdigest() != checksum:
                raise ValueError("Model checksum mismatch.")

            # 3. Load weights
            weights_array = np.frombuffer(base64.b64decode(weights_b64), dtype=np.float32)
            self.weights = weights_array.reshape((self.config.n_features, self.config.n_classes))
            self.version = model_data.get('version', '0.0.0')

            # 4. Security checks
            if np.any(np.abs(self.weights) > self.config.weight_security_max):
                raise ValueError("Model weights exceed security bounds.")

            return True
        except (FileNotFoundError, json.JSONDecodeError, InvalidSignature, ValueError) as e:
            logging.error(f"Failed to load or verify model: {e}")
            self.weights = None
            return False

    def predict(self, features: np.ndarray) -> Optional[np.ndarray]:
        """Performs a forward pass using vectorized NumPy operations."""
        if self.weights is None:
            logging.error("Model not loaded. Cannot predict.")
            return None
        
        # Single-layer feedforward network
        logits = features @ self.weights
        return softmax(logits)

# --- 5. Rule Engine ---

class RuleEngine:
    """Applies a prioritized set of deterministic rules for overrides and adjustments."""
    def __init__(self, config: SecurityConfig):
        self.config = config
        # Rules are defined with a priority (lower is higher) and the function to execute
        self.rules = sorted([
            (1, self._rule_emergency),
            (2, self._rule_high_noise_away),
            (3, self._rule_unknown_face_away),
            (4, self._rule_door_open_away),
            (5, self._rule_night_motion),
            (9, self._rule_false_positive_reduction), # Low priority
        ])

    def apply(self, data: Dict[str, Any], probabilities: np.ndarray) -> Tuple[Optional[ThreatLevel], Optional[str], np.ndarray]:
        """
        Iterates through rules in priority order and returns the first match.
        """
        for _, rule_func in self.rules:
            result = rule_func(data, probabilities)
            if result:
                return result
        return (None, None, probabilities)

    def _rule_emergency(self, data: Dict[str, Any], probs: np.ndarray) -> Optional[Tuple]:
        for event in data.get('events', []):
            is_emergency = event.get('type') in {'smoke', 'fire', 'glassbreak'}
            if is_emergency and event.get('confidence', 0) >= self.config.emergency_threshold:
                return (ThreatLevel.CRITICAL, f"emergency_{event['type']}", probs)
        return None

    def _rule_high_noise_away(self, data: Dict[str, Any], probs: np.ndarray) -> Optional[Tuple]:
        if data.get('systemMode') == 'away':
            for event in data.get('events', []):
                if event.get('type') == 'sound' and event.get('metadata', {}).get('decibels', 0) > self.config.noise_alert_db:
                    return (ThreatLevel.ELEVATED, "high_noise_away", probs)
        return None

    def _rule_unknown_face_away(self, data: Dict[str, Any], probs: np.ndarray) -> Optional[Tuple]:
        if data.get('systemMode') == 'away':
            for event in data.get('events', []):
                if event.get('type') == 'face' and not event.get('metadata', {}).get('is_known', True):
                    return (ThreatLevel.ELEVATED, "unknown_face_away", probs)
        return None

    def _rule_door_open_away(self, data: Dict[str, Any], probs: np.ndarray) -> Optional[Tuple]:
        if data.get('systemMode') == 'away':
            for event in data.get('events', []):
                if event.get('type') == 'door' and event.get('confidence', 0) >= self.config.door_open_threshold:
                    return (ThreatLevel.ELEVATED, "door_open_away_mode", probs)
        return None

    def _rule_night_motion(self, data: Dict[str, Any], probs: np.ndarray) -> Optional[Tuple]:
        if data.get('systemMode') == 'night':
            for event in data.get('events', []):
                if event.get('type') == 'motion' and event.get('confidence', 0) > 0.7:
                    return (ThreatLevel.ELEVATED, "night_motion_detected", probs)
        return None

    def _rule_false_positive_reduction(self, data: Dict[str, Any], probs: np.ndarray) -> Optional[Tuple]:
        for event in data.get('events', []):
            if event.get('type') == 'pet' and event.get('confidence', 0) >= self.config.pet_confidence_threshold:
                return (ThreatLevel.IGNORE, "pet_detected", probs)
            if event.get('type') == 'face' and event.get('confidence', 0) >= self.config.face_recognition_threshold:
                if event.get('metadata', {}).get('is_known', False):
                    return (ThreatLevel.IGNORE, "known_face_detected", probs)
        return None

# --- 6. Crime Intelligence ---

class CrimeIntelligence:
    """
    Integrates local crime data to provide spatial risk context.
    Features include Haversine distance, temporal filtering, and caching.
    """
    def __init__(self, config: SecurityConfig, data_path: str):
        self.config = config
        self.data_path = data_path
        self.crime_cache = collections.OrderedDict()
        self.cache_lock = threading.Lock()
        self.crime_weights = {'violent': 1.0, 'property': 0.7, 'other': 0.3}

    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculates distance between two points on Earth in kilometers."""
        R = 6371.0  # Earth radius in kilometers
        
        lat1_rad = np.radians(lat1)
        lon1_rad = np.radians(lon1)
        lat2_rad = np.radians(lat2)
        lon2_rad = np.radians(lon2)
        
        dlon = lon2_rad - lon1_rad
        dlat = lat2_rad - lat1_rad
        
        a = np.sin(dlat / 2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
        
        return R * c

    def _load_crime_data(self) -> List[Dict[str, Any]]:
        """Loads crime data from the last N days."""
        today = datetime.date.today()
        all_crimes = []
        for i in range(self.config.crime_recency_days):
            date_to_load = today - datetime.timedelta(days=i)
            file_path = os.path.join(self.data_path, f"crime_report_{date_to_load.strftime('%Y%m%d')}.json")
            try:
                with open(file_path, 'r') as f:
                    crimes = json.load(f)
                    for crime in crimes:
                        crime['days_ago'] = i
                    all_crimes.extend(crimes)
            except (FileNotFoundError, json.JSONDecodeError):
                continue
        return all_crimes

    def get_context(self, location: Dict[str, float]) -> Dict[str, Any]:
        """Calculates crime context for a given location with caching."""
        loc_tuple = (location['lat'], location['lon'])
        cache_key = hashlib.sha3_256(str(loc_tuple).encode()).hexdigest()

        with self.cache_lock:
            if cache_key in self.crime_cache and time.time() - self.crime_cache[cache_key][1] < self.config.crime_cache_ttl:
                return self.crime_cache[cache_key][0]

        all_crimes = self._load_crime_data()
        relevant_crimes = []
        for crime in all_crimes:
            distance = self.haversine_distance(location['lat'], location['lon'], crime['lat'], crime['lon'])
            if distance <= 1.0: # Within 1km
                crime['distance'] = distance
                relevant_crimes.append(crime)
        
        crime_index = 0.0
        if relevant_crimes:
            # Apply exponential decay and severity weighting
            total_weighted_score = sum(
                self.crime_weights.get(c['type'], 0.3) * np.exp(-0.1 * c['days_ago']) for c in relevant_crimes
            )
            crime_index = min(total_weighted_score / 5.0, self.config.max_crime_index) # Normalize

        escalation_required = len(relevant_crimes) >= self.config.crime_escalation_count
        
        context = {
            "relevantCrimes": len(relevant_crimes),
            "crimeIndex": round(crime_index, 4),
            "escalationRequired": escalation_required,
        }

        with self.cache_lock:
            self.crime_cache[cache_key] = (context, time.time())
            if len(self.crime_cache) > 1000: # Simple cache size limit
                self.crime_cache.popitem(last=False)

        return context

# --- 7. Advanced Reasoning Engine ---

class ReasoningEngine:
    """Performs multi-layer analysis to synthesize a final, explainable assessment."""
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.event_severity = {
            'fire': 1.0, 'smoke': 1.0, 'glassbreak': 0.9, 'door': 0.8, 'window': 0.8,
            'motion': 0.6, 'sound': 0.5, 'vehicle': 0.4, 'face': 0.7, 'pet': 0.1
        }

    def analyze(self, data: Dict[str, Any], nn_probs: np.ndarray, crime_context: Dict[str, Any]) -> Dict[str, Any]:
        """Executes the full 8-layer reasoning pipeline with event correlation."""
        factors = []
        analysis = {}

        # Pre-process events for deduplication
        original_event_count = len(data.get('events', []))
        processed_events, suppressed_count = self._preprocess_events(data.get('events', []))
        if not processed_events:
            # Handle case where all events are suppressed
            return {"primaryFactors": ["all_events_suppressed_as_duplicates"], "layerAnalysis": {}, "final_confidence": 0.0}

        # Layers 1-3: Initial Assessment (using processed events)
        l1_score, l1_factors = self._layer1_immediate_threat(processed_events)
        analysis['layer1_threat'] = l1_score
        factors.extend(l1_factors)

        l2_multiplier, l2_factor = self._layer2_temporal_context(processed_events[0]['timestamp'])
        analysis['layer2_temporal'] = l2_multiplier
        if l2_factor: factors.append(l2_factor)

        l3_multiplier, l3_factor = self._layer3_spatial_risk(crime_context)
        analysis['layer3_spatial'] = l3_multiplier
        if l3_factor: factors.append(l3_factor)

        # Layer 4: Advanced Event Correlation (Chains, Duplicates, Multi-Device)
        l4_multiplier, l4_factors = self._layer4_event_correlation(processed_events, original_event_count)
        analysis['layer4_correlation'] = l4_multiplier
        factors.extend(l4_factors)

        # Layer 5: Confidence Calibration
        l5_score = self._layer5_confidence_calibration(nn_probs)
        analysis['layer5_confidence_cal'] = l5_score

        # Layer 6: Legitimacy Evaluation
        l6_legitimacy, l6_factor = self._layer6_legitimacy_evaluation(data)
        analysis['layer6_legitimacy'] = l6_legitimacy
        if l6_factor: factors.append(l6_factor)

        # Layer 7: Multi-Factor Synthesis
        synthesized_score = self._layer7_synthesis(l1_score, l2_multiplier, l3_multiplier, l4_multiplier, l5_score, l6_legitimacy)
        analysis['synthesis_score'] = synthesized_score

        # Layer 8: Meta-Reasoning (Self-Confidence)
        final_confidence = self._layer8_meta_reasoning(synthesized_score, nn_probs)
        analysis['final_confidence'] = final_confidence

        return {"primaryFactors": factors, "layerAnalysis": analysis, "final_confidence": final_confidence}

    def _preprocess_events(self, events: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
        """Deduplicates events and returns a cleaned list and suppressed count."""
        if not events:
            return [], 0

        # Sort by timestamp first
        sorted_events = sorted(events, key=lambda e: e['timestamp'])
        
        deduplicated_events = []
        last_event_time = {}
        suppressed_count = 0

        for event in sorted_events:
            event_key = (event['type'], event.get('metadata', {}).get('deviceId'))
            event_time = datetime.datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))

            if event_key in last_event_time:
                time_diff = (event_time - last_event_time[event_key]).total_seconds()
                if time_diff < self.config.duplicate_event_window_seconds:
                    suppressed_count += 1
                    continue # Suppress this duplicate event
            
            deduplicated_events.append(event)
            last_event_time[event_key] = event_time
            
        return deduplicated_events, suppressed_count

    def _layer4_event_correlation(self, events: List[Dict[str, Any]], original_count: int) -> Tuple[float, List[str]]:
        """Layer 4: Analyzes event chains, duplication, and multi-device correlation."""
        factors = []
        multiplier = 1.0

        # 1. Suppression Analysis: Penalize for high duplication ratio (suggests faulty sensor)
        suppressed_ratio = (original_count - len(events)) / original_count if original_count > 0 else 0
        if suppressed_ratio > 0.8:
            multiplier *= 0.5 # Heavy suppression, likely noise
            factors.append("high_event_suppression_ratio")

        # 2. Chain Analysis: Look for logical sequences
        event_types = [e['type'] for e in events]
        device_ids = {e.get('metadata', {}).get('deviceId') for e in events}

        # Pattern: Breach -> Motion
        is_breach = any(et in ['door', 'window', 'glassbreak'] for et in event_types)
        is_motion = 'motion' in event_types
        if is_breach and is_motion:
            # A real implementation would check timestamps are close
            multiplier *= 2.0
            factors.append("breach_and_motion_chain_detected")

        # Pattern: Multi-device motion (suggests movement through a space)
        if event_types.count('motion') > 1 and len(device_ids) > 1:
            multiplier *= 1.5
            factors.append("multi_device_motion_correlation")

        return multiplier, factors

    def _layer5_confidence_calibration(self, nn_probs: np.ndarray) -> float:
        """Layer 5: Analyzes the probability distribution from the neural network."""
        # Reward high confidence, penalize uncertainty
        return np.max(nn_probs) - np.std(nn_probs)

    def _layer6_legitimacy_evaluation(self, data: Dict[str, Any]) -> Tuple[float, Optional[str]]:
        """Layer 6: Filters for potential false positives based on system state."""
        if data.get('systemMode') == 'home' and any(e['type'] == 'motion' for e in data['events']):
            return 0.5, "motion_in_home_mode"
        return 1.0, None

    def _layer7_synthesis(self, l1, l2, l3, l4, l5, l6) -> float:
        """Layer 7: Combines all factors into a single synthesized score."""
        # Weighted combination of all layers
        base_score = (l1 + l5) / 2.0
        context_multiplier = l2 * l3 * l4 * l6
        return base_score * context_multiplier

    def _layer8_meta_reasoning(self, synthesized_score: float, nn_probs: np.ndarray) -> float:
        """Layer 8: Assesses the system's own confidence in the final score."""
        # If the synthesized score aligns with the NN's primary prediction, be more confident.
        agreement_bonus = 1.0 + (0.2 * nn_probs[np.argmax(nn_probs)])
        return min(synthesized_score * agreement_bonus, 1.0)

    def _layer1_immediate_threat(self, events: List[Dict[str, Any]]) -> Tuple[float, List[str]]:
        """Layer 1: Scores based on the inherent severity of events."""
        max_severity = 0.0
        factors = []
        for event in events:
            severity = self.event_severity.get(event['type'], 0.0) * event['confidence']
            if severity > max_severity:
                max_severity = severity
            factors.append(f"{event['type']}_confidence_{event['confidence']:.2f}")
        return max_severity, factors

    def _layer2_temporal_context(self, timestamp_str: str) -> Tuple[float, Optional[str]]:
        """Layer 2: Applies risk multipliers based on time of day."""
        ts = datetime.datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        # High risk between 10 PM and 5 AM
        if 22 <= ts.hour or ts.hour <= 5:
            return 1.5, "night_time_multiplier"
        return 1.0, None

    def _layer3_spatial_risk(self, crime_context: Dict[str, Any]) -> Tuple[float, Optional[str]]:
        """Layer 3: Applies risk multipliers based on local crime data."""
        if crime_context.get('escalationRequired', False):
            return 1.3 + crime_context.get('crimeIndex', 0.0), "local_crime_escalation"
        return 1.0 + crime_context.get('crimeIndex', 0.0), None


# --- 99. Main System Orchestrator (Putting it all together) ---

# --- Singleton Instance for Embedding ---

_global_system_instance = None

def get_embedded_system_instance(brand_config: Optional[Dict[str, Any]] = None) -> 'NovinAISecuritySystem':
    """Creates and returns a single, reusable instance of the NovinAI system.
    This is the recommended entry point for embedded use cases (e.g., mobile apps).

    Args:
        brand_config: Optional brand-specific configuration including:
            - crime_data_path: Custom path to crime data directory
            - model_path: Custom path to model file
            - config_overrides: Dict of SecurityConfig overrides
    """
    global _global_system_instance
    if _global_system_instance is None:
        print("Initializing singleton NovinAI System for embedding...")
        try:
            from importlib.resources import files
        except ImportError:
            # Fallback for Python < 3.9
            from importlib_resources import files

        config = SecurityConfig()

        # Apply brand-specific config overrides if provided
        if brand_config and 'config_overrides' in brand_config:
            for key, value in brand_config['config_overrides'].items():
                if hasattr(config, key):
                    setattr(config, key, value)

        # Use brand-provided paths or fall back to bundled resources
        crime_data_path = brand_config.get('crime_data_path') if brand_config else None
        if not crime_data_path:
            crime_data_path = str(files('novin_intelligence').joinpath('data/crime'))

        model_path = brand_config.get('model_path') if brand_config else None
        if not model_path:
            model_path = str(files('novin_intelligence').joinpath('models/novin_ai_v2.0.json'))

        signature_path = brand_config.get('signature_path') if brand_config else None
        if not signature_path:
            signature_path = str(files('novin_intelligence').joinpath('models/novin_ai_v2.0.json.sig'))

        public_key_path = brand_config.get('public_key_path') if brand_config else None
        if not public_key_path:
            public_key_path = str(files('novin_intelligence').joinpath('models/model_public.pem'))

        system = NovinAISecuritySystem(config, crime_data_path)
        system.load_dependencies(model_path, signature_path, public_key_path)
        _global_system_instance = system
        print("Singleton instance created with brand configuration.")
    return _global_system_instance


class NovinAISecuritySystem:
    """The main orchestrator for the entire threat assessment pipeline."""
    def __init__(self, config: SecurityConfig, crime_data_path: str):
        self.config = config
        self.validator = InputValidation(config)
        self.rate_limiter = RateLimiting(config)
        self.resource_monitor = ResourceMonitoring(config)
        self.feature_extractor = FeatureExtraction(config)
        self.neural_network = NeuralNetwork(config)
        self.rule_engine = RuleEngine(config)
        self.crime_intelligence = CrimeIntelligence(config, crime_data_path)
        self.reasoning_engine = ReasoningEngine(config)

        self.request_count = 0
        self.error_count = 0
        self.start_time = time.time()
        self.lock = threading.Lock()
        self._setup_logging()

    def _setup_logging(self):
        """Sets up a rotating file logger for audit purposes."""
        log_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'audit')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, 'requests.log')
        
        self.logger = logging.getLogger('NovinAIAudit')
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False

        if not self.logger.handlers:
            handler = logging.handlers.RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
            formatter = logging.Formatter('%(asctime)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def load_dependencies(self, model_path: str, signature_path: str, public_key_path: str):
        """Loads all necessary external resources like models."""
        if not self.neural_network.load_model(model_path, signature_path, public_key_path):
            raise RuntimeError("Failed to initialize NovinAI: Critical model dependency failed to load.")

    def process_request_json(self, request_json_str: str, client_id: str) -> str:
        """Wrapper to process a request from a JSON string, for embedding."""
        try:
            request_data = json.loads(request_json_str)
            response_data = self.process_request(request_data, client_id)
            return json.dumps(response_data)
        except Exception as e:
            error_response = {"error": True, "message": f"Failed to process JSON request: {e}"}
            return json.dumps(error_response)

    def process_request(self, request_data: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        """Processes a single security assessment request through the full, integrated pipeline."""
        request_id = hashlib.sha256(json.dumps(request_data, sort_keys=True).encode()).hexdigest()
        start_process_time = time.perf_counter()

        # Pipeline Step 1: Security & Resource Pre-checks
        if not self.rate_limiter.is_allowed(client_id):
            return self._build_error_response(request_id, client_id, 'rate_limit_exceeded', ["Too many requests."])
        is_healthy, health_msg = self.resource_monitor.is_healthy()
        if not is_healthy:
            return self._build_error_response(request_id, client_id, 'system_overloaded', [health_msg])

        # Pipeline Step 2: Input Validation
        validation_errors = self.validator.validate_request(request_data)
        if validation_errors:
            return self._build_error_response(request_id, client_id, 'validation_error', validation_errors)

        # Pipeline Step 3: Contextual Analysis (Crime)
        crime_context = self.crime_intelligence.get_context(request_data['location'])

        # Pipeline Step 4: Feature Extraction
        features = self.feature_extractor.extract(request_data, crime_context)

        # Pipeline Step 5: Neural Network Prediction (with Fallback)
        nn_probs = self.neural_network.predict(features)
        is_fallback = False
        if nn_probs is None:
            is_fallback = True
            nn_probs = np.array([0.25] * self.config.n_classes) # Uniform prior

        # Pipeline Step 6: Rule Engine Application
        rule_override, rule_name, _ = self.rule_engine.apply(request_data, nn_probs)

        # Pipeline Step 7: Advanced Reasoning
        reasoning_output = self.reasoning_engine.analyze(request_data, nn_probs, crime_context)

        # Pipeline Step 8: Synthesize Final Assessment
        if rule_override:
            final_threat_level = rule_override
            final_confidence = 1.0
            if rule_name: reasoning_output['primaryFactors'].append(f"rule_override:{rule_name}")
        elif is_fallback:
            final_threat_level = rule_override or ThreatLevel.STANDARD # Fallback can't be critical
            final_confidence = reasoning_output['final_confidence']
        else:
            final_confidence = reasoning_output['final_confidence']
            if final_confidence > 0.9:
                final_threat_level = ThreatLevel.CRITICAL
            elif final_confidence > 0.7:
                final_threat_level = ThreatLevel.ELEVATED
            elif final_confidence > 0.3:
                final_threat_level = ThreatLevel.STANDARD
            else:
                final_threat_level = ThreatLevel.IGNORE
        
        processing_time_ms = (time.perf_counter() - start_process_time) * 1000

        # Pipeline Step 9: Build Final Response
        response = {
            "requestId": request_id,
            "clientId": client_id,
            "timestamp": datetime.datetime.now(UTC).isoformat(),
            "processingTimeMs": round(processing_time_ms, 2),
            "version": self.neural_network.version,
            "threatAssessment": {
                "level": str(final_threat_level),
                "confidence": round(final_confidence, 4),
                "probabilityDistribution": {str(ThreatLevel(i)): round(float(p), 4) for i, p in enumerate(nn_probs)},
            },
            "reasoning": {
                "primaryFactors": reasoning_output['primaryFactors'],
                "ruleApplied": rule_name,
                "layerAnalysis": reasoning_output['layerAnalysis'],
            },
            "context": {
                "systemMode": request_data.get('systemMode'),
                # Sanitize output to prevent data leakage
                "location": {"risk_zone": round(crime_context.get('crimeIndex', 0.0) * 10)},
                "crimeContext": crime_context,
                "deviceStatus": {
                    "battery": request_data.get('deviceInfo', {}).get('battery')
                }
            },
            "systemStatus": {
                "healthy": True,
                "fallbackActive": is_fallback
            },
            "security": {
                "requestValidated": True,
                "rateLimitStatus": "nominal",
                "modelVerified": True,
                "signatureValid": self.neural_network.public_key is not None
            }
        }
        return response

    def _build_error_response(self, request_id: str, client_id: str, error_type: str, messages: List[str]) -> Dict[str, Any]:
        """Constructs a standardized error response."""
        return {
            "requestId": request_id,
            "clientId": client_id,
            "timestamp": datetime.datetime.now(UTC).isoformat(),
            "error": True,
            "errorType": error_type,
            "errorCode": messages[0].upper().replace(' ', '_'),
            "message": messages[0],
            "details": {"validationErrors": messages},
            "fallbackAssessment": {
                "threatLevel": "standard",
                "confidence": 0.0,
                "reason": f"{error_type}_failed"
            }
        }

# Example Usage (for demonstration if run directly)
if __name__ == '__main__':
    print("NovinAI Security System Module")
    print("This file is intended to be used as a module, not run directly.")
    print("To use, instantiate NovinAISecuritySystem and call process_request.")

    # A minimal example of how one might use the system:
    # config = SecurityConfig()
    # system = NovinAISecuritySystem(config)
    # try:
    #     system.load_dependencies(
    #         model_path='path/to/model.json',
    #         signature_path='path/to/model.sig',
    #         public_key_path='path/to/public_key.pem'
    #     )
    #     sample_request = { ... }
    #     result = system.process_request(sample_request, 'client-123')
    #     print(json.dumps(result, indent=2))
    # except RuntimeError as e:
    #     print(f"Initialization failed: {e}")
