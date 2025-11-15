import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import '../services/har_api_service.dart';
import 'dart:async';

class ActivityStatisticsScreen extends StatefulWidget {
  final String userId;

  const ActivityStatisticsScreen({super.key, this.userId = 'user1'});

  @override
  State<ActivityStatisticsScreen> createState() =>
      _ActivityStatisticsScreenState();
}

class _ActivityStatisticsScreenState extends State<ActivityStatisticsScreen> {
  final HARApiService _apiService = HARApiService();
  Map<String, dynamic>? _statistics;
  bool _isLoading = true;
  Timer? _timer;
  int _selectedDays = 7;

  @override
  void initState() {
    super.initState();
    _loadStatistics();
    // Auto refresh every 5 seconds
    _timer =
        Timer.periodic(const Duration(seconds: 5), (_) => _loadStatistics());
  }

  Future<void> _loadStatistics() async {
    try {
      final stats = await _apiService.getUserStatistics(
        userId: widget.userId,
        days: _selectedDays,
      );

      if (mounted) {
        setState(() {
          _statistics = stats;
          _isLoading = false;
        });
      }
    } catch (e) {
      print('Error loading statistics: $e');
      setState(() {
        _isLoading = false;
      });
    }
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Color _getActivityColor(String activity) {
    switch (activity) {
      case 'WALKING':
        return Colors.blue;
      case 'RUNNING':
        return Colors.red;
      case 'UPSTAIRS':
        return Colors.green;
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Activity Statistics'),
        backgroundColor: Colors.blue,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadStatistics,
            tooltip: 'Refresh',
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _statistics == null
              ? const Center(child: Text('No data available'))
              : SingleChildScrollView(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Time range selector
                      _buildTimeRangeSelector(),

                      const SizedBox(height: 24),

                      // Summary cards
                      _buildSummaryCard(),

                      const SizedBox(height: 24),

                      // Pie chart
                      const Text(
                        'Activity Distribution',
                        style: TextStyle(
                            fontSize: 20, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 16),
                      _buildPieChart(),

                      const SizedBox(height: 24),

                      // Activity list
                      const Text(
                        'Activity Details',
                        style: TextStyle(
                            fontSize: 20, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 16),
                      _buildActivityList(),
                    ],
                  ),
                ),
    );
  }

  Widget _buildTimeRangeSelector() {
    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Time Range',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              children: [1, 7, 14, 30].map((days) {
                return ChoiceChip(
                  label: Text('$days days'),
                  selected: _selectedDays == days,
                  onSelected: (selected) {
                    setState(() {
                      _selectedDays = days;
                      _isLoading = true;
                    });
                    _loadStatistics();
                  },
                );
              }).toList(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSummaryCard() {
    final total = _statistics?['total_predictions'] ?? 0;

    return Card(
      elevation: 4,
      color: Colors.blue[50],
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceAround,
          children: [
            Column(
              children: [
                const Icon(Icons.show_chart, size: 40, color: Colors.blue),
                const SizedBox(height: 8),
                Text(
                  '$total',
                  style: const TextStyle(
                    fontSize: 32,
                    fontWeight: FontWeight.bold,
                    color: Colors.blue,
                  ),
                ),
                const Text('Total Activities'),
              ],
            ),
            Column(
              children: [
                const Icon(Icons.calendar_today, size: 40, color: Colors.green),
                const SizedBox(height: 8),
                Text(
                  '$_selectedDays',
                  style: const TextStyle(
                    fontSize: 32,
                    fontWeight: FontWeight.bold,
                    color: Colors.green,
                  ),
                ),
                const Text('Days'),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPieChart() {
    final stats = _statistics?['statistics'] as Map<String, dynamic>? ?? {};

    if (stats.isEmpty) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(32.0),
          child: Text('No activity data'),
        ),
      );
    }

    return SizedBox(
      height: 300,
      child: PieChart(
        PieChartData(
          sections: stats.entries.map((entry) {
            final activity = entry.key;
            final data = entry.value as Map<String, dynamic>;
            final percentage = data['percentage'] as double;

            return PieChartSectionData(
              value: percentage,
              title: '${percentage.toStringAsFixed(1)}%',
              color: _getActivityColor(activity),
              radius: 100,
              titleStyle: const TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            );
          }).toList(),
          sectionsSpace: 2,
          centerSpaceRadius: 40,
        ),
      ),
    );
  }

  Widget _buildActivityList() {
    final stats = _statistics?['statistics'] as Map<String, dynamic>? ?? {};

    if (stats.isEmpty) {
      return const Center(child: Text('No activity data'));
    }

    // Sort by count descending
    final sortedEntries = stats.entries.toList()
      ..sort((a, b) {
        final countA = (a.value as Map)['count'] as int;
        final countB = (b.value as Map)['count'] as int;
        return countB.compareTo(countA);
      });

    return Column(
      children: sortedEntries.map((entry) {
        final activity = entry.key;
        final data = entry.value as Map<String, dynamic>;
        final count = data['count'] as int;
        final percentage = data['percentage'] as double;
        final color = _getActivityColor(activity);
        final icon = _getActivityIcon(activity);

        return Card(
          margin: const EdgeInsets.only(bottom: 12),
          child: ListTile(
            leading: CircleAvatar(
              backgroundColor: color,
              child: Icon(icon, color: Colors.white),
            ),
            title: Text(
              activity,
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
            subtitle: Text('$count times'),
            trailing: Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: color.withOpacity(0.2),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                '${percentage.toStringAsFixed(1)}%',
                style: TextStyle(
                  color: color,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ),
        );
      }).toList(),
    );
  }
}
