import 'package:flutter/material.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:intl/intl.dart';
import 'package:fl_chart/fl_chart.dart';

class CaloScreenPredictions extends StatefulWidget {
  const CaloScreenPredictions({super.key});

  @override
  State<CaloScreenPredictions> createState() => _CaloScreenPredictionsState();
}

class _CaloScreenPredictionsState extends State<CaloScreenPredictions> {
  DateTime selectedDate = DateTime.now();
  final String userId = 'user1'; // Sử dụng user_id mặc định từ backend

  // Calorie estimates per minute for each activity
  final Map<String, double> caloriesPerMinute = {
    'WALKING': 3.5,
    'RUNNING': 9.0,
    'UPSTAIRS': 7.0,
    'DOWNSTAIRS': 5.0,
    'SITTING': 1.0,
    'STANDING': 1.5,
  };

  final Map<String, String> activityTranslations = {
    'WALKING': 'Đi bộ',
    'RUNNING': 'Chạy',
    'UPSTAIRS': 'Lên cầu thang',
    'DOWNSTAIRS': 'Xuống cầu thang',
    'SITTING': 'Ngồi',
    'STANDING': 'Đứng',
  };

  void _selectDate() async {
    final pickedDate = await showDatePicker(
      context: context,
      initialDate: selectedDate,
      firstDate: DateTime(2020),
      lastDate: DateTime.now(),
      locale: const Locale('vi', 'VN'),
    );

    if (pickedDate != null && pickedDate != selectedDate) {
      setState(() => selectedDate = pickedDate);
    }
  }

  Stream<QuerySnapshot> _getPredictionsStream() {
    // Query đơn giản chỉ dùng user_id, lọc theo ngày ở client
    print('🔍 Query Firestore: user_id=$userId');
    return FirebaseFirestore.instance
        .collection('activity_predictions')
        .where('user_id', isEqualTo: userId)
        .snapshots();
  }

  List<DocumentSnapshot> _filterByDate(List<DocumentSnapshot> docs) {
    print('📊 Total docs from Firestore: ${docs.length}');
    DateTime startOfDay = DateTime(
      selectedDate.year,
      selectedDate.month,
      selectedDate.day,
    );
    DateTime endOfDay = startOfDay.add(const Duration(days: 1));
    print('📅 Filtering for date: ${selectedDate.toString().split(' ')[0]}');

    final filtered = docs.where((doc) {
      var data = doc.data() as Map<String, dynamic>;
      String? startTimeStr = data['start_time'];
      if (startTimeStr == null) {
        print('⚠️  Doc ${doc.id} has no start_time');
        return false;
      }

      try {
        DateTime startTime = DateTime.parse(startTimeStr);
        bool matches =
            startTime.isAfter(startOfDay) && startTime.isBefore(endOfDay);
        if (matches) {
          print(
              '✅ Doc ${doc.id}: ${data['activity']} at ${startTime.toString()}');
        }
        return matches;
      } catch (e) {
        print('❌ Error parsing start_time for doc ${doc.id}: $e');
        return false;
      }
    }).toList();

    print('📊 Filtered docs: ${filtered.length}');
    return filtered;
  }

