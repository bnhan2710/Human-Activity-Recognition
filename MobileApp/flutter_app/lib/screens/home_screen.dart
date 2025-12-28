import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import '../services/imu_service_mock.dart';
import '../services/activity_monitor_service.dart';
import 'calo_screen_predictions.dart';
import 'history_screen_predictions.dart';
import 'notifications_screen_firebase.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  String username = '';
  String currentActivity = 'Đang chờ dữ liệu...';
  double confidence = 0.0;
  Map<String, double> probabilities = {};
  final ImuService _imuService = ImuService();
  final ActivityMonitorService _monitorService = ActivityMonitorService();

  @override
  void initState() {
    super.initState();
    _loadUserProfile();
    _initializeImuService();
    _listenToPredictions(); // Listen to real-time predictions
    _startActivityMonitoring(); // Start monitoring for sitting alerts
  }

  void _startActivityMonitoring() {
    // Set up callbacks
    _monitorService.onSittingAlert = (message, duration) {
      _showSittingAlert(message);
    };

    _monitorService.onActivityChange = (activity, confidence) {
      // Update UI immediately when activity changes
      if (mounted) {
        setState(() {
          currentActivity = _translateActivity(activity);
          this.confidence = confidence;
        });
        print('🔄 Activity changed: $activity → $currentActivity (${(confidence * 100).toStringAsFixed(1)}%)');
      }
    };

    // Start monitoring
    _monitorService.startMonitoring();
  }

  void _showSittingAlert(String message) {
    if (!mounted) return;

    // Show dialog
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.warning_amber_rounded, color: Colors.orange, size: 32),
            SizedBox(width: 12),
            Text('Cảnh báo sức khỏe!'),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              message,
              style: const TextStyle(fontSize: 16),
            ),
            const SizedBox(height: 16),
            const Text(
              '💡 Gợi ý:',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            const Text('• Đứng dậy và đi bộ vài phút'),
            const Text('• Vươn vai, xoay cổ'),
            const Text('• Uống nước'),
            const Text('• Nhìn xa để nghỉ mắt'),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Đã hiểu', style: TextStyle(fontSize: 16)),
          ),
        ],
      ),
    );

    // Also show snackbar
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Row(
            children: [
              const Icon(Icons.event_seat, color: Colors.white),
              const SizedBox(width: 12),
              Expanded(child: Text(message)),
            ],
          ),
          backgroundColor: Colors.orange,
          duration: const Duration(seconds: 5),
          action: SnackBarAction(
            label: 'Xem',
            textColor: Colors.white,
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) => const NotificationsScreenFirebase(),
                ),
              );
            },
          ),
        ),
      );
    }
  }

  void _listenToPredictions() {
    // Listen to predictions from Firestore (where backend saves predictions)
    // Use timestamp ordering with limit for fast real-time updates
    FirebaseFirestore.instance
        .collection('activity_predictions')
        .where('user_id', isEqualTo: 'user1')
        .orderBy('timestamp', descending: true) // Use server timestamp
        .limit(1) // Only get the latest prediction
        .snapshots()
        .listen(
          (snapshot) {
            if (snapshot.docs.isNotEmpty) {
              try {
                final prediction = snapshot.docs.first.data();

                setState(() {
                  currentActivity =
                      _translateActivity(prediction['activity'] ?? 'UNKNOWN');
                  confidence = (prediction['confidence'] ?? 0.0).toDouble();

                  // Parse probabilities
                  if (prediction['probabilities'] != null) {
                    final probs =
                        prediction['probabilities'] as Map<dynamic, dynamic>;
                    probabilities = probs.map((key, value) =>
                        MapEntry(key.toString(), (value as num).toDouble()));
                  }
                });

                print(
                    '✅ Received prediction: $currentActivity (${(confidence * 100).toStringAsFixed(1)}%)');
              } catch (e) {
                print('❌ Error parsing prediction: $e');
              }
            }
          },
          onError: (error) {
            print('❌ Prediction listen error: $error');
          },
        );
  }

  String _translateActivity(String activity) {
    const activityMap = {
      'WALKING': 'Đi bộ',
      'UPSTAIRS': 'Lên cầu thang',
      'DOWNSTAIRS': 'Xuống cầu thang',
      'SITTING': 'Ngồi',
      'STANDING': 'Đứng',
      'RUNNING': 'Chạy',
    };
    return activityMap[activity] ?? activity;
  }

  void _loadUserProfile() async {
    final user = FirebaseAuth.instance.currentUser;
    if (user != null) {
      final doc = await FirebaseFirestore.instance
          .collection('users')
          .doc(user.uid)
          .get();

      setState(() {
        username = doc.data()?['username'] ?? user.email ?? 'User';
      });
    }
  }

  void _initializeImuService() async {
    await _imuService.initialize();
    _imuService.startListening();

    _imuService.activityStream.listen((activity) {
      setState(() {
        currentActivity = activity;
      });
    });
  }

  void _handleLogout() async {
    await FirebaseAuth.instance.signOut();
    if (mounted) {
      Navigator.pushReplacementNamed(context, '/login');
    }
  }

    @override
  void dispose() {
    _monitorService.stopMonitoring(); // Stop monitoring when leaving screen
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF5F7FB),
      appBar: AppBar(
        elevation: 0,
        backgroundColor: const Color(0xFF2196F3),
        flexibleSpace: Container(
          decoration: const BoxDecoration(
            gradient: LinearGradient(
              colors: [Color(0xFF1976D2), Color(0xFF2196F3), Color(0xFF42A5F5)],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
          ),
        ),
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.2),
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Icon(Icons.sensors, size: 24, color: Colors.white),
            ),
            const SizedBox(width: 12),
            const Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  'HAR System',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                    letterSpacing: 0.5,
                  ),
                ),
                Text(
                  'Activity Recognition',
                  style: TextStyle(
                    fontSize: 11,
                    color: Colors.white70,
                    fontWeight: FontWeight.w400,
                  ),
                ),
              ],
            ),
          ],
        ),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 8),
            child: IconButton(
              onPressed: _handleLogout,
              icon: Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Icon(Icons.logout_rounded,
                    color: Colors.white, size: 20),
              ),
              tooltip: 'Đăng xuất',
            ),
          ),
        ],
      ),
      body: LayoutBuilder(
        builder: (context, constraints) {
          final isDesktop = constraints.maxWidth > 1000;
          final crossAxisCount = isDesktop ? 4 : 2;

          return Center(
            child: Container(
              constraints: const BoxConstraints(maxWidth: 1200),
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: [
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(24),
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                        colors: [Color(0xFF667eea), Color(0xFF764ba2)],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                      borderRadius: BorderRadius.circular(20),
                      boxShadow: [
                        BoxShadow(
                          color: const Color(0xFF667eea).withOpacity(0.3),
                          blurRadius: 20,
                          offset: const Offset(0, 10),
                        ),
                      ],
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.all(12),
                              decoration: BoxDecoration(
                                color: Colors.white.withOpacity(0.2),
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: const Icon(
                                Icons.waving_hand,
                                color: Colors.amber,
                                size: 28,
                              ),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Text(
                                    'Xin chào',
                                    style: TextStyle(
                                      fontSize: 14,
                                      color: Colors.white70,
                                      fontWeight: FontWeight.w500,
                                    ),
                                  ),
                                  Text(
                                    username,
                                    style: const TextStyle(
                                      fontSize: 24,
                                      fontWeight: FontWeight.bold,
                                      color: Colors.white,
                                      letterSpacing: 0.5,
                                    ),
                                    maxLines: 1,
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 16),
                        Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 16, vertical: 10),
                          decoration: BoxDecoration(
                            color: Colors.white.withOpacity(0.15),
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(
                              color: Colors.white.withOpacity(0.2),
                              width: 1,
                            ),
                          ),
                          child: Row(
                            children: [
                              Icon(
                                Icons.auto_awesome,
                                color: Colors.amber[300],
                                size: 20,
                              ),
                              const SizedBox(width: 10),
                              const Expanded(
                                child: Text(
                                  'Sẵn sàng theo dõi hoạt động của bạn',
                                  style: TextStyle(
                                    fontSize: 15,
                                    color: Colors.white,
                                    fontWeight: FontWeight.w500,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 20),
                  Expanded(
                    child: GridView.count(
                      padding: const EdgeInsets.only(top: 24),
                      physics: const NeverScrollableScrollPhysics(),
                      crossAxisCount: crossAxisCount,
                      crossAxisSpacing: 20,
                      mainAxisSpacing: 20,
                      children: [
                        _buildActivityCard(),
                        _buildFeatureCard(
                          'Thống kê Calo',
                          'Xem thống kê calo tiêu hao',
                          Icons.local_fire_department,
                          Colors.orange[400]!,
                          () => Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (context) => const CaloScreenPredictions(),
                            ),
                          ),
                        ),
                        _buildFeatureCard(
                          'Lịch sử hoạt động',
                          'Xem lại các hoạt động đã thực hiện',
                          Icons.history,
                          Colors.purple[400]!,
                          () => Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (context) => const HistoryScreenPredictions(),
                            ),
                          ),
                        ),
                        _buildFeatureCard(
                          'Thông báo',
                          'Xem thông báo và nhắc nhở',
                          Icons.notifications_active,
                          Colors.red[400]!,
                          () => Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (context) =>
                                  NotificationsScreenFirebase(),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildActivityCard() {
    return Card(
      elevation: 3,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
      child: Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [Colors.green[400]!.withOpacity(0.7), Colors.green[400]!],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(16),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            // Icon hoạt động
            Icon(
              _getActivityIcon(currentActivity),
              size: 40,
              color: Colors.white,
            ),
            const SizedBox(height: 10),

            // Tiêu đề
            const Text(
              'Hoạt động hiện tại',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w600,
                color: Colors.white70,
                height: 1.2,
              ),
            ),
            const SizedBox(height: 8),

            // Tên hoạt động
            Text(
              currentActivity,
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: Colors.white,
                height: 1.2,
              ),
            ),

            // Confidence indicator
            if (confidence > 0) ...[
              const SizedBox(height: 12),
              Column(
                children: [
                  // Confidence bar
                  ClipRRect(
                    borderRadius: BorderRadius.circular(10),
                    child: LinearProgressIndicator(
                      value: confidence,
                      minHeight: 8,
                      backgroundColor: Colors.white.withOpacity(0.3),
                      valueColor: AlwaysStoppedAnimation<Color>(
                        confidence > 0.8
                            ? Colors.white
                            : confidence > 0.5
                                ? Colors.amber
                                : Colors.orange,
                      ),
                    ),
                  ),
                  const SizedBox(height: 6),
                  // Confidence text
                  Text(
                    '${(confidence * 100).toStringAsFixed(1)}% tin cậy',
                    style: const TextStyle(
                      fontSize: 11,
                      color: Colors.white70,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }

  IconData _getActivityIcon(String activity) {
    switch (activity) {
      case 'Đi bộ':
        return Icons.directions_walk;
      case 'Chạy':
        return Icons.directions_run;
      case 'Lên cầu thang':
        return Icons.stairs;
      case 'Xuống cầu thang':
        return Icons.arrow_downward;
      case 'Ngồi':
        return Icons.chair;
      case 'Đứng':
        return Icons.accessibility_new;
      default:
        return Icons.help_outline;
    }
  }

  Widget _buildFeatureCard(
    String title,
    String subtitle,
    IconData icon,
    Color color,
    VoidCallback? onTap,
  ) {
    return Card(
      elevation: 3,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [color.withOpacity(0.7), color],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            borderRadius: BorderRadius.circular(16),
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, size: 40, color: Colors.white),
              const SizedBox(height: 10),
              Text(
                title,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                  height: 1.2,
                ),
              ),
              const SizedBox(height: 6),
              Text(
                subtitle,
                textAlign: TextAlign.center,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  fontSize: 12,
                  color: Colors.white,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
