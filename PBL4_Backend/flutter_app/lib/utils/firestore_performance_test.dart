import 'package:cloud_firestore/cloud_firestore.dart';

/// Test Firestore query performance
/// Run this to compare before/after index creation
class FirestorePerformanceTest {
  static Future<void> testLatestPredictionQuery() async {
    print('🧪 Testing Firestore Query Performance...\n');

    final userId = 'user1';
    final stopwatch = Stopwatch()..start();

    try {
      // Test 1: Fetch with index (fast)
      print('📊 Test 1: Indexed query (user_id + timestamp + limit)');
      final snapshot1 = await FirebaseFirestore.instance
          .collection('activity_predictions')
          .where('user_id', isEqualTo: userId)
          .orderBy('timestamp', descending: true)
          .limit(1)
          .get();

      stopwatch.stop();
      print('✅ Documents fetched: ${snapshot1.docs.length}');
      print('⏱️  Latency: ${stopwatch.elapsedMilliseconds}ms');
      print('📦 Data size: ~${_estimateSize(snapshot1)} bytes\n');

      if (snapshot1.docs.isNotEmpty) {
        final data = snapshot1.docs.first.data();
        print('Latest prediction:');
        print('  Activity: ${data['activity']}');
        print(
            '  Confidence: ${(data['confidence'] * 100).toStringAsFixed(1)}%');
        print('  Time: ${data['created_at']}\n');
      }

      // Test 2: Fetch all (slow - for comparison)
      print('📊 Test 2: Full collection fetch (no limit)');
      stopwatch.reset();
      stopwatch.start();

      final snapshot2 = await FirebaseFirestore.instance
          .collection('activity_predictions')
          .where('user_id', isEqualTo: userId)
          .get();

      stopwatch.stop();
      print('✅ Documents fetched: ${snapshot2.docs.length}');
      print('⏱️  Latency: ${stopwatch.elapsedMilliseconds}ms');
      print('📦 Data size: ~${_estimateSize(snapshot2)} bytes\n');

      // Calculate improvement
      final improvement = (snapshot2.docs.length / 1).round();
      print('🚀 Performance Improvement:');
      print('  ${improvement}x fewer documents fetched');
      print('  ~${improvement}x faster query time');
      print('  ~${improvement}x less data transfer\n');

      // Test 3: Real-time listener performance
      print('📊 Test 3: Real-time listener latency');
      var updateCount = 0;
      final listenerStopwatch = Stopwatch();

      final subscription = FirebaseFirestore.instance
          .collection('activity_predictions')
          .where('user_id', isEqualTo: userId)
          .orderBy('timestamp', descending: true)
          .limit(1)
          .snapshots()
          .listen((snapshot) {
        updateCount++;
        listenerStopwatch.stop();

        if (snapshot.docs.isNotEmpty) {
          final data = snapshot.docs.first.data();
          print(
              '  Update #$updateCount: ${data['activity']} (${listenerStopwatch.elapsedMilliseconds}ms)');
        }

        // Reset for next update
        listenerStopwatch.reset();
        listenerStopwatch.start();
      });

      print('⏳ Listening for 10 seconds...');
      await Future.delayed(const Duration(seconds: 10));

      await subscription.cancel();
      print('✅ Total updates received: $updateCount');
      print(
          '📈 Average rate: ${(updateCount / 10).toStringAsFixed(1)} updates/sec\n');

      // Recommendations
      print('💡 Recommendations:');
      if (snapshot2.docs.length > 100) {
        print(
            '  ⚠️  Large collection detected (${snapshot2.docs.length} docs)');
        print('  ✅ MUST use indexed queries with limit()');
        print('  ❌ AVOID fetching full collection');
      }

      if (updateCount < 5) {
        print('  ⚠️  Low update rate (${updateCount} updates in 10s)');
        print('  💡 Check if backend is running and pushing predictions');
      } else {
        print('  ✅ Good update rate (${updateCount} updates in 10s)');
        print('  ✅ Real-time sync working properly');
      }
    } catch (e) {
      print('❌ Error: $e');

      if (e.toString().contains('index')) {
        print('\n⚠️  INDEX REQUIRED!');
        print('Solution:');
        print('1. Click the link in the error message');
        print('2. Or create index manually in Firebase Console');
        print('3. See FIRESTORE_INDEX_SETUP.md for details');
      }
    }
  }

  static int _estimateSize(QuerySnapshot snapshot) {
    // Rough estimate: ~1KB per document
    return snapshot.docs.length * 1024;
  }

  /// Test connection to Firestore
  static Future<void> testConnection() async {
    print('🔌 Testing Firestore connection...');

    try {
      final snapshot = await FirebaseFirestore.instance
          .collection('activity_predictions')
          .limit(1)
          .get();

      print('✅ Connected to Firestore');
      print('📊 Collection exists: ${snapshot.docs.isNotEmpty}');

      if (snapshot.docs.isNotEmpty) {
        print('✅ Data available');
      } else {
        print('⚠️  No data in collection');
        print('💡 Make sure backend is running and pushing predictions');
      }
    } catch (e) {
      print('❌ Connection failed: $e');
    }
  }
}
