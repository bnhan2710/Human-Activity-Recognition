import 'dart:async';
import 'dart:typed_data';
import 'package:flutter_bluetooth_serial/flutter_bluetooth_serial.dart';

class BluetoothService {
  static final BluetoothService _instance = BluetoothService._internal();
  factory BluetoothService() => _instance;
  BluetoothService._internal();

  FlutterBluetoothSerial _bluetooth = FlutterBluetoothSerial.instance;
  BluetoothConnection? _connection;

  // Stream để broadcast dữ liệu nhận được
  final _dataStreamController = StreamController<String>.broadcast();
  Stream<String> get dataStream => _dataStreamController.stream;

  // Stream trạng thái kết nối
  final _connectionStateController = StreamController<bool>.broadcast();
  Stream<bool> get connectionStateStream => _connectionStateController.stream;

  bool _isConnected = false;
  bool get isConnected => _isConnected;

  // Buffer để lưu dữ liệu chưa hoàn chỉnh
  String _buffer = '';

  /// Lấy danh sách thiết bị đã pair
  Future<List<BluetoothDevice>> getPairedDevices() async {
    try {
      List<BluetoothDevice> devices = await _bluetooth.getBondedDevices();
      print('📱 Found ${devices.length} paired devices');
      return devices;
    } catch (e) {
      print('❌ Error getting paired devices: $e');
      return [];
    }
  }

  /// Kết nối với thiết bị ESP32
  Future<bool> connect(String address) async {
    try {
      print('🔄 Connecting to $address...');

      // Ngắt kết nối cũ nếu có
      await disconnect();

      // Kết nối mới
      _connection = await BluetoothConnection.toAddress(address);
      _isConnected = true;
      _connectionStateController.add(true);

      print('✅ Connected to $address');

      // Lắng nghe dữ liệu liên tục
      _listenToData();

      return true;
    } catch (e) {
      print('❌ Connection error: $e');
      _isConnected = false;
      _connectionStateController.add(false);
      return false;
    }
  }

  /// Lắng nghe dữ liệu từ ESP32 liên tục
  void _listenToData() {
    _connection?.input?.listen(
      (Uint8List data) {
        // Chuyển bytes thành string
        String received = String.fromCharCodes(data);
        print('📥 Received: $received');

        // Thêm vào buffer
        _buffer += received;

        // Xử lý từng dòng (nếu có dấu xuống dòng)
        _processBuffer();
      },
      onDone: () {
        print('⚠️ Connection closed');
        _handleDisconnect();
      },
      onError: (error) {
        print('❌ Data stream error: $error');
        _handleDisconnect();
      },
    );
  }

  /// Xử lý buffer - tách từng dòng dữ liệu
  void _processBuffer() {
    while (_buffer.contains('\n')) {
      int index = _buffer.indexOf('\n');
      String line = _buffer.substring(0, index).trim();
      _buffer = _buffer.substring(index + 1);

      if (line.isNotEmpty) {
        print('📊 Complete data: $line');
        // Broadcast dữ liệu hoàn chỉnh
        _dataStreamController.add(line);
      }
    }
  }

  /// Gửi dữ liệu đến ESP32
  Future<void> sendData(String data) async {
    try {
      if (_connection != null && _isConnected) {
        _connection!.output.add(Uint8List.fromList(data.codeUnits));
        await _connection!.output.allSent;
        print('📤 Sent: $data');
      } else {
        print('⚠️ Not connected, cannot send data');
      }
    } catch (e) {
      print('❌ Send error: $e');
    }
  }

  /// Ngắt kết nối
  Future<void> disconnect() async {
    try {
      if (_connection != null) {
        await _connection!.close();
        _connection = null;
      }
      _handleDisconnect();
      print('🔌 Disconnected');
    } catch (e) {
      print('❌ Disconnect error: $e');
    }
  }

  void _handleDisconnect() {
    _isConnected = false;
    _connectionStateController.add(false);
    _buffer = '';
  }

  /// Dọn dẹp resources
  void dispose() {
    disconnect();
    _dataStreamController.close();
    _connectionStateController.close();
  }
}
