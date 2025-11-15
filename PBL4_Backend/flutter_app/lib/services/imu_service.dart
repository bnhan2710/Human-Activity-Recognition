import 'dart:async';
import 'dart:math';
import 'package:firebase_database/firebase_database.dart';
import 'firestore_service.dart';

class ImuService {
  static const int WINDOW_SIZE = 40;
  static const int FEATURE_COUNT = 9;

  final DatabaseReference _imuRef = FirebaseDatabase.instance.ref('imu_data');

  List<List<double>> _dataWindow = [];
  String? _currentActivity;
  DateTime? _activityStartTime;

  final Map<int, String> _activityLabels = {
    0: 'Đứng',
    1: 'Ngồi',
    2: 'Chạy',
    3: 'Đi bộ',
    4: 'Leo cầu thang',
  };

  final StreamController<String> _activityStreamController =
      StreamController<String>.broadcast();
  Stream<String> get activityStream => _activityStreamController.stream;

  Future<void> initialize() async {
    print('IMU Service initialized (using mock prediction)');
  }

  void startListening() {
    _imuRef.onValue.listen((event) {
      if (event.snapshot.value != null) {
        _processImuData(event.snapshot.value);
      }
    });
  }

  void _processImuData(dynamic data) {
    try {
      List<double> sample = [];

      if (data is Map) {
        sample = [
          (data['ax_g'] ?? 0.0).toDouble(),
          (data['ay_g'] ?? 0.0).toDouble(),
          (data['az_g'] ?? 0.0).toDouble(),
          (data['gx_dps'] ?? 0.0).toDouble(),
          (data['gy_dps'] ?? 0.0).toDouble(),
          (data['gz_dps'] ?? 0.0).toDouble(),
          (data['amag_g'] ?? 0.0).toDouble(),
          (data['pitch_kf'] ?? 0.0).toDouble(),
          (data['roll_kf'] ?? 0.0).toDouble(),
        ];
      }

      _dataWindow.add(sample);

      if (_dataWindow.length > WINDOW_SIZE) {
        _dataWindow.removeAt(0);
      }

      if (_dataWindow.length == WINDOW_SIZE) {
        _predictActivity();
      }
    } catch (e) {
      print('Error processing IMU data: $e');
    }
  }

  void _predictActivity() {
    // Mock prediction using simple heuristics from accelerometer magnitude
    try {
      double avgAmag = 0.0;
      double avgGx = 0.0;

      for (var sample in _dataWindow) {
        if (sample.length >= 7) {
          avgAmag += sample[6]; // amag_g
        }
        if (sample.length >= 4) {
          avgGx += sample[3].abs(); // gx_dps
        }
      }

      avgAmag /= _dataWindow.length;
      avgGx /= _dataWindow.length;

      // Simple classification based on motion intensity
      int predictedClass;
      double confidence;

      if (avgGx > 100) {
        predictedClass = 2; // Chạy
        confidence = 0.85;
      } else if (avgGx > 50) {
        predictedClass = 3; // Đi bộ
        confidence = 0.80;
      } else if (avgAmag > 1.2) {
        predictedClass = 0; // Đứng
        confidence = 0.75;
      } else {
        predictedClass = 1; // Ngồi
        confidence = 0.70;
      }

      String predictedActivity =
          _activityLabels[predictedClass] ?? 'Không xác định';

      if (_currentActivity != predictedActivity) {
        _onActivityChanged(predictedActivity, confidence);
      }
    } catch (e) {
      print('Error during prediction: $e');
    }
  }

  void _onActivityChanged(String newActivity, double confidence) {
    print(
      'Activity changed: $_currentActivity → $newActivity (confidence: ${(confidence * 100).toStringAsFixed(1)}%)',
    );

    _activityStreamController.add(newActivity);

    if (_currentActivity != null && _activityStartTime != null) {
      FirestoreService.saveActivity(
        activity: _currentActivity!,
        startTime: _activityStartTime!,
        endTime: DateTime.now(),
        confidence: confidence,
      );
    }

    _currentActivity = newActivity;
    _activityStartTime = DateTime.now();
  }

  void dispose() {
    _activityStreamController.close();
  }
}
