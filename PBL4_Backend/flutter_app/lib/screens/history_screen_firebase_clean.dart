import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:intl/intl.dart';
import 'package:intl/date_symbol_data_local.dart';

class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  DateTime _selectedDate = DateTime.now();
  final userId = FirebaseAuth.instance.currentUser?.uid;
  bool _isLocaleInitialized = false;

  @override
  void initState() {
    super.initState();
    _initializeLocale();
    _debugInfo();
  }

  Future<void> _initializeLocale() async {
    await initializeDateFormatting('vi_VN', null);
    setState(() => _isLocaleInitialized = true);
  }

  void _debugInfo() {
    print('\n🔍 ============ DEBUG HISTORY SCREEN ============');
    print('📱 User ID: $userId');
    print(
        '📅 Selected Date: ${_selectedDate.day}/${_selectedDate.month}/${_selectedDate.year}');

    if (userId == null) {
      print('❌ ERROR: User not logged in!');
      return;
    }

    FirebaseFirestore.instance
        .collection('activities')
        .where('user_id', isEqualTo: userId)
        .get()
        .then((snapshot) {
      print('\n📊 TOTAL ACTIVITIES: ${snapshot.docs.length}');

      if (snapshot.docs.isEmpty) {
        print('⚠️ NO DATA FOUND! Please seed data first.');
        return;
      }

      var firstDoc = snapshot.docs.first.data();
      print('\n📝 Sample Activity:');
      print('   action: ${firstDoc['action']}');
      print('   user_id: ${firstDoc['user_id']}');
      print('   start_time: ${firstDoc['start_time']}');
      print('   calories: ${firstDoc['calories_burned']}');

      DateTime startOfDay =
          DateTime(_selectedDate.year, _selectedDate.month, _selectedDate.day);
      DateTime endOfDay = startOfDay.add(const Duration(days: 1));

      var activitiesForDate = snapshot.docs.where((doc) {
        var data = doc.data();
        var startTime = (data['start_time'] as Timestamp?)?.toDate();
        return startTime != null &&
            startTime.isAfter(startOfDay) &&
            startTime.isBefore(endOfDay);
      }).toList();

      print(
          '\n📅 Activities for ${_selectedDate.day}/${_selectedDate.month}/${_selectedDate.year}: ${activitiesForDate.length}');
      print('============================================\n');
    });
  }

  Stream<List<DocumentSnapshot>> _getActivitiesStream() {
    if (userId == null) {
      print('⚠️ Stream: User ID is null');
      return Stream.value([]);
    }

    print(
        '🔄 Creating stream - Query ALL activities for user (filter on client)');

    DateTime startOfDay =
        DateTime(_selectedDate.year, _selectedDate.month, _selectedDate.day);
    DateTime endOfDay = startOfDay.add(const Duration(days: 1));

    return FirebaseFirestore.instance
        .collection('activities')
        .where('user_id', isEqualTo: userId)
        .snapshots()
        .map((snapshot) {
      var filtered = snapshot.docs.where((doc) {
        var data = doc.data();
        var startTime = (data['start_time'] as Timestamp?)?.toDate();
        return startTime != null &&
            startTime.isAfter(startOfDay) &&
            startTime.isBefore(endOfDay);
      }).toList();

      filtered.sort((a, b) {
        var aTime = (a.data()['start_time'] as Timestamp?)?.toDate();
        var bTime = (b.data()['start_time'] as Timestamp?)?.toDate();
        if (aTime == null || bTime == null) return 0;
        return aTime.compareTo(bTime);
      });

      print(
          '📊 Filtered ${filtered.length} activities for ${_selectedDate.day}/${_selectedDate.month}/${_selectedDate.year}');
      return filtered;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (!_isLocaleInitialized) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    return Scaffold(
      backgroundColor: const Color(0xFFF5F7FB),
      appBar: AppBar(
        elevation: 2,
        backgroundColor: Colors.purple,
        foregroundColor: Colors.white,
        title: const Text('Lịch sử hoạt động',
            style: TextStyle(fontWeight: FontWeight.bold)),
      ),
      body: Column(
        children: [
          _buildDateSelector(),
          Expanded(
            child: StreamBuilder<List<DocumentSnapshot>>(
              stream: _getActivitiesStream(),
              builder: (context, snapshot) {
                print('\n🔄 ============ STREAM BUILDER ============');
                print('📡 Connection State: ${snapshot.connectionState}');
                print('📡 Has Data: ${snapshot.hasData}');
                print('📡 Has Error: ${snapshot.hasError}');
                if (snapshot.hasError) {
                  print('❌ Error: ${snapshot.error}');
                }
                if (snapshot.hasData) {
                  print('📊 Documents count: ${snapshot.data!.length}');
                }
                print('==========================================\n');

                if (snapshot.connectionState == ConnectionState.waiting) {
                  return const Center(child: CircularProgressIndicator());
                }

                if (snapshot.hasError) {
                  return Center(
                    child: Padding(
                      padding: const EdgeInsets.all(20),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(Icons.error, size: 60, color: Colors.red),
                          const SizedBox(height: 16),
                          Text(
                            'Lỗi: ${snapshot.error}',
                            textAlign: TextAlign.center,
                            style: const TextStyle(color: Colors.red),
                          ),
                        ],
                      ),
                    ),
                  );
                }

                if (!snapshot.hasData || snapshot.data!.isEmpty) {
                  return Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Icons.inbox, size: 80, color: Colors.grey),
                        const SizedBox(height: 16),
                        const Text(
                          'Không có hoạt động nào',
                          style: TextStyle(fontSize: 18, color: Colors.grey),
                        ),
                      ],
                    ),
                  );
                }

                final activities = snapshot.data!;
                print('✅ Rendering ${activities.length} activities');

                return ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: activities.length,
                  itemBuilder: (context, index) {
                    final doc = activities[index];
                    final data = doc.data() as Map<String, dynamic>;
                    return _buildActivityCard(data);
                  },
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDateSelector() {
    return Card(
      margin: const EdgeInsets.all(16),
      elevation: 2,
      child: ListTile(
        leading: const Icon(Icons.calendar_today, color: Colors.purple),
        title: Text(
          DateFormat('EEEE, dd/MM/yyyy', 'vi_VN').format(_selectedDate),
          style: const TextStyle(fontWeight: FontWeight.bold),
        ),
        trailing: const Icon(Icons.arrow_drop_down),
        onTap: () async {
          final date = await showDatePicker(
            context: context,
            initialDate: _selectedDate,
            firstDate: DateTime(2020),
            lastDate: DateTime.now().add(const Duration(days: 365)),
          );
          if (date != null) {
            setState(() => _selectedDate = date);
            _debugInfo();
          }
        },
      ),
    );
  }

  Widget _buildActivityCard(Map<String, dynamic> data) {
    final action = data['action'] ?? 'Không xác định';
    final startTime = (data['start_time'] as Timestamp?)?.toDate();
    final endTime = (data['end_time'] as Timestamp?)?.toDate();
    final duration = (data['duration'] ?? 0).toDouble();
    final calories = (data['calories_burned'] ?? 0).toDouble();

    final startTimeStr = startTime != null
        ? DateFormat('HH:mm', 'vi_VN').format(startTime)
        : '--:--';
    final endTimeStr = endTime != null
        ? DateFormat('HH:mm', 'vi_VN').format(endTime)
        : '--:--';
    final durationMinutes = (duration / 60).round();

    IconData icon;
    Color color;
    switch (action) {
      case 'Chạy':
        icon = Icons.directions_run;
        color = Colors.red[400]!;
        break;
      case 'Đi bộ':
        icon = Icons.directions_walk;
        color = Colors.green[400]!;
        break;
      case 'Leo cầu thang':
        icon = Icons.stairs;
        color = Colors.purple[400]!;
        break;
      case 'Đứng':
        icon = Icons.accessibility_new;
        color = Colors.blue[400]!;
        break;
      case 'Ngồi':
        icon = Icons.event_seat;
        color = Colors.grey[400]!;
        break;
      default:
        icon = Icons.help_outline;
        color = Colors.grey[400]!;
    }

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: ListTile(
        contentPadding: const EdgeInsets.all(16),
        leading: Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: color.withOpacity(0.2),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Icon(icon, color: color, size: 28),
        ),
        title: Text(
          action,
          style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 8),
            Row(
              children: [
                const Icon(Icons.access_time, size: 16, color: Colors.grey),
                const SizedBox(width: 4),
                Text('$startTimeStr - $endTimeStr ($durationMinutes phút)'),
              ],
            ),
            const SizedBox(height: 4),
            Row(
              children: [
                const Icon(Icons.local_fire_department,
                    size: 16, color: Colors.orange),
                const SizedBox(width: 4),
                Text(
                  '${calories.toStringAsFixed(0)} kcal',
                  style: const TextStyle(fontWeight: FontWeight.bold),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
