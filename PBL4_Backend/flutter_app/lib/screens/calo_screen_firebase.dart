import 'package:flutter/material.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:intl/intl.dart';
import 'package:intl/date_symbol_data_local.dart';
import '../services/firestore_service.dart';

class CaloScreenFirebase extends StatefulWidget {
  const CaloScreenFirebase({super.key});

  @override
  State<CaloScreenFirebase> createState() => _CaloScreenFirebaseState();
}

class _CaloScreenFirebaseState extends State<CaloScreenFirebase> {
  DateTime selectedDate = DateTime.now();
  final userId = FirebaseAuth.instance.currentUser?.uid;
  bool _isLocaleInitialized = false;

  @override
  void initState() {
    super.initState();
    _initializeLocale();
    _debugInfo();
  }

  void _debugInfo() {
    print('🔍 DEBUG - Calo Screen:');
    print('  User ID: $userId');
    print('  Selected Date: $selectedDate');

    if (userId != null) {
      FirebaseFirestore.instance
          .collection('activities')
          .where('user_id', isEqualTo: userId)
          .limit(5)
          .get()
          .then((snapshot) {
        print('  📊 Found ${snapshot.docs.length} activities');
        if (snapshot.docs.isNotEmpty) {
          print('  Sample: ${snapshot.docs.first.data()}');
        }
      }).catchError((error) {
        print('  ❌ Error: $error');
      });
    }
  }

  Future<void> _initializeLocale() async {
    await initializeDateFormatting('vi_VN', null);
    if (mounted) {
      setState(() {
        _isLocaleInitialized = true;
      });
    }
  }

  void selectDate() async {
    final pickedDate = await showDatePicker(
      context: context,
      initialDate: selectedDate,
      firstDate: DateTime(2020),
      lastDate: DateTime.now(),
    );

    if (pickedDate != null && pickedDate != selectedDate) {
      setState(() => selectedDate = pickedDate);
    }
  }

  Stream<QuerySnapshot> _getActivitiesStream() {
    if (userId == null) return const Stream.empty();

    DateTime startOfDay = DateTime(
      selectedDate.year,
      selectedDate.month,
      selectedDate.day,
    );
    DateTime endOfDay = startOfDay.add(const Duration(days: 1));

    return FirebaseFirestore.instance
        .collection('activities')
        .where('user_id', isEqualTo: userId)
        .where('start_time',
            isGreaterThanOrEqualTo: Timestamp.fromDate(startOfDay))
        .where('start_time', isLessThan: Timestamp.fromDate(endOfDay))
        .snapshots();
  }

  Map<String, dynamic> _calculateStats(List<DocumentSnapshot> docs) {
    double totalCalories = 0;
    Map<String, int> activityCount = {};
    Map<String, double> activityCalories = {};
    Map<String, int> activityDuration = {};

    for (var doc in docs) {
      var data = doc.data() as Map<String, dynamic>;

      // Map fields từ database
      String activity = data['action'] ?? 'Không xác định';
      double calories = (data['calories_burned'] ?? 0).toDouble();
      double durationSeconds = (data['duration'] ?? 0).toDouble();
      int durationMinutes = (durationSeconds / 60).round();

      totalCalories += calories;
      activityCount[activity] = (activityCount[activity] ?? 0) + 1;
      activityCalories[activity] = (activityCalories[activity] ?? 0) + calories;
      activityDuration[activity] =
          (activityDuration[activity] ?? 0) + durationMinutes;
    }

    return {
      'totalCalories': totalCalories,
      'activityCount': activityCount,
      'activityCalories': activityCalories,
      'activityDuration': activityDuration,
    };
  }

