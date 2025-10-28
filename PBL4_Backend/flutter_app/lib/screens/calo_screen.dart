import 'package:flutter/material.dart';
import '../api/api_service.dart';

class CaloScreen extends StatefulWidget {
  const CaloScreen({super.key});

  @override
  State<CaloScreen> createState() => _CaloScreenState();
}

class _CaloScreenState extends State<CaloScreen> {
  final ApiService api = ApiService();
  DateTime selectedDate = DateTime.now();
  bool isLoading = true;
  double totalCalories = 0;
  Map<String, dynamic> activities = {};

  @override
  void initState() {
    super.initState();
    loadCaloriesData();
  }

  void loadCaloriesData() async {
    setState(() => isLoading = true);

    final dateStr =
        '${selectedDate.year}-${selectedDate.month.toString().padLeft(2, '0')}-${selectedDate.day.toString().padLeft(2, '0')}';
    final result = await api.getCaloriesByDate(dateStr);

    if (result['error'] == null) {
      setState(() {
        totalCalories = (result['total_calories'] ?? 0).toDouble();
        activities = result['activities'] ?? {};
        isLoading = false;
      });
    } else {
      setState(() => isLoading = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(result['error'] ?? 'Lỗi không xác định')),
      );
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
      loadCaloriesData();
    }
  }

  @override
  Widget build(BuildContext context) {
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
      body: isLoading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Date Picker Card
                  Card(
                    elevation: 3,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: ListTile(
                      leading: const Icon(
                        Icons.calendar_today,
                        color: Colors.orangeAccent,
                      ),
                      title: Text(
                        '${selectedDate.day}/${selectedDate.month}/${selectedDate.year}',
                        style: const TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 16,
                        ),
                      ),
                      trailing: ElevatedButton(
                        onPressed: selectDate,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.orangeAccent,
                        ),
                        child: const Text('Chọn ngày'),
                      ),
                    ),
                  ),

                  const SizedBox(height: 24),

                  // Total Calories Card
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(24),
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                        colors: [Color(0xFFFF6F00), Color(0xFFFF9800)],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                      borderRadius: BorderRadius.circular(20),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.orange.withOpacity(0.3),
                          blurRadius: 10,
                          offset: const Offset(0, 5),
                        ),
                      ],
                    ),
                    child: Column(
                      children: [
                        const Icon(
                          Icons.local_fire_department,
                          size: 60,
                          color: Colors.white,
                        ),
                        const SizedBox(height: 12),
                        const Text(
                          'Tổng calo tiêu thụ',
                          style: TextStyle(fontSize: 18, color: Colors.white70),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          '${totalCalories.toStringAsFixed(1)} kcal',
                          style: const TextStyle(
                            fontSize: 40,
                            fontWeight: FontWeight.bold,
                            color: Colors.white,
                          ),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 24),

                  // Activities Breakdown
                  const Text(
                    'Chi tiết theo hoạt động',
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                      color: Colors.black87,
                    ),
                  ),

                  const SizedBox(height: 16),

                  activities.isEmpty
                      ? const Center(
                          child: Padding(
                            padding: EdgeInsets.all(32),
                            child: Text(
                              'Chưa có hoạt động nào trong ngày này',
                              style: TextStyle(
                                fontSize: 16,
                                color: Colors.grey,
                              ),
                            ),
                          ),
                        )
                      : Column(
                          children: activities.entries.map((entry) {
                            final activityName = entry.key;
                            final activityData = entry.value;
                            final calories = (activityData['calories'] ?? 0)
                                .toDouble();
                            final duration = (activityData['duration'] ?? 0)
                                .toDouble();
                            final count = activityData['count'] ?? 0;

                            return Card(
                              margin: const EdgeInsets.only(bottom: 12),
                              elevation: 2,
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(16),
                              ),
                              child: Padding(
                                padding: const EdgeInsets.all(16),
                                child: Row(
                                  children: [
                                    Container(
                                      width: 50,
                                      height: 50,
                                      decoration: BoxDecoration(
                                        color: _getActivityColor(
                                          activityName,
                                        ).withOpacity(0.2),
                                        borderRadius: BorderRadius.circular(12),
                                      ),
                                      child: Icon(
                                        _getActivityIcon(activityName),
                                        color: _getActivityColor(activityName),
                                        size: 28,
                                      ),
                                    ),
                                    const SizedBox(width: 16),
                                    Expanded(
                                      child: Column(
                                        crossAxisAlignment:
                                            CrossAxisAlignment.start,
                                        children: [
                                          Text(
                                            activityName,
                                            style: const TextStyle(
                                              fontSize: 16,
                                              fontWeight: FontWeight.bold,
                                            ),
                                          ),
                                          const SizedBox(height: 4),
                                          Text(
                                            '$count lần • ${(duration / 60).toStringAsFixed(0)} phút',
                                            style: const TextStyle(
                                              fontSize: 14,
                                              color: Colors.grey,
                                            ),
                                          ),
                                        ],
                                      ),
                                    ),
                                    Text(
                                      '${calories.toStringAsFixed(1)} kcal',
                                      style: TextStyle(
                                        fontSize: 16,
                                        fontWeight: FontWeight.bold,
                                        color: _getActivityColor(activityName),
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            );
                          }).toList(),
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
