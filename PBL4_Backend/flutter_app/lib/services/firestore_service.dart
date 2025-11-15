import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';

class FirestoreService {
  static final FirebaseFirestore _firestore = FirebaseFirestore.instance;

  /// Lưu kết quả dự đoán hoạt động lên Firestore
  static Future<void> saveActivity({
    required String activity,
    required DateTime startTime,
    required DateTime endTime,
    required double confidence,
  }) async {
    try {
      final user = FirebaseAuth.instance.currentUser;
      if (user == null) {
        print('User not authenticated');
        return;
      }

      final duration = endTime.difference(startTime).inSeconds;

      // Tính calo dựa trên MET values
      final caloriesBurned = _calculateCalories(activity, duration);

      await _firestore.collection('activities').add({
        'userId': user.uid,
        'activity': activity,
        'startTime': Timestamp.fromDate(startTime),
        'endTime': Timestamp.fromDate(endTime),
        'duration': duration,
        'confidence': confidence,
        'caloriesBurned': caloriesBurned,
        'createdAt': FieldValue.serverTimestamp(),
      });

      print(
        'Activity saved: $activity (${duration}s, ${caloriesBurned.toStringAsFixed(1)} kcal)',
      );
    } catch (e) {
      print('Error saving activity: $e');
    }
  }

  /// Tính calories dựa trên MET values
  static double _calculateCalories(String activity, int durationSeconds) {
    // MET values cho từng hoạt động
    const metValues = {
      'Đứng': 1.3,
      'Ngồi': 1.0,
      'Chạy': 7.0,
      'Đi bộ': 3.5,
      'Leo cầu thang': 3.5,
    };

    final met = metValues[activity] ?? 1.0;
    const weight = 70.0; // Default weight, có thể lấy từ user profile
    final durationHours = durationSeconds / 3600.0;

    return met * weight * durationHours;
  }

  /// Lấy lịch sử hoạt động theo ngày
  static Stream<QuerySnapshot> getActivitiesByDate(DateTime date) {
    final user = FirebaseAuth.instance.currentUser;
    if (user == null) {
      return const Stream.empty();
    }

    final startOfDay = DateTime(date.year, date.month, date.day);
    final endOfDay = startOfDay.add(const Duration(days: 1));

    return _firestore
        .collection('activities')
        .where('userId', isEqualTo: user.uid)
        .where(
          'startTime',
          isGreaterThanOrEqualTo: Timestamp.fromDate(startOfDay),
        )
        .where('startTime', isLessThan: Timestamp.fromDate(endOfDay))
        .orderBy('startTime', descending: false)
        .snapshots();
  }

  /// Lấy tổng calo theo ngày
  static Future<double> getTotalCaloriesByDate(DateTime date) async {
    final user = FirebaseAuth.instance.currentUser;
    if (user == null) return 0.0;

    final startOfDay = DateTime(date.year, date.month, date.day);
    final endOfDay = startOfDay.add(const Duration(days: 1));

    final snapshot = await _firestore
        .collection('activities')
        .where('userId', isEqualTo: user.uid)
        .where(
          'startTime',
          isGreaterThanOrEqualTo: Timestamp.fromDate(startOfDay),
        )
        .where('startTime', isLessThan: Timestamp.fromDate(endOfDay))
        .get();

    double total = 0.0;
    for (var doc in snapshot.docs) {
      total += (doc.data()['caloriesBurned'] ?? 0.0).toDouble();
    }

    return total;
  }

  /// Tạo thông báo khi ngồi quá lâu
  static Future<void> createSittingWarning(int durationMinutes) async {
    final user = FirebaseAuth.instance.currentUser;
    if (user == null) return;

    await _firestore.collection('notifications').add({
      'userId': user.uid,
      'type': 'sitting_warning',
      'title': 'Cảnh báo ngồi quá lâu',
      'message':
          'Bạn đã ngồi liên tục $durationMinutes phút. Hãy đứng dậy hoạt động!',
      'isRead': false,
      'createdAt': FieldValue.serverTimestamp(),
    });
  }

  /// Lấy danh sách thông báo
  static Stream<QuerySnapshot> getNotifications() {
    final user = FirebaseAuth.instance.currentUser;
    if (user == null) {
      return const Stream.empty();
    }

    return _firestore
        .collection('notifications')
        .where('userId', isEqualTo: user.uid)
        .orderBy('createdAt', descending: true)
        .limit(10)
        .snapshots();
  }

  /// Đánh dấu thông báo đã đọc
  static Future<void> markNotificationAsRead(String notificationId) async {
    await _firestore.collection('notifications').doc(notificationId).update({
      'isRead': true,
    });
  }
}