  @override
  Widget build(BuildContext context) {
    if (!_isLocaleInitialized) {
      return Scaffold(
        backgroundColor: Colors.grey[50],
        appBar: AppBar(
          title: const Text('Thống kê Calo'),
          backgroundColor: Colors.orange,
          foregroundColor: Colors.white,
          elevation: 0,
        ),
        body: const Center(
          child: CircularProgressIndicator(),
        ),
      );
    }

    return Scaffold(
      backgroundColor: const Color(0xFFF5F7FB),
      appBar: AppBar(
        elevation: 2,
        backgroundColor: Colors.orangeAccent,
        foregroundColor: Colors.white,
        title: const Text(
          'Thống kê Calo',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
      ),
      body: StreamBuilder(
        stream: _getActivitiesStream(),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }

          if (!snapshot.hasData || snapshot.data!.docs.isEmpty) {
            return _buildEmptyState();
          }

          final activities = snapshot.data!.docs;
          final stats = _calculateStats(activities);

          return SingleChildScrollView(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _buildDatePicker(),
                const SizedBox(height: 24),
                _buildTotalCaloriesCard(stats['totalCalories']),
                const SizedBox(height: 24),
                const Text(
                  'Chi tiết theo hoạt động',
                  style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                    color: Colors.black87,
                  ),
                ),
                const SizedBox(height: 16),
                ...stats['activityCalories'].entries.map(
                      (entry) => _buildActivityCard(
                        entry.key,
                        entry.value,
                        stats['activityDuration'][entry.key],
                        stats['activityCount'][entry.key],
                      ),
                    ),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildDatePicker() {
    final weekday = DateFormat('EEEE', 'vi_VN').format(selectedDate);
    final dateStr = DateFormat('dd/MM/yyyy').format(selectedDate);

    return Card(
      elevation: 4,
      shadowColor: Colors.orangeAccent.withOpacity(0.3),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      child: Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [Colors.orange.shade50, Colors.white],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(20),
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.orangeAccent,
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Icon(
                Icons.calendar_today,
                color: Colors.white,
                size: 24,
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    dateStr,
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 18,
                      color: Colors.black87,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    weekday,
                    style: TextStyle(
                      fontSize: 14,
                      color: Colors.grey[600],
                    ),
                  ),
                ],
              ),
            ),
            ElevatedButton.icon(
              onPressed: selectDate,
              icon: const Icon(Icons.edit_calendar, size: 18),
              label: const Text('Chọn'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.orangeAccent,
                foregroundColor: Colors.white,
                elevation: 0,
                padding:
                    const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTotalCaloriesCard(double totalCalories) {
    // Tính phần trăm so với mục tiêu (giả sử mục tiêu là 2000 kcal)
    const goalCalories = 2000.0;
    final percentage = (totalCalories / goalCalories * 100).clamp(0, 100);

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(28),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [
            Color(0xFFFF6F00),
            Color(0xFFFF8F00),
            Color(0xFFFFA726),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(24),
        boxShadow: [
          BoxShadow(
            color: Colors.orange.withOpacity(0.4),
            blurRadius: 20,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Icon(
                  Icons.local_fire_department,
                  size: 40,
                  color: Colors.white,
                ),
              ),
              const SizedBox(width: 12),
              const Text(
                'Tổng Calo Đã Đốt',
                style: TextStyle(
                  fontSize: 20,
                  color: Colors.white,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),
          Text(
            '${totalCalories.toStringAsFixed(0)}',
            style: const TextStyle(
              fontSize: 56,
              fontWeight: FontWeight.bold,
              color: Colors.white,
              height: 1,
            ),
          ),
          const Text(
            'kcal',
            style: TextStyle(
              fontSize: 24,
              color: Colors.white70,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 20),
          // Progress bar
          Container(
            height: 8,
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.3),
              borderRadius: BorderRadius.circular(4),
            ),
            child: FractionallySizedBox(
              alignment: Alignment.centerLeft,
              widthFactor: percentage / 100,
              child: Container(
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(4),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.white.withOpacity(0.5),
                      blurRadius: 8,
                    ),
                  ],
                ),
              ),
            ),
          ),
          const SizedBox(height: 12),
          Text(
            '${percentage.toStringAsFixed(0)}% của mục tiêu ${goalCalories.toStringAsFixed(0)} kcal',
            style: const TextStyle(
              fontSize: 14,
              color: Colors.white70,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildActivityCard(
    String activityName,
    double calories,
    int duration,
    int count,
  ) {
    final durationMinutes = (duration / 60).ceil();
    final color = _getActivityColor(activityName);

    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      elevation: 3,
      shadowColor: color.withOpacity(0.3),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      child: Container(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(20),
          gradient: LinearGradient(
            colors: [Colors.white, color.withOpacity(0.05)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            children: [
              Row(
                children: [
                  Container(
                    width: 60,
                    height: 60,
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: [color, color.withOpacity(0.7)],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                      borderRadius: BorderRadius.circular(16),
                      boxShadow: [
                        BoxShadow(
                          color: color.withOpacity(0.3),
                          blurRadius: 8,
                          offset: const Offset(0, 4),
                        ),
                      ],
                    ),
                    child: Icon(
                      _getActivityIcon(activityName),
                      color: Colors.white,
                      size: 32,
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          activityName,
                          style: const TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                            color: Colors.black87,
                          ),
                        ),
                        const SizedBox(height: 6),
                        Row(
                          children: [
                            Icon(Icons.repeat,
                                size: 16, color: Colors.grey[600]),
                            const SizedBox(width: 4),
                            Text(
                              '$count lần',
                              style: TextStyle(
                                  fontSize: 14, color: Colors.grey[600]),
                            ),
                            const SizedBox(width: 16),
                            Icon(Icons.access_time,
                                size: 16, color: Colors.grey[600]),
                            const SizedBox(width: 4),
                            Text(
                              '$durationMinutes phút',
                              style: TextStyle(
                                  fontSize: 14, color: Colors.grey[600]),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              Container(
                padding:
                    const EdgeInsets.symmetric(vertical: 12, horizontal: 20),
                decoration: BoxDecoration(
                  color: color.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: color.withOpacity(0.3), width: 1),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(
                      Icons.local_fire_department,
                      color: color,
                      size: 24,
                    ),
                    const SizedBox(width: 8),
                    Text(
                      '${calories.toStringAsFixed(1)} kcal',
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        color: color,
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
  }

  Widget _buildEmptyState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            _buildDatePicker(),
            const SizedBox(height: 60),
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: Colors.grey.shade100,
                shape: BoxShape.circle,
              ),
              child: Icon(
                Icons.fitness_center,
                size: 80,
                color: Colors.grey.shade400,
              ),
            ),
            const SizedBox(height: 24),
            const Text(
              'Chưa có hoạt động nào',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: Colors.black87,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Hãy bắt đầu vận động để ghi nhận\nhoạt động của bạn',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 16,
                color: Colors.grey[600],
                height: 1.5,
              ),
            ),
          ],
        ),
      ),
    );
  }

  IconData _getActivityIcon(String activityName) {
    switch (activityName) {
      case 'Chạy':
        return Icons.directions_run;
      case 'Đi bộ':
        return Icons.directions_walk;
      case 'Leo cầu thang':
        return Icons.stairs;
      case 'Đứng':
        return Icons.accessibility_new;
      case 'Ngồi':
        return Icons.event_seat;
      default:
        return Icons.fitness_center;
    }
  }

  Color _getActivityColor(String activityName) {
    switch (activityName) {
      case 'Chạy':
        return Colors.red;
      case 'Đi bộ':
        return Colors.green;
      case 'Leo cầu thang':
        return Colors.purple;
      case 'Đứng':
        return Colors.blue;
      case 'Ngồi':
        return Colors.grey;
      default:
        return Colors.orange;
    }
  }
}
