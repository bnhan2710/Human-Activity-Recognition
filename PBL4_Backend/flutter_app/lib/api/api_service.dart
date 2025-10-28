import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class ApiService {
  final String baseUrl = 'http://127.0.0.1:8000';

  /// 🧩 Đăng ký tài khoản
  Future<Map<String, dynamic>> register(
    String email,
    String username,
    String password,
    double weight,
  ) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/auth/register'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'email': email,
          'username': username,
          'password': password,
          'weight': weight,
        }),
      );

      final data = jsonDecode(response.body);

      if (response.statusCode == 200 || response.statusCode == 201) {
        String? token;
        if (data is Map<String, dynamic> && data.containsKey('access_token')) {
          final rawToken = data['access_token'];
          if (rawToken != null) {
            token = rawToken.toString();
            final prefs = await SharedPreferences.getInstance();
            await prefs.setString('access_token', token);
            print('Access token (register): $token');
          }
        }

        if (data is Map<String, dynamic>) {
          final result = Map<String, dynamic>.from(data);
          if (token != null) result['access_token'] = token;
          return result;
        } else {
          return {'access_token': token, 'raw': data};
        }
      } else {
        return {
          'error': 'Đăng ký thất bại (${response.statusCode})',
          'detail': data['detail'] ?? response.body,
        };
      }
    } catch (e) {
      return {'error': 'Không thể kết nối đến server', 'detail': e.toString()};
    }
  }

  /// 🔐 Đăng nhập và lưu token
  Future<Map<String, dynamic>> login(String email, String password) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/auth/login'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'email': email, 'password': password}),
      );

      final data = jsonDecode(response.body);

      if (response.statusCode == 200) {
        String? token;
        if (data is Map<String, dynamic> && data.containsKey('access_token')) {
          final rawToken = data['access_token'];
          if (rawToken != null) {
            token = rawToken.toString();
            final prefs = await SharedPreferences.getInstance();
            await prefs.setString('access_token', token);
            // In ra để developer có thể thấy token khi đăng nhập thành công
            print('Access token: $token');
          }
        }

        if (data is Map<String, dynamic>) {
          final result = Map<String, dynamic>.from(data);
          if (token != null) result['access_token'] = token;
          return result;
        } else {
          return {'access_token': token, 'raw': data};
        }
      } else {
        return {
          'error': 'Đăng nhập thất bại (${response.statusCode})',
          'detail': data['detail'] ?? response.body,
        };
      }
    } catch (e) {
      return {'error': 'Không thể kết nối đến server', 'detail': e.toString()};
    }
  }

  /// 🪪 Lấy access token từ bộ nhớ
  Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('access_token');
  }

  /// ✅ Kiểm tra token hiện tại có hợp lệ hay không (gọi /users/me)
  Future<bool> isTokenValid() async {
    final token = await getToken();
    if (token == null) return false;

    try {
      final response = await http.get(
        Uri.parse('$baseUrl/users/me'),
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
      );

      if (response.statusCode == 200) {
        // In ra token để developer kiểm tra
        print('Current access token: $token');
        return true;
      } else {
        print('Token invalid (${response.statusCode}): ${response.body}');
        return false;
      }
    } catch (e) {
      print('Error while validating token: $e');
      return false;
    }
  }

  /// 🚪 Đăng xuất (xoá token)
  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('access_token');
  }

  /// 👤 Lấy thông tin user từ API /auth/me
  Future<Map<String, dynamic>> getProfile() async {
    try {
      final token = await getToken();
      if (token == null) {
        return {'error': 'Chưa đăng nhập'};
      }

      final response = await http.get(
        Uri.parse('$baseUrl/auth/me'),
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
      );

      final data = jsonDecode(response.body);

      if (response.statusCode == 200) {
        return data;
      } else {
        return {
          'error': 'Không lấy được thông tin (${response.statusCode})',
          'detail': data['detail'] ?? response.body,
        };
      }
    } catch (e) {
      return {'error': 'Lỗi kết nối đến server', 'detail': e.toString()};
    }
  }

  /// 📊 Lấy thống kê calo theo ngày
  Future<Map<String, dynamic>> getCaloriesByDate(String date) async {
    try {
      final token = await getToken();
      if (token == null) {
        return {'error': 'Chưa đăng nhập'};
      }

      print('Calling calories API with token: ${token.substring(0, 20)}...');

      final response = await http.get(
        Uri.parse('$baseUrl/activities/calories?target_date=$date'),
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
      );

      print('Calories API response status: ${response.statusCode}');
      print('Calories API response body: ${response.body}');

      final data = jsonDecode(response.body);

      if (response.statusCode == 200) {
        return data;
      } else {
        return {
          'error': 'Không lấy được dữ liệu (${response.statusCode})',
          'detail': data['detail'] ?? response.body,
        };
      }
    } catch (e) {
      return {'error': 'Lỗi kết nối đến server', 'detail': e.toString()};
    }
  }

  /// 📜 Lấy lịch sử hoạt động theo ngày
  Future<Map<String, dynamic>> getActivityHistory(String date) async {
    try {
      final token = await getToken();
      if (token == null) {
        return {'error': 'Chưa đăng nhập'};
      }

      print('Calling history API with date: $date');

      final response = await http.get(
        Uri.parse('$baseUrl/activities/history?target_date=$date'),
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
      );

      print('History API response status: ${response.statusCode}');
      print('History API response body: ${response.body}');

      final data = jsonDecode(response.body);

      if (response.statusCode == 200) {
        return data;
      } else {
        return {
          'error': 'Không lấy được dữ liệu (${response.statusCode})',
          'detail': data['detail'] ?? response.body,
        };
      }
    } catch (e) {
      print('History API error: $e');
      return {'error': 'Lỗi kết nối đến server', 'detail': e.toString()};
    }
  }

  /// 🔔 Lấy danh sách thông báo
  Future<Map<String, dynamic>> getNotifications() async {
    try {
      final token = await getToken();
      if (token == null) {
        return {'error': 'Chưa đăng nhập'};
      }

      final response = await http.get(
        Uri.parse('$baseUrl/notifications'),
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
      );

      final data = jsonDecode(response.body);

      if (response.statusCode == 200) {
        return data;
      } else {
        return {
          'error': 'Không lấy được thông báo (${response.statusCode})',
          'detail': data['detail'] ?? response.body,
        };
      }
    } catch (e) {
      return {'error': 'Lỗi kết nối đến server', 'detail': e.toString()};
    }
  }

  /// ✅ Đánh dấu thông báo đã đọc
  Future<Map<String, dynamic>> markNotificationAsRead(
    int notificationId,
  ) async {
    try {
      final token = await getToken();
      if (token == null) {
        return {'error': 'Chưa đăng nhập'};
      }

      final response = await http.put(
        Uri.parse('$baseUrl/notifications/$notificationId/read'),
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
      );

      final data = jsonDecode(response.body);

      if (response.statusCode == 200) {
        return data;
      } else {
        return {
          'error': 'Không thể đánh dấu đã đọc (${response.statusCode})',
          'detail': data['detail'] ?? response.body,
        };
      }
    } catch (e) {
      return {'error': 'Lỗi kết nối đến server', 'detail': e.toString()};
    }
  }
}
