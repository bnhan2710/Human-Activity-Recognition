import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import '../services/activity_service.dart';
import 'calo_screen_firebase.dart' as calo;
import 'history_screen_firebase_clean.dart' as history;
import 'notifications_screen_firebase.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen>
    with SingleTickerProviderStateMixin {
  String username = '';
  String _previousActivity = '';
  final ActivityService _activityService = ActivityService();
  Stream<Map<String, dynamic>>? _activityStream;
  late AnimationController _animationController;
  late Animation<double> _scaleAnimation;

  @override
  void initState() {
    super.initState();
    _loadUserProfile();
    _initializeActivityStream();

    // Setup animation
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 600),
      vsync: this,
    );

    _scaleAnimation = Tween<double>(begin: 0.8, end: 1.0).animate(
      CurvedAnimation(parent: _animationController, curve: Curves.elasticOut),
    );
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

  void _initializeActivityStream() {
    _activityStream = _activityService.listenCurrentActivity(userId: 'user1');
  }

  String _getActivityDisplayName(String activity) {
    switch (activity) {
      case 'WALKING':
        return '🚶 Đang đi bộ';
      case 'RUNNING':
        return '🏃 Đang chạy';
      case 'UPSTAIRS':
        return '⬆️ Lên cầu thang';
      case 'DOWNSTAIRS':
        return '⬇️ Xuống cầu thang';
      case 'SITTING':
        return '🪑 Đang ngồi';
      case 'STANDING':
        return '🧍 Đang đứng';
      case 'UNKNOWN':
        return '❓ Chưa xác định';
      default:
        return '⏳ Đang chờ...';
    }
  }

  IconData _getActivityIcon(String activity) {
    switch (activity) {
      case 'WALKING':
        return Icons.directions_walk;
      case 'RUNNING':
        return Icons.directions_run;
      case 'UPSTAIRS':
        return Icons.arrow_upward;
      case 'DOWNSTAIRS':
        return Icons.arrow_downward;
      case 'SITTING':
        return Icons.chair;
      case 'STANDING':
        return Icons.accessibility_new;
      default:
        return Icons.help_outline;
    }
  }

  Color _getActivityColor(String activity) {
    switch (activity) {
      case 'WALKING':
        return Colors.blue[400]!;
      case 'RUNNING':
        return Colors.red[400]!;
      case 'UPSTAIRS':
        return Colors.green[400]!;
      case 'DOWNSTAIRS':
        return Colors.orange[400]!;
      case 'SITTING':
        return Colors.purple[400]!;
      case 'STANDING':
        return Colors.teal[400]!;
      default:
        return Colors.grey[400]!;
    }
  }

  void _handleLogout() async {
    await FirebaseAuth.instance.signOut();
    if (mounted) {
      Navigator.pushReplacementNamed(context, '/login');
    }
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
                  // Welcome card
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
                              child: const Icon(Icons.waving_hand,
                                  color: Colors.amber, size: 28),
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
                                        fontWeight: FontWeight.w500),
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
                                color: Colors.white.withOpacity(0.2), width: 1),
                          ),
                          child: Row(
                            children: [
                              Icon(Icons.auto_awesome,
                                  color: Colors.amber[300], size: 20),
                              const SizedBox(width: 10),
                              const Expanded(
                                child: Text(
                                  'Sẵn sàng theo dõi hoạt động của bạn',
                                  style: TextStyle(
                                      fontSize: 15,
                                      color: Colors.white,
                                      fontWeight: FontWeight.w500),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 20),

                  // Grid cards
                  Expanded(
                    child: GridView.count(
                      padding: const EdgeInsets.only(top: 24),
                      physics: const NeverScrollableScrollPhysics(),
                      crossAxisCount: crossAxisCount,
                      crossAxisSpacing: 20,
                      mainAxisSpacing: 20,
                      children: [
                        // Realtime Activity Card
                        StreamBuilder<Map<String, dynamic>>(
                          stream: _activityStream,
                          builder: (context, snapshot) {
                            if (snapshot.hasData) {
                              final data = snapshot.data!;
                              final activity = data['activity'] as String;
                              final confidence =
                                  (data['confidence'] as num).toDouble();

                              return _buildActivityCard(
                                'Hoạt động hiện tại',
                                _getActivityDisplayName(activity),
                                _getActivityIcon(activity),
                                _getActivityColor(activity),
                                confidence,
                              );
                            } else if (snapshot.hasError) {
                              return _buildFeatureCard(
                                'Hoạt động hiện tại',
                                'Lỗi: ${snapshot.error}',
                                Icons.error_outline,
                                Colors.red[400]!,
                                null,
                              );
                            } else {
                              return _buildFeatureCard(
                                'Hoạt động hiện tại',
                                'Đang chờ dữ liệu...',
                                Icons.hourglass_empty,
                                Colors.grey[400]!,
                                null,
                              );
                            }
                          },
                        ),

                        _buildFeatureCard(
                          'Thống kê Calo',
                          'Xem thống kê calo tiêu hao',
                          Icons.local_fire_department,
                          Colors.orange[400]!,
                          () => Navigator.push(
                              context,
                              MaterialPageRoute(
                                  builder: (context) =>
                                      calo.CaloScreenFirebase())),
                        ),

                        _buildFeatureCard(
                          'Lịch sử hoạt động',
                          'Xem lại các hoạt động đã thực hiện',
                          Icons.history,
                          Colors.purple[400]!,
                          () => Navigator.push(
                              context,
                              MaterialPageRoute(
                                  builder: (context) =>
                                      history.HistoryScreen())),
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
                                      NotificationsScreenFirebase())),
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

  Widget _buildActivityCard(
    String title,
    String subtitle,
    IconData icon,
    Color color,
    double confidence,
  ) {
    return Card(
      elevation: 5,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [color.withOpacity(0.7), color],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(16),
          boxShadow: [
            BoxShadow(
                color: color.withOpacity(0.5),
                blurRadius: 15,
                offset: const Offset(0, 8)),
          ],
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            TweenAnimationBuilder<double>(
              tween: Tween(begin: 0.8, end: 1.0),
              duration: const Duration(milliseconds: 500),
              curve: Curves.easeOut,
              builder: (context, value, child) {
                return Transform.scale(
                  scale: value,
                  child: Icon(icon, size: 50, color: Colors.white),
                );
              },
            ),
            const SizedBox(height: 12),
            Text(
              title,
              textAlign: TextAlign.center,
              style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                  height: 1.2),
            ),
            const SizedBox(height: 8),
            Text(
              subtitle,
              textAlign: TextAlign.center,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: Colors.white),
            ),
            if (confidence > 0) ...[
              const SizedBox(height: 8),
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.3),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  '${(confidence * 100).toStringAsFixed(1)}%',
                  style: const TextStyle(
                      fontSize: 11,
                      color: Colors.white,
                      fontWeight: FontWeight.bold),
                ),
              ),
            ],
          ],
        ),
      ),
    );
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
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
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
                    height: 1.2),
              ),
              const SizedBox(height: 6),
              Text(
                subtitle,
                textAlign: TextAlign.center,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(fontSize: 12, color: Colors.white),
              ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }
}
