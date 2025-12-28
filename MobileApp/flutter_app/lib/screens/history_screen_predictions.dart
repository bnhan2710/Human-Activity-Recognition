import 'package:flutter/material.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:intl/intl.dart';
import 'package:fl_chart/fl_chart.dart';

class HistoryScreenPredictions extends StatefulWidget {
  const HistoryScreenPredictions({super.key});

  @override
  State<HistoryScreenPredictions> createState() =>
      _HistoryScreenPredictionsState();
}

class _HistoryScreenPredictionsState extends State<HistoryScreenPredictions> {
  DateTime selectedDate = DateTime.now();
  final String userId = 'user1';

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
    return FirebaseFirestore.instance
        .collection('activity_predictions')
        .where('user_id', isEqualTo: userId)
        .snapshots();
  }

  List<DocumentSnapshot> _filterByDate(List<DocumentSnapshot> docs) {
    DateTime startOfDay = DateTime(
      selectedDate.year,
      selectedDate.month,
      selectedDate.day,
    );
    DateTime endOfDay = startOfDay.add(const Duration(days: 1));

    return docs.where((doc) {
      var data = doc.data() as Map<String, dynamic>;
      String? startTimeStr = data['start_time'];
      if (startTimeStr == null) return false;

      try {
        DateTime startTime = DateTime.parse(startTimeStr);
        return startTime.isAfter(startOfDay) && startTime.isBefore(endOfDay);
      } catch (e) {
        return false;
      }
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Lịch sử Hoạt động'),
        elevation: 0,
        backgroundColor: Colors.blue[700],
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
                  return Center(child: Text('Lỗi: ${snapshot.error}'));
                }

                if (!snapshot.hasData || snapshot.data!.docs.isEmpty) {
                  return _buildEmptyState();
                }

                final filteredDocs = _filterByDate(snapshot.data!.docs);

                if (filteredDocs.isEmpty) {
                  return _buildEmptyState();
                }

                return SingleChildScrollView(
                  child: _buildPieChartSection(filteredDocs),
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
        color: Colors.blue[700],
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
              foregroundColor: Colors.blue[700],
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
          Icon(Icons.history, size: 80, color: Colors.grey[400]),
          const SizedBox(height: 16),
          Text(
            'Chưa có lịch sử hoạt động',
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

  Widget _buildPieChartSection(List<DocumentSnapshot> docs) {
    // Tính toán thời gian cho từng hoạt động
    Map<String, double> activityDurations = {};
    double totalDuration = 0.0;

    for (var doc in docs) {
      var data = doc.data() as Map<String, dynamic>;
      String activity = data['activity'] ?? 'UNKNOWN';
      double duration = (data['duration_seconds'] ?? 0.0).toDouble();

      activityDurations[activity] =
          (activityDurations[activity] ?? 0.0) + duration;
      totalDuration += duration;
    }

    // Tạo sections cho pie chart
    List<PieChartSectionData> sections = [];

    activityDurations.forEach((activity, duration) {
      double percentage = (duration / totalDuration) * 100;
      Color color = _getActivityColor(activity);

      sections.add(
        PieChartSectionData(
          color: color,
          value: duration,
          title: '${percentage.toStringAsFixed(1)}%',
          radius: 100,
          titleStyle: const TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.bold,
            color: Colors.white,
          ),
        ),
      );
    });

    return Container(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Thống kê hoạt động trong ngày',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Tổng thời gian: ${_formatDuration(totalDuration)}',
            style: TextStyle(
              fontSize: 14,
              color: Colors.grey[600],
            ),
          ),
          const SizedBox(height: 20),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Pie Chart
              Expanded(
                flex: 2,
                child: SizedBox(
                  height: 250,
                  child: PieChart(
                    PieChartData(
                      sections: sections,
                      centerSpaceRadius: 0,
                      sectionsSpace: 2,
                      borderData: FlBorderData(show: false),
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 20),
              // Legend với thời gian
              Expanded(
                flex: 1,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: activityDurations.entries.map((entry) {
                    String activity = entry.key;
                    double duration = entry.value;
                    double percentage = (duration / totalDuration) * 100;
                    String activityName =
                        activityTranslations[activity] ?? activity;
                    Color color = _getActivityColor(activity);

                    return Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: Row(
                        children: [
                          Container(
                            width: 16,
                            height: 16,
                            decoration: BoxDecoration(
                              color: color,
                              borderRadius: BorderRadius.circular(4),
                            ),
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  activityName,
                                  style: const TextStyle(
                                    fontSize: 13,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                                Text(
                                  '${_formatDuration(duration)} (${percentage.toStringAsFixed(1)}%)',
                                  style: TextStyle(
                                    fontSize: 11,
                                    color: Colors.grey[600],
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    );
                  }).toList(),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Color _getActivityColor(String activity) {
    switch (activity) {
      case 'WALKING':
        return Colors.green;
      case 'RUNNING':
        return Colors.red;
      case 'UPSTAIRS':
        return Colors.blue;
      case 'DOWNSTAIRS':
        return Colors.orange;
      case 'SITTING':
        return Colors.purple;
      case 'STANDING':
        return Colors.teal;
      default:
        return Colors.grey;
    }
  }

  String _formatDuration(double seconds) {
    if (seconds < 60) {
      return '${seconds.toStringAsFixed(0)}s';
    } else if (seconds < 3600) {
      int minutes = (seconds / 60).floor();
      int secs = (seconds % 60).floor();
      return '${minutes}p ${secs}s';
    } else {
      int hours = (seconds / 3600).floor();
      int minutes = ((seconds % 3600) / 60).floor();
      return '${hours}h ${minutes}p';
    }
  }
}
