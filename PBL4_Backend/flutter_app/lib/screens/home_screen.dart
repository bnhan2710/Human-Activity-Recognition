import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import '../services/imu_service_mock.dart';
import 'calo_screen_firebase.dart' as calo;
import 'history_screen_firebase_clean.dart' as history;
import 'notifications_screen_firebase.dart';
import 'settings_screen_new.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  String username = '';
  String currentActivity = 'Đang chờ dữ liệu...';
  final ImuService _imuService = ImuService();

  @override
  void initState() {
    super.initState();
    _loadUserProfile();
    _initializeImuService();
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
                        _buildFeatureCard(
                          'Hoạt động hiện tại',
                          currentActivity,
                          Icons.directions_run,
                          Colors.green[400]!,
                          null,
                        ),
                        _buildFeatureCard(
                          'Thống kê Calo',
                          'Xem thống kê calo tiêu hao',
                          Icons.local_fire_department,
                          Colors.orange[400]!,
                          () => Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (context) => calo.CaloScreenFirebase(),
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
                              builder: (context) => history.HistoryScreen(),
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
                        _buildFeatureCard(
                          'Quản lý dữ liệu',
                          'Tạo dữ liệu mẫu để test',
                          Icons.settings,
                          Colors.teal[400]!,
                          () {
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                content: Text('Chức năng đang được phát triển'),
                              ),
                            );
                          },
                        ),
                        _buildFeatureCard(
                          'Force Seed',
                          'Tạo lại dữ liệu mẫu',
                          Icons.refresh,
                          Colors.indigo[400]!,
                          () => _showSeedDialog(),
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

  void _showSeedDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('🌱 Force Seed Data'),
        content: const Text(
          'Bạn có muốn tạo lại dữ liệu mẫu?\n\n'
          'Lưu ý: Điều này sẽ thêm thêm dữ liệu mới, không xóa dữ liệu cũ.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Hủy'),
          ),
          TextButton(
            onPressed: () async {
              Navigator.pop(context);
              if (!mounted) return;

              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('🌱 Chức năng đang được phát triển'),
                  duration: Duration(seconds: 2),
                ),
              );

              // TODO: Implement seed function
              // await SeedService.forceSeed(days: 7);
            },
            child: const Text('Tạo'),
          ),
          TextButton(
            onPressed: () async {
              Navigator.pop(context);
              final confirm = await showDialog<bool>(
                context: context,
                builder: (context) => AlertDialog(
                  title: const Text('⚠️ Xác nhận xóa'),
                  content: const Text(
                    'Bạn có chắc muốn xóa TOÀN BỘ dữ liệu và tạo lại?',
                  ),
                  actions: [
                    TextButton(
                      onPressed: () => Navigator.pop(context, false),
                      child: const Text('Hủy'),
                    ),
                    TextButton(
                      onPressed: () => Navigator.pop(context, true),
                      style: TextButton.styleFrom(foregroundColor: Colors.red),
                      child: const Text('Xóa & Tạo lại'),
                    ),
                  ],
                ),
              );

              if (confirm == true) {
                if (!mounted) return;

                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('🗑️ Chức năng đang được phát triển'),
                    duration: Duration(seconds: 2),
                  ),
                );

                // TODO: Implement clear and seed function
                // await SeedService.clearAllAndReset();
                // await SeedService.forceSeed(days: 7);
              }
            },
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text('Xóa & Tạo lại'),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _imuService.dispose();
    super.dispose();
  }
}
