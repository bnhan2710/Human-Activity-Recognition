"""
Firebase Handler Module
Manages Firebase Realtime Database and Firestore connection and data streaming
"""

import firebase_admin
from firebase_admin import credentials, db, firestore
import logging
from typing import Callable, Optional, Dict, Any, List
import threading
import json
import os
from datetime import datetime

logger = logging.getLogger(__name__)


class FirebaseHandler:
    """
    Handles Firebase Realtime Database connection and real-time data streaming
    """
    
    def __init__(self, database_url: str, service_account_path: Optional[str] = None, 
                 credentials_dict: Optional[Dict] = None, use_firestore: bool = True):
        """
        Initialize Firebase connection
        
        Args:
            database_url: Firebase Realtime Database URL
            service_account_path: Path to service account JSON file
            credentials_dict: Service account credentials as dictionary (alternative to file)
            use_firestore: Whether to initialize Firestore client
        """
        self.database_url = database_url
        self.service_account_path = service_account_path
        self.credentials_dict = credentials_dict
        self.use_firestore = use_firestore
        self._connected = False
        self._listener_ref = None
        self._listener_thread = None
        self._firestore_client = None
        
        # Initialize Firebase
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Check if already initialized
            if firebase_admin._apps:
                logger.info("ℹ️ Firebase already initialized, reusing existing app")
                # Get existing Firestore client if needed
                if self.use_firestore and not self._firestore_client:
                    self._firestore_client = firestore.client()
                    logger.info("✅ Firestore client initialized from existing app")
                self._connected = True
                return
            
            # Get credentials
            if self.service_account_path:
                if not os.path.exists(self.service_account_path):
                    raise FileNotFoundError(f"Service account file not found: {self.service_account_path}")
                cred = credentials.Certificate(self.service_account_path)
            elif self.credentials_dict:
                cred = credentials.Certificate(self.credentials_dict)
            else:
                # Try to use default credentials
                cred = credentials.ApplicationDefault()
            
            # Initialize app
            firebase_admin.initialize_app(cred, {
                'databaseURL': self.database_url
            })
            
            # Initialize Firestore client if requested
            if self.use_firestore:
                self._firestore_client = firestore.client()
                logger.info(f"✅ Firestore client initialized")
            
            self._connected = True
            logger.info(f" Firebase initialized successfully: {self.database_url}")
        
        except Exception as e:
            logger.error(f" Failed to initialize Firebase: {e}")
            self._connected = False
            raise
    
    def is_connected(self) -> bool:
        """Check if Firebase is connected"""
        return self._connected
    
    def start_listening(self, callback: Callable[[Dict[str, Any]], None], path: str = "/sensor_data"):
        """
        Start listening to a Firebase path for real-time updates
        
        Args:
            callback: Function to call when data changes (receives data dict)
            path: Firebase database path to listen to
        """
        if not self._connected:
            raise ConnectionError("Firebase not connected")
        
        try:
            logger.info(f"🔍 Attempting to connect to Firebase Realtime Database: {path}")
            
            # Get reference to path
            ref = db.reference(path)
            
            # Test connection by trying to read once first
            logger.info(f"   Testing connection with read_once...")
            try:
                test_data = ref.get()
                logger.info(f"   ✅ Connection test successful!")
                logger.info(f"   📊 Data exists: {test_data is not None}")
                if test_data and isinstance(test_data, dict):
                    logger.info(f"   📊 Number of entries: {len(test_data)}")
            except Exception as test_err:
                logger.error(f"   ❌ Connection test failed: {test_err}")
                raise ConnectionError(f"Failed to establish a connection: {test_err}")
            
            # Define listener
            def listener(event):
                """Handle Firebase data changes"""
                try:
                    data = event.data
                    if data:
                        logger.debug(f"📨 Received data from Firebase: {path}")
                        callback(data)
                except Exception as e:
                    logger.error(f"Error in Firebase listener callback: {e}")
            
            # Attach listener
            logger.info(f"   🎧 Attaching real-time listener...")
            ref.listen(listener)
            self._listener_ref = ref
            
            logger.info(f"✅ Started listening to Firebase path: {path}")
        
        except Exception as e:
            logger.error(f"❌ Failed to start Firebase listener: {e}")
            raise
    
    def stop_listening(self):
        """Stop listening to Firebase"""
        if self._listener_ref:
            # Firebase Admin SDK doesn't have explicit stop for listeners
            # Set ref to None to allow garbage collection
            self._listener_ref = None
            logger.info(" Stopped Firebase listener")
    
    def read_once(self, path: str = "/sensor_data") -> Optional[Dict]:
        """
        Read data from Firebase once (not streaming)
        
        Args:
            path: Firebase database path to read from
            
        Returns:
            Data from Firebase or None if not found
        """
        if not self._connected:
            raise ConnectionError("Firebase not connected")
        
        try:
            ref = db.reference(path)
            data = ref.get()
            logger.debug(f"📖 Read data from Firebase: {path}")
            return data
        
        except Exception as e:
            logger.error(f" Failed to read from Firebase: {e}")
            return None
    
    def write_data(self, path: str, data: Dict[str, Any]):
        """
        Write data to Firebase
        
        Args:
            path: Firebase database path to write to
            data: Data to write
        """
        if not self._connected:
            raise ConnectionError("Firebase not connected")
        
        try:
            ref = db.reference(path)
            ref.set(data)
            logger.debug(f"✍️ Wrote data to Firebase: {path}")
        
        except Exception as e:
            logger.error(f" Failed to write to Firebase: {e}")
            raise
    
    def push_data(self, path: str, data: Dict[str, Any]) -> str:
        """
        Push data to Firebase (creates new child with unique key)
        
        Args:
            path: Firebase database path to push to
            data: Data to push
            
        Returns:
            Key of the pushed data
        """
        if not self._connected:
            raise ConnectionError("Firebase not connected")
        
        try:
            ref = db.reference(path)
            new_ref = ref.push(data)
            key = new_ref.key
            logger.debug(f"📤 Pushed data to Firebase: {path}/{key}")
            return key
        
        except Exception as e:
            logger.error(f" Failed to push to Firebase: {e}")
            raise
    
    def send_prediction(self, activity: str, confidence: float, probabilities: Dict[str, float], 
                       path: str = "/predictions"):
        """
        Send prediction result to Firebase Realtime Database
        
        Args:
            activity: Predicted activity name
            confidence: Confidence score
            probabilities: Probabilities for all activities
            path: Firebase path to write to
        """
        from datetime import datetime
        
        prediction_data = {
            'activity': activity,
            'confidence': confidence,
            'probabilities': probabilities,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            self.push_data(path, prediction_data)
            logger.info(f" Sent prediction to Firebase: {activity} ({confidence:.2%})")
        except Exception as e:
            logger.error(f"Failed to send prediction to Firebase: {e}")
    
    # ==================== Firestore Methods ====================
    
    def get_firestore_client(self):
        """Get Firestore client instance"""
        if not self._firestore_client:
            raise ConnectionError("Firestore client not initialized. Set use_firestore=True")
        return self._firestore_client
    
    def save_prediction_to_firestore(self, activity: str, confidence: float, 
                                     probabilities: Dict[str, float], 
                                     user_id: str = "user1",
                                     collection: str = "activity_predictions",
                                     start_time: Optional[datetime] = None,
                                     end_time: Optional[datetime] = None,
                                     duration_seconds: Optional[float] = None) -> str:
        """
        Save prediction result to Firestore
        
        Args:
            activity: Predicted activity name
            confidence: Confidence score (0-1)
            probabilities: Dictionary of activity probabilities
            user_id: User identifier
            collection: Firestore collection name
            start_time: Activity start timestamp
            end_time: Activity end timestamp
            duration_seconds: Activity duration in seconds
            
        Returns:
            Document ID of the saved prediction
        """
        if not self._firestore_client:
            raise ConnectionError("Firestore client not initialized")
        
        try:
            now = datetime.now()
            prediction_data = {
                'activity': activity,
                'confidence': confidence,
                'probabilities': probabilities,
                'timestamp': firestore.SERVER_TIMESTAMP,
                'created_at': now.isoformat(),
                'user_id': user_id,
                'start_time': start_time.isoformat() if start_time else now.isoformat(),
                'end_time': end_time.isoformat() if end_time else now.isoformat(),
                'duration_seconds': duration_seconds if duration_seconds is not None else 2.0
            }
            
            # Add document to collection
            doc_ref = self._firestore_client.collection(collection).add(prediction_data)
            doc_id = doc_ref[1].id
            
            logger.info(f"✅ Saved prediction to Firestore: {activity} ({confidence:.2%}) - Duration: {prediction_data['duration_seconds']}s - Doc ID: {doc_id}")
            return doc_id
        
        except Exception as e:
            logger.error(f"❌ Failed to save prediction to Firestore: {e}")
            raise
    
    def get_predictions_from_firestore(self, user_id: str = "user1", 
                                       collection: str = "activity_predictions",
                                       limit: int = 10) -> List[Dict]:
        """
        Get recent predictions from Firestore
        
        Args:
            user_id: User identifier
            collection: Firestore collection name
            limit: Maximum number of predictions to retrieve
            
        Returns:
            List of prediction documents
        """
        if not self._firestore_client:
            raise ConnectionError("Firestore client not initialized")
        
        try:
            predictions = []
            
            # Query without ordering to avoid index requirement
            # We'll sort in memory instead
            docs = (self._firestore_client.collection(collection)
                   .where('user_id', '==', user_id)
                   .stream())
            
            for doc in docs:
                pred_data = doc.to_dict()
                pred_data['id'] = doc.id
                predictions.append(pred_data)
            
            # Sort by created_at in memory (descending)
            predictions.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            # Apply limit after sorting
            predictions = predictions[:limit]
            
            logger.info(f"📖 Retrieved {len(predictions)} predictions from Firestore")
            return predictions
        
        except Exception as e:
            logger.error(f"❌ Failed to retrieve predictions from Firestore: {e}")
            raise
    
    def update_prediction_in_firestore(self, doc_id: str, update_data: Dict[str, Any],
                                       collection: str = "activity_predictions"):
        """
        Update a prediction document in Firestore
        
        Args:
            doc_id: Document ID to update
            update_data: Data to update
            collection: Firestore collection name
        """
        if not self._firestore_client:
            raise ConnectionError("Firestore client not initialized")
        
        try:
            doc_ref = self._firestore_client.collection(collection).document(doc_id)
            doc_ref.update(update_data)
            logger.info(f"✅ Updated prediction in Firestore: {doc_id}")
        
        except Exception as e:
            logger.error(f"❌ Failed to update prediction in Firestore: {e}")
            raise
    
    def delete_prediction_from_firestore(self, doc_id: str, 
                                         collection: str = "activity_predictions"):
        """
        Delete a prediction document from Firestore
        
        Args:
            doc_id: Document ID to delete
            collection: Firestore collection name
        """
        if not self._firestore_client:
            raise ConnectionError("Firestore client not initialized")
        
        try:
            self._firestore_client.collection(collection).document(doc_id).delete()
            logger.info(f"🗑️ Deleted prediction from Firestore: {doc_id}")
        
        except Exception as e:
            logger.error(f"❌ Failed to delete prediction from Firestore: {e}")
            raise
    
    def disconnect(self):
        """Disconnect from Firebase"""
        if self._connected:
            self.stop_listening()
            
            # Delete the app
            if firebase_admin._apps:
                firebase_admin.delete_app(firebase_admin.get_app())
            
            self._connected = False
            logger.info(" Firebase disconnected")
    
    def __del__(self):
        """Cleanup on deletion"""
        self.disconnect()


class FirebaseStreamListener:
    """
    Advanced Firebase listener with buffering and batch processing
    """
    
    def __init__(self, handler: FirebaseHandler, callback: Callable, 
                 buffer_size: int = 10, path: str = "/sensor_data"):
        """
        Initialize stream listener with buffering
        
        Args:
            handler: FirebaseHandler instance
            callback: Callback function for batch processing
            buffer_size: Number of samples to buffer before calling callback
            path: Firebase path to listen to
        """
        self.handler = handler
        self.callback = callback
        self.buffer_size = buffer_size
        self.path = path
        self.buffer = []
        self._lock = threading.Lock()
    
    def _buffer_callback(self, data: Dict[str, Any]):
        """Internal callback that buffers data"""
        with self._lock:
            self.buffer.append(data)
            
            if len(self.buffer) >= self.buffer_size:
                # Process batch
                batch = self.buffer.copy()
                self.buffer.clear()
                
                # Call user callback with batch
                try:
                    self.callback(batch)
                except Exception as e:
                    logger.error(f"Error in batch callback: {e}")
    
    def start(self):
        """Start listening with buffering"""
        self.handler.start_listening(self._buffer_callback, self.path)
        logger.info(f" Started buffered listener (buffer_size={self.buffer_size})")
    
    def stop(self):
        """Stop listening and process remaining buffer"""
        with self._lock:
            if self.buffer:
                # Process remaining data
                try:
                    self.callback(self.buffer)
                except Exception as e:
                    logger.error(f"Error processing remaining buffer: {e}")
                self.buffer.clear()
        
        self.handler.stop_listening()
        logger.info(" Stopped buffered listener")