  Map<String, dynamic> _calculateStats(List<DocumentSnapshot> docs) {
    double totalCalories = 0;
    double totalDuration = 0; // in seconds
    Map<String, int> activityCount = {};
    Map<String, double> activityCalories = {};
    Map<String, double> activityDuration = {};

    for (var doc in docs) {
      var data = doc.data() as Map<String, dynamic>;

      String activity = data['activity'] ?? 'UNKNOWN';
      double durationSeconds = (data['duration_seconds'] ?? 0.0).toDouble();
      double durationMinutes = durationSeconds / 60.0;

      // Calculate calories based on duration and activity type
      double calorieRate = caloriesPerMinute[activity] ?? 2.0;
      double calories = calorieRate * durationMinutes;

      totalCalories += calories;
      totalDuration += durationSeconds;

      activityCount[activity] = (activityCount[activity] ?? 0) + 1;
      activityCalories[activity] = (activityCalories[activity] ?? 0) + calories;
      activityDuration[activity] =
          (activityDuration[activity] ?? 0) + durationSeconds;
    }

    return {
      'totalCalories': totalCalories,
      'totalDuration': totalDuration,
      'activityCount': activityCount,
      'activityCalories': activityCalories,
      'activityDuration': activityDuration,
      'totalActivities': docs.length,
    };
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Thống kê Calo'),
        elevation: 0,
        backgroundColor: Colors.orange[700],
      ),
      body: Column(
        children: [
          _buildDateSelector(),
          Expanded(
            child: StreamBuilder<QuerySnapshot>(
              stream: _getPredictionsStream(),
              builder: (context, snapshot) {
                if (snapshot.connectionState == ConnectionState.waiting) {
                  return const Center(child: CircularProgressIndicator());
                }

                if (snapshot.hasError) {
                  return Center(
                    child: Text('Lỗi: ${snapshot.error}'),
                  );
                }

                if (!snapshot.hasData || snapshot.data!.docs.isEmpty) {
                  return _buildEmptyState();
                }

                // Lọc dữ liệu theo ngày được chọn
                final filteredDocs = _filterByDate(snapshot.data!.docs);

                if (filteredDocs.isEmpty) {
                  return _buildEmptyState();
                }

                final stats = _calculateStats(filteredDocs);

                return SingleChildScrollView(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _buildSummaryCard(stats),
                      const SizedBox(height: 16),
                      _buildActivityBreakdown(stats),
                      const SizedBox(height: 16),
                      _buildCalorieChart(stats),
                      const SizedBox(height: 16),
                      _buildDurationChart(stats),
                    ],
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDateSelector() {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 20),
      decoration: BoxDecoration(
        color: Colors.orange[700],
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 4,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Ngày được chọn',
                style: TextStyle(
                  color: Colors.white70,
                  fontSize: 12,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                DateFormat('dd/MM/yyyy').format(selectedDate),
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          ElevatedButton.icon(
            onPressed: _selectDate,
            icon: const Icon(Icons.calendar_today, size: 18),
            label: const Text('Chọn ngày'),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.white,
              foregroundColor: Colors.orange[700],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.inbox_outlined, size: 80, color: Colors.grey[400]),
          const SizedBox(height: 16),
          Text(
            'Chưa có dữ liệu hoạt động',
            style: TextStyle(fontSize: 18, color: Colors.grey[600]),
          ),
          const SizedBox(height: 8),
          Text(
            'Hãy bắt đầu vận động!',
            style: TextStyle(fontSize: 14, color: Colors.grey[500]),
          ),
        ],
      ),
    );
  }

  Widget _buildSummaryCard(Map<String, dynamic> stats) {
    final totalCalories = stats['totalCalories'] as double;
    final totalDuration = stats['totalDuration'] as double;

    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _buildStatItem(
                  Icons.local_fire_department,
                  '${totalCalories.toStringAsFixed(1)}',
                  'Calo',
                  Colors.orange,
                ),
                _buildStatItem(
                  Icons.timer,
                  '${(totalDuration / 60).toStringAsFixed(0)}',
                  'Phút',
                  Colors.blue,
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatItem(
      IconData icon, String value, String label, Color color) {
    return Column(
      children: [
        Icon(icon, size: 40, color: color),
        const SizedBox(height: 8),
        Text(
          value,
          style: TextStyle(
            fontSize: 24,
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
        Text(
          label,
          style: TextStyle(
            fontSize: 12,
            color: Colors.grey[600],
          ),
        ),
      ],
    );
  }

  Widget _buildActivityBreakdown(Map<String, dynamic> stats) {
    final activityCalories = stats['activityCalories'] as Map<String, double>;
    final activityDuration = stats['activityDuration'] as Map<String, double>;

    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Chi tiết hoạt động',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),
            ...activityCalories.entries.map((entry) {
              final activity = entry.key;
              final calories = entry.value;
              final duration = activityDuration[activity] ?? 0;
              final activityName = activityTranslations[activity] ?? activity;

              return Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Row(
                  children: [
                    _getActivityIcon(activity),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            activityName,
                            style: const TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                          Text(
                            '${(duration / 60).toStringAsFixed(1)} phút',
                            style: TextStyle(
                              fontSize: 12,
                              color: Colors.grey[600],
                            ),
                          ),
                        ],
                      ),
                    ),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        Text(
                          '${calories.toStringAsFixed(1)}',
                          style: const TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                            color: Colors.orange,
                          ),
                        ),
                        const Text(
                          'Calo',
                          style: TextStyle(
                            fontSize: 11,
                            color: Colors.grey,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              );
            }).toList(),
          ],
        ),
      ),
    );
  }

  Widget _buildCalorieChart(Map<String, dynamic> stats) {
    final activityCalories = stats['activityCalories'] as Map<String, double>;

    if (activityCalories.isEmpty) return const SizedBox.shrink();

    final sortedEntries = activityCalories.entries.toList()
      ..sort((a, b) => b.value.compareTo(a.value));

    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Biểu đồ Calo theo hoạt động',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 20),
            SizedBox(
              height: 200,
              child: BarChart(
                BarChartData(
                  alignment: BarChartAlignment.spaceAround,
                  maxY: sortedEntries.first.value * 1.2,
                  barGroups: sortedEntries.asMap().entries.map((entry) {
                    return BarChartGroupData(
                      x: entry.key,
                      barRods: [
                        BarChartRodData(
                          toY: entry.value.value,
                          color: Colors.orange,
                          width: 20,
                          borderRadius: const BorderRadius.only(
                            topLeft: Radius.circular(6),
                            topRight: Radius.circular(6),
                          ),
                        ),
                      ],
                    );
                  }).toList(),
                  titlesData: FlTitlesData(
                    bottomTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        getTitlesWidget: (value, meta) {
                          if (value.toInt() < sortedEntries.length) {
                            final activity = sortedEntries[value.toInt()].key;
                            final name =
                                activityTranslations[activity] ?? activity;
                            return Padding(
                              padding: const EdgeInsets.only(top: 8),
                              child: Text(
                                name,
                                style: const TextStyle(fontSize: 10),
                                textAlign: TextAlign.center,
                              ),
                            );
                          }
                          return const Text('');
                        },
                      ),
                    ),
                    leftTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        reservedSize: 40,
                        getTitlesWidget: (value, meta) {
                          return Text(
                            value.toInt().toString(),
                            style: const TextStyle(fontSize: 10),
                          );
                        },
                      ),
                    ),
                    topTitles: const AxisTitles(
                      sideTitles: SideTitles(showTitles: false),
                    ),
                    rightTitles: const AxisTitles(
                      sideTitles: SideTitles(showTitles: false),
                    ),
                  ),
                  borderData: FlBorderData(show: false),
                  gridData: FlGridData(show: true, drawVerticalLine: false),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDurationChart(Map<String, dynamic> stats) {
    final activityDuration = stats['activityDuration'] as Map<String, double>;

    if (activityDuration.isEmpty) return const SizedBox.shrink();

    final sortedEntries = activityDuration.entries.toList()
      ..sort((a, b) => b.value.compareTo(a.value));

    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Thời lượng hoạt động (phút)',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 20),
            SizedBox(
              height: 200,
              child: BarChart(
                BarChartData(
                  alignment: BarChartAlignment.spaceAround,
                  maxY: (sortedEntries.first.value / 60) * 1.2,
                  barGroups: sortedEntries.asMap().entries.map((entry) {
                    return BarChartGroupData(
                      x: entry.key,
                      barRods: [
                        BarChartRodData(
                          toY: entry.value.value / 60,
                          color: Colors.blue,
                          width: 20,
                          borderRadius: const BorderRadius.only(
                            topLeft: Radius.circular(6),
                            topRight: Radius.circular(6),
                          ),
                        ),
                      ],
                    );
                  }).toList(),
                  titlesData: FlTitlesData(
                    bottomTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        getTitlesWidget: (value, meta) {
                          if (value.toInt() < sortedEntries.length) {
                            final activity = sortedEntries[value.toInt()].key;
                            final name =
                                activityTranslations[activity] ?? activity;
                            return Padding(
                              padding: const EdgeInsets.only(top: 8),
                              child: Text(
                                name,
                                style: const TextStyle(fontSize: 10),
                                textAlign: TextAlign.center,
                              ),
                            );
                          }
                          return const Text('');
                        },
                      ),
                    ),
                    leftTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        reservedSize: 40,
                        getTitlesWidget: (value, meta) {
                          return Text(
                            value.toInt().toString(),
                            style: const TextStyle(fontSize: 10),
                          );
                        },
                      ),
                    ),
                    topTitles: const AxisTitles(
                      sideTitles: SideTitles(showTitles: false),
                    ),
                    rightTitles: const AxisTitles(
                      sideTitles: SideTitles(showTitles: false),
                    ),
                  ),
                  borderData: FlBorderData(show: false),
                  gridData: FlGridData(show: true, drawVerticalLine: false),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _getActivityIcon(String activity) {
    IconData icon;
    Color color;

    switch (activity) {
      case 'WALKING':
        icon = Icons.directions_walk;
        color = Colors.green;
        break;
      case 'RUNNING':
        icon = Icons.directions_run;
        color = Colors.red;
        break;
      case 'UPSTAIRS':
        icon = Icons.arrow_upward;
        color = Colors.blue;
        break;
      case 'DOWNSTAIRS':
        icon = Icons.arrow_downward;
        color = Colors.orange;
        break;
      case 'SITTING':
        icon = Icons.event_seat;
        color = Colors.purple;
        break;
      case 'STANDING':
        icon = Icons.accessibility_new;
        color = Colors.teal;
        break;
      default:
        icon = Icons.help_outline;
        color = Colors.grey;
    }

    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Icon(icon, color: color, size: 24),
    );
  }
}
