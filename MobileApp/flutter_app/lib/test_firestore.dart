import 'package:cloud_firestore/cloud_firestore.dart';

void main() async {
  // Test Firestore connection
  print('Testing Firestore connection...');

  try {
    final firestore = FirebaseFirestore.instance;

    // Check if there's any data
    final snapshot = await firestore
        .collection('activity_predictions')
        .orderBy('timestamp', descending: true)
        .limit(5)
        .get();

    print('✅ Firestore connected!');
    print('   Found ${snapshot.docs.length} predictions');

    if (snapshot.docs.isNotEmpty) {
      print('\nLatest predictions:');
      for (var doc in snapshot.docs) {
        final data = doc.data();
        print(
            '   - ${data['activity']}: ${(data['confidence'] * 100).toStringAsFixed(1)}%');
      }
    } else {
      print('\n⚠️ No predictions found in Firestore');
      print('   Make sure backend has predicted and saved data');
    }

    // Test stream
    print('\nTesting stream...');
    final stream = firestore
        .collection('activity_predictions')
        .where('user_id', isEqualTo: 'user1')
        .orderBy('timestamp', descending: true)
        .limit(1)
        .snapshots();

    stream.listen((snapshot) {
      if (snapshot.docs.isNotEmpty) {
        final data = snapshot.docs.first.data();
        print(
            '📡 Stream update: ${data['activity']} (${(data['confidence'] * 100).toStringAsFixed(1)}%)');
      } else {
        print('📡 Stream: No data');
      }
    });

    print('\n✅ Stream active. Waiting for updates...');
    print('   (Run backend and predict to see updates)');

    // Keep alive for 30 seconds
    await Future.delayed(Duration(seconds: 30));
  } catch (e) {
    print('❌ Error: $e');
  }
}
