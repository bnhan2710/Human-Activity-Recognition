import 'dart:convert';
import 'package:http/http.dart' as http;

class HARApiService {
  static const String baseUrl = 'http://localhost:8000';

  // Singleton
  static final HARApiService _instance = HARApiService._internal();
  factory HARApiService() => _instance;
  HARApiService._internal();

  /// Health check
  Future<Map<String, dynamic>> healthCheck() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/health'));
      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Health check failed');
      }
    } catch (e) {
      print('❌ Health check error: $e');
      rethrow;
    }
  }

  /// Get recent predictions
  Future<List<Map<String, dynamic>>> getRecentPredictions(
      {int limit = 10}) async {
    try {
      final response =
          await http.get(Uri.parse('$baseUrl/predictions/recent?limit=$limit'));

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return List<Map<String, dynamic>>.from(data['predictions']);
      } else {
        throw Exception('Failed to get predictions');
      }
    } catch (e) {
      print('❌ Get predictions error: $e');
      return [];
    }
  }

  /// Get user statistics
  Future<Map<String, dynamic>> getUserStatistics(
      {required String userId, int days = 7}) async {
    try {
      final response =
          await http.get(Uri.parse('$baseUrl/statistics/$userId?days=$days'));

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to get statistics');
      }
    } catch (e) {
      print('❌ Get statistics error: $e');
      rethrow;
    }
  }

  /// Send sensor data
  Future<Map<String, dynamic>> sendSensorData(Map<String, dynamic> data) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/sensor_data'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode(data),
      );

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to send sensor data');
      }
    } catch (e) {
      print('❌ Send sensor data error: $e');
      rethrow;
    }
  }

  /// Clear buffer
  Future<void> clearBuffer() async {
    try {
      await http.delete(Uri.parse('$baseUrl/buffer/clear'));
    } catch (e) {
      print('❌ Clear buffer error: $e');
    }
  }
}
