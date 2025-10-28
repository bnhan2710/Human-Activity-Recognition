import 'package:flutter/material.dart';
import '../api/api_service.dart';
import 'dart:convert';
import 'history_screen.dart';
import 'notifications_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final ApiService api = ApiService();
  String username = '';
  bool isLoading = true;

  @override
  void initState() {
    super.initState();
    loadUserProfile();
  }

  void loadUserProfile() async {
    final token = await api.getToken();
    if (token != null) {
      try {
        final parts = token.split('.');
        if (parts.length == 3) {
          final payload = base64Url.normalize(parts[1]);
          final payloadString = utf8.decode(base64Url.decode(payload));
          final payloadMap = jsonDecode(payloadString);

          final usernameFromToken = payloadMap['username'] ?? payloadMap['sub'];
          if (usernameFromToken != null) {
            setState(() {
              username = usernameFromToken;
              isLoading = false;
            });
            return;
          }
        }
      } catch (e) {
        print('JWT decode error: $e');
      }
    }

    final profile = await api.getProfile();
    if (profile['username'] != null) {
      setState(() {
        username = profile['username'];
        isLoading = false;
      });
    } else {
      setState(() => isLoading = false);
    }
  }

  void handleLogout(BuildContext context) async {
    await api.logout();
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(const SnackBar(content: Text('Đã đăng xuất')));
    Navigator.pushReplacementNamed(context, '/login');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF5F7FB),
      appBar: AppBar(
        elevation: 4,
        backgroundColor: Colors.blueAccent,
        foregroundColor: Colors.white,
        title: const Text(
          'Human Activity Recognition',
          style: TextStyle(fontWeight: FontWeight.bold, letterSpacing: 0.5),
        ),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 12),
            child: ElevatedButton.icon(
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.white.withOpacity(0.15),
                elevation: 0,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              onPressed: () => handleLogout(context),
              icon: const Icon(Icons.logout, color: Colors.white),
              label: const Text(
                'Đăng xuất',
                style: TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ),
        ],
      ),
      body: isLoading
          ? const Center(child: CircularProgressIndicator())
          : LayoutBuilder(
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
                        // 🔹 Welcome section
                        Container(
                          width: double.infinity,
                          padding: const EdgeInsets.all(24),
                          decoration: BoxDecoration(
                            gradient: const LinearGradient(
                              colors: [Color(0xFF2196F3), Color(0xFF42A5F5)],
                              begin: Alignment.topLeft,
                              end: Alignment.bottomRight,
                            ),
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Xin chào, $username 👋',
                                style: const TextStyle(
                                  fontSize: 28,
                                  fontWeight: FontWeight.bold,
                                  color: Colors.white,
                                ),
                              ),
                              const SizedBox(height: 6),
                              const Text(
                                'Chào mừng đến với hệ thống nhận diện hoạt động con người',
                                style: TextStyle(
                                  fontSize: 16,
                                  color: Colors.white,
                                ),
                              ),
                            ],
                          ),
                        ),

                        // 🔹 Feature grid
                        Expanded(
                          child: GridView.count(
                            padding: const EdgeInsets.only(top: 24),
                            physics:
                                const NeverScrollableScrollPhysics(), // 🚫 Không cuộn
                            crossAxisCount: crossAxisCount,
                            crossAxisSpacing: 20,
                            mainAxisSpacing: 20,
                            childAspectRatio: 1.2,
                            children: [
                              _buildFeatureCard(
                                'Theo dõi hoạt động',
                                'Nhận diện hành động thời gian thực',
                                Icons.directions_run,
                                Colors.green[400]!,
                              ),
                              _buildFeatureCard(
                                'Thống kê calo',
                                'Tính toán lượng calo tiêu thụ',
                                Icons.local_fire_department,
                                Colors.orange[400]!,
                                () {
                                  Navigator.pushNamed(context, '/calo');
                                },
                              ),
                              _buildFeatureCard(
                                'Lịch sử hoạt động',
                                'Xem báo cáo chi tiết',
                                Icons.history,
                                Colors.purple[400]!,
                                () {
                                  print('Navigating to history screen...');
                                  Navigator.push(
                                    context,
                                    MaterialPageRoute(
                                      builder: (context) =>
                                          const HistoryScreen(),
                                    ),
                                  );
                                },
                              ),
                              _buildFeatureCard(
                                'Thông báo sức khỏe',
                                'Nhắc nhở chăm sóc sức khỏe',
                                Icons.notifications_active,
                                Colors.red[400]!,
                                () {
                                  Navigator.push(
                                    context,
                                    MaterialPageRoute(
                                      builder: (context) =>
                                          const NotificationsScreen(),
                                    ),
                                  );
                                },
                              ),
                            ],
                          ),
                        ),

                        // 🔹 System status
                        Container(
                          width: double.infinity,
                          padding: const EdgeInsets.all(24),
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(20),
                            boxShadow: [
                              BoxShadow(
                                color: Colors.black.withOpacity(0.05),
                                blurRadius: 8,
                                offset: const Offset(0, 4),
                              ),
                            ],
                          ),
                          child: Column(
                            children: const [
                              Icon(
                                Icons.sensors_rounded,
                                size: 60,
                                color: Colors.blueAccent,
                              ),
                              SizedBox(height: 12),
                              Text(
                                'Hệ thống sẵn sàng',
                                style: TextStyle(
                                  fontSize: 20,
                                  fontWeight: FontWeight.bold,
                                  color: Colors.blueAccent,
                                ),
                              ),
                              SizedBox(height: 6),
                              Text(
                                'Kết nối thiết bị cảm biến để bắt đầu theo dõi hoạt động',
                                textAlign: TextAlign.center,
                                style: TextStyle(color: Colors.grey),
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
    Color color, [
    VoidCallback? onTap,
  ]) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: () {
          if (onTap != null) {
            print('Card tapped: $title');
            onTap();
          }
        },
        borderRadius: BorderRadius.circular(16),
        child: Container(
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16),
            boxShadow: [
              BoxShadow(
                color: Colors.grey.withOpacity(0.1),
                spreadRadius: 1,
                blurRadius: 8,
                offset: const Offset(0, 3),
              ),
            ],
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, size: 40, color: color),
              const SizedBox(height: 10),
              Text(
                title,
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                subtitle,
                textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 13, color: Colors.grey),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
