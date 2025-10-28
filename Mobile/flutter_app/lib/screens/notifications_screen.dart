import 'package:flutter/material.dart';
import '../api/api_service.dart';

class NotificationsScreen extends StatefulWidget {
  const NotificationsScreen({super.key});

  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen> {
  final ApiService api = ApiService();
  bool isLoading = true;
  List<dynamic> notifications = [];

  @override
  void initState() {
    super.initState();
    loadNotifications();
  }

  void loadNotifications() async {
    setState(() => isLoading = true);

    final result = await api.getNotifications();

    if (result['error'] == null) {
      setState(() {
        notifications = result['notifications'] ?? [];
        isLoading = false;
      });
    } else {
      setState(() => isLoading = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(result['error'] ?? 'Lỗi không xác định')),
      );
    }
  }

  void markAsRead(int notificationId, int index) async {
    final result = await api.markNotificationAsRead(notificationId);

    if (result['error'] == null) {
      setState(() {
        notifications[index]['is_read'] = true;
      });
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(result['error'] ?? 'Lỗi không xác định')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF5F7FB),
      appBar: AppBar(
        elevation: 2,
        backgroundColor: Colors.red,
        foregroundColor: Colors.white,
        title: const Text(
          'Thông báo sức khỏe',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
      ),
      body: isLoading
          ? const Center(child: CircularProgressIndicator())
          : notifications.isEmpty
          ? const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.notifications_off, size: 80, color: Colors.grey),
                  SizedBox(height: 16),
                  Text(
                    'Chưa có thông báo nào',
                    style: TextStyle(fontSize: 18, color: Colors.grey),
                  ),
                ],
              ),
            )
          : ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: notifications.length,
              itemBuilder: (context, index) {
                final notification = notifications[index];
                final id = notification['id'];
                final title = notification['title'] ?? 'Thông báo';
                final message = notification['message'] ?? '';
                final isRead = notification['is_read'] ?? false;
                final createdAt = notification['created_at'] ?? '';

                // Parse datetime
                String timeAgo = 'Vừa xong';
                if (createdAt.isNotEmpty) {
                  try {
                    final dateTime = DateTime.parse(createdAt);
                    final diff = DateTime.now().difference(dateTime);
                    if (diff.inDays > 0) {
                      timeAgo = '${diff.inDays} ngày trước';
                    } else if (diff.inHours > 0) {
                      timeAgo = '${diff.inHours} giờ trước';
                    } else if (diff.inMinutes > 0) {
                      timeAgo = '${diff.inMinutes} phút trước';
                    }
                  } catch (e) {
                    // ignore
                  }
                }

                return Card(
                  margin: const EdgeInsets.only(bottom: 12),
                  elevation: 2,
                  color: isRead ? Colors.white : Colors.blue.shade50,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: InkWell(
                    onTap: () {
                      if (!isRead) {
                        markAsRead(id, index);
                      }
                    },
                    borderRadius: BorderRadius.circular(12),
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Container(
                            width: 50,
                            height: 50,
                            decoration: BoxDecoration(
                              color: isRead
                                  ? Colors.grey.shade200
                                  : Colors.red.shade100,
                              borderRadius: BorderRadius.circular(25),
                            ),
                            child: Icon(
                              Icons.notifications_active,
                              color: isRead ? Colors.grey : Colors.red,
                              size: 28,
                            ),
                          ),
                          const SizedBox(width: 16),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  children: [
                                    Expanded(
                                      child: Text(
                                        title,
                                        style: TextStyle(
                                          fontSize: 16,
                                          fontWeight: isRead
                                              ? FontWeight.normal
                                              : FontWeight.bold,
                                        ),
                                      ),
                                    ),
                                    if (!isRead)
                                      Container(
                                        width: 10,
                                        height: 10,
                                        decoration: const BoxDecoration(
                                          color: Colors.red,
                                          shape: BoxShape.circle,
                                        ),
                                      ),
                                  ],
                                ),
                                const SizedBox(height: 8),
                                Text(
                                  message,
                                  style: TextStyle(
                                    fontSize: 14,
                                    color: Colors.grey[700],
                                  ),
                                ),
                                const SizedBox(height: 8),
                                Text(
                                  timeAgo,
                                  style: const TextStyle(
                                    fontSize: 12,
                                    color: Colors.grey,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                );
              },
            ),
    );
  }
}
