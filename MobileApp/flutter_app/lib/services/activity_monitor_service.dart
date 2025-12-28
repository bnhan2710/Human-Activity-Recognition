import 'dart:async';
import 'package:cloud_firestore/cloud_firestore.dart';

class ActivityMonitorService {
  static final ActivityMonitorService _instance =
      ActivityMonitorService._internal();
  factory ActivityMonitorService() => _instance;
  ActivityMonitorService._internal();

  final String userId = 'user1';
  StreamSubscription? _subscription;

  // Tracking sitting duration
  DateTime? _sittingStartTime;
  double _totalSittingSeconds = 0.0;
  String? _currentActivity;
  bool _hasNotifiedOneMinute = false; // Đổi từ 5 phút thành 1 phút

  // Callbacks for notifications
  Function(String message, Duration duration)? onSittingAlert;
  Function(String activity, double confidence)? onActivityChange;

  void startMonitoring() {
    print('🔍 Starting activity monitoring...');

    // Use timestamp ordering with limit to get only latest document
    // This is much faster than fetching all documents
    _subscription = FirebaseFirestore.instance
        .collection('activity_predictions')
        .where('user_id', isEqualTo: userId)
        .orderBy('timestamp', descending: true) // Use server timestamp field
        .limit(1) // Only get the most recent document
        .snapshots()
        .listen(
      (snapshot) {
        if (snapshot.docs.isNotEmpty) {
          final data = snapshot.docs.first.data();
          _handleNewPrediction(data);
        }
      },
      onError: (error) {
        print('❌ Monitor error: $error');
        // If index error, fallback to simpler query
        if (error.toString().contains('index')) {
          print('⚠️ Index required. Please create index or use simpler query.');
        }
      },
    );
  }

  void _handleNewPrediction(Map<String, dynamic> data) {
    final activity = data['activity'] ?? 'UNKNOWN';
    final confidence = (data['confidence'] ?? 0.0).toDouble();
    final durationSeconds = (data['duration_seconds'] ?? 2.0).toDouble();

    print(
        '📊 Activity: $activity, Confidence: ${(confidence * 100).toStringAsFixed(1)}%');

    // Notify activity change
    onActivityChange?.call(activity, confidence);

    if (activity == 'SITTING') {
      _handleSitting(durationSeconds);
    } else {
      _resetSitting();
    }
  }

  void _handleSitting(double durationSeconds) {
    // If just started sitting
    if (_currentActivity != 'SITTING') {
      _sittingStartTime = DateTime.now();
      _totalSittingSeconds = durationSeconds;
      _hasNotifiedOneMinute = false;
      print('🪑 Started sitting at ${_sittingStartTime}');
    } else {
      // Continue sitting - accumulate time
      _totalSittingSeconds += durationSeconds;
      print(
          '🪑 Total sitting time: ${_totalSittingSeconds.toStringAsFixed(1)}s');
    }

    _currentActivity = 'SITTING';

    // Check if exceeded 1 minute (60 seconds)
    if (_totalSittingSeconds >= 60 && !_hasNotifiedOneMinute) {
      _triggerSittingAlert();
      _hasNotifiedOneMinute = true;
    }
  }

  void _resetSitting() {
    if (_currentActivity == 'SITTING' && _sittingStartTime != null) {
      final duration = Duration(seconds: _totalSittingSeconds.toInt());
      print('✅ Stopped sitting. Total duration: ${_formatDuration(duration)}');
    }

    _sittingStartTime = null;
    _totalSittingSeconds = 0.0;
    _currentActivity = null;
    _hasNotifiedOneMinute = false;
  }

  void _triggerSittingAlert() {
    final duration = Duration(seconds: _totalSittingSeconds.toInt());
    final message =
        '⚠️ Bạn đã ngồi ${_formatDuration(duration)}! Hãy đứng dậy vận động.';

    print('🔔 ALERT: $message');

    // Save notification to Firestore
    _saveNotification(
      title: 'Cảnh báo: Ngồi quá lâu!',
      message:
          'Bạn đã ngồi hơn 1 phút. Hãy đứng dậy và vận động để tốt cho sức khỏe.',
      type: 'sitting_alert',
      duration: duration,
    );

    // Trigger callback
    onSittingAlert?.call(message, duration);
  }

  Future<void> _saveNotification({
    required String title,
    required String message,
    required String type,
    required Duration duration,
  }) async {
    try {
      await FirebaseFirestore.instance.collection('notifications').add({
        'user_id': userId,
        'title': title,
        'message': message,
        'type': type,
        'duration_minutes': duration.inMinutes,
        'is_read': false,
        'created_at': FieldValue.serverTimestamp(),
        'timestamp': DateTime.now().toIso8601String(),
      });
      print('✅ Notification saved to Firestore');
    } catch (e) {
      print('❌ Error saving notification: $e');
    }
  }

  String _formatDuration(Duration duration) {
    final minutes = duration.inMinutes;
    final seconds = duration.inSeconds % 60;
    if (minutes > 0) {
      return '$minutes phút $seconds giây';
    }
    return '$seconds giây';
  }

  // Get current sitting status
  Map<String, dynamic> getSittingStatus() {
    if (_currentActivity == 'SITTING' && _sittingStartTime != null) {
      return {
        'is_sitting': true,
        'duration_seconds': _totalSittingSeconds,
        'start_time': _sittingStartTime!.toIso8601String(),
        'has_alerted': _hasNotifiedOneMinute,
      };
    }
    return {
      'is_sitting': false,
      'duration_seconds': 0.0,
      'start_time': null,
      'has_alerted': false,
    };
  }

  void stopMonitoring() {
    print('🛑 Stopping activity monitoring');
    _subscription?.cancel();
    _resetSitting();
  }

  void dispose() {
    stopMonitoring();
  }
}
