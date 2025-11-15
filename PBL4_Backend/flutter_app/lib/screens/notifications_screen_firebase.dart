import 'package:flutter/material.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';

class NotificationsScreenFirebase extends StatelessWidget {
  const NotificationsScreenFirebase({super.key});

  Stream<QuerySnapshot> _getNotificationsStream() {
    final userId = FirebaseAuth.instance.currentUser?.uid;
    if (userId == null) return const Stream.empty();

    return FirebaseFirestore.instance
        .collection('notifications')
        .where('user_id', isEqualTo: userId)
        .orderBy('created_at', descending: true)
        .snapshots();
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
      body: StreamBuilder(
        stream: _getNotificationsStream(),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }

          if (!snapshot.hasData || snapshot.data!.docs.isEmpty) {
            return const Center(
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
            );
          }

          final notifications = snapshot.data!.docs;

          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: notifications.length,
            itemBuilder: (context, index) {
              final doc = notifications[index];
              final data = doc.data() as Map<String, dynamic>;
              final title = data['title'] ?? 'Thông báo';
              final message = data['message'] ?? '';
              final isRead = data['is_read'] ?? false;
              final notificationType = data['notification_type'] ?? 'info';
              final createdAt = (data['created_at'] as Timestamp?)?.toDate();

              String timeAgo = 'Vừa xong';
              if (createdAt != null) {
                final diff = DateTime.now().difference(createdAt);
                if (diff.inDays > 0) {
                  timeAgo = '${diff.inDays} ngày trước';
                } else if (diff.inHours > 0) {
                  timeAgo = '${diff.inHours} giờ trước';
                } else if (diff.inMinutes > 0) {
                  timeAgo = '${diff.inMinutes} phút trước';
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
                      doc.reference.update({'is_read': true});
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
          );
        },
      ),
    );
  }
}
