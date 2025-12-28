import 'package:cloud_firestore/cloud_firestore.dart';
import 'dart:async';

class ActivityService {
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;

  // Singleton
  static final ActivityService _instance = ActivityService._internal();
  factory ActivityService() => _instance;
  ActivityService._internal();

  /// Stream để listen activity realtime từ Firestore
  Stream<Map<String, dynamic>> listenCurrentActivity(
      {String userId = 'user1'}) {
    return _firestore
        .collection('activity_predictions')
        .where('user_id', isEqualTo: userId)
        .orderBy('timestamp', descending: true)
        .limit(1)
        .snapshots()
        .map((snapshot) {
      if (snapshot.docs.isEmpty) {
        return {
          'activity': 'UNKNOWN',
          'confidence': 0.0,
          'timestamp': DateTime.now(),
        };
      }

      final doc = snapshot.docs.first;
      final data = doc.data();

      return {
        'activity': data['activity'] ?? 'UNKNOWN',
        'confidence': data['confidence'] ?? 0.0,
        'probabilities': data['probabilities'] ?? {},
        'timestamp':
            (data['timestamp'] as Timestamp?)?.toDate() ?? DateTime.now(),
      };
    });
  }

  /// Get latest activity (one-time)
  Future<Map<String, dynamic>> getLatestActivity(
      {String userId = 'user1'}) async {
    try {
      final snapshot = await _firestore
          .collection('activity_predictions')
          .where('user_id', isEqualTo: userId)
          .orderBy('timestamp', descending: true)
          .limit(1)
          .get();

      if (snapshot.docs.isEmpty) {
        return {
          'activity': 'UNKNOWN',
          'confidence': 0.0,
        };
      }

      final data = snapshot.docs.first.data();
      return {
        'activity': data['activity'] ?? 'UNKNOWN',
        'confidence': data['confidence'] ?? 0.0,
        'probabilities': data['probabilities'] ?? {},
        'timestamp':
            (data['timestamp'] as Timestamp?)?.toDate() ?? DateTime.now(),
      };
    } catch (e) {
      print('Error getting latest activity: $e');
      return {
        'activity': 'ERROR',
        'confidence': 0.0,
      };
    }
  }

  /// Get activity history
  Stream<List<Map<String, dynamic>>> getActivityHistory({
    String userId = 'user1',
    int limit = 20,
  }) {
    return _firestore
        .collection('activity_predictions')
        .where('user_id', isEqualTo: userId)
        .orderBy('timestamp', descending: true)
        .limit(limit)
        .snapshots()
        .map((snapshot) {
      return snapshot.docs.map((doc) {
        final data = doc.data();
        return {
          'activity': data['activity'] ?? 'UNKNOWN',
          'confidence': data['confidence'] ?? 0.0,
          'timestamp':
              (data['timestamp'] as Timestamp?)?.toDate() ?? DateTime.now(),
        };
      }).toList();
    });
  }
}
