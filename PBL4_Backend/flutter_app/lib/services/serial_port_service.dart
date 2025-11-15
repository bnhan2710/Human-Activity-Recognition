import 'dart:async';
import 'package:flutter_libserialport/flutter_libserialport.dart';

class SerialPortService {
  static final SerialPortService _instance = Serial  /// Gửi lệnh đến ESP32 (giống send_cmd trong Python với retries)
  Future<bool> sendCommand(String cmd, {int retries = 3}) async {
    for (int attempt = 0; attempt < retries; attempt++) {
      try {
        if (_port != null && _isConnected) {
          _port!.write(Uint8List.fromList('$cmd\n'.codeUnits));
          print('📤 Sent: $cmd');
          // Delay như Python: time.sleep(0.2)
          await Future.delayed(const Duration(milliseconds: 200));
          return true;
        }
      } catch (e) {
        print('⚠️ Write error (attempt ${attempt + 1}/$retries): $e');
        await Future.delayed(const Duration(milliseconds: 300));
      }
    }
    print('❌ Failed to send command: $cmd');
    return false;
  }

  /// Gửi label (giống "L:" command trong Python)
  Future<bool> setLabel(String label) async {
    return await sendCommand('L:$label');
  }internal();
  factory SerialPortService() => _instance;
  SerialPortService._internal();

  SerialPort? _port;
  SerialPortReader? _reader;
  
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

  /// Lấy danh sách COM ports có sẵn (giống Python)
  List<String> getAvailablePorts() {
    try {
      final ports = SerialPort.availablePorts;
      print('📱 All available COM ports:');
      for (var port in ports) {
        final sp = SerialPort(port);
        print('   $port: ${sp.description}');
        sp.dispose();
      }
      return ports;
    } catch (e) {
      print('❌ Error getting ports: $e');
      return [];
    }
  }

  /// Thử kết nối với danh sách ports (giống try_open_serial trong Python)
  Future<bool> tryConnectPorts({int baudRate = BAUDRATE}) async {
    print('🔍 Trying predefined ports: $SERIAL_PORTS');
    
    // Hiển thị tất cả ports
    getAvailablePorts();
    
    // Thử từng port trong danh sách
    for (String portName in SERIAL_PORTS) {
      print('\n🔄 Trying to open $portName...');
      
      bool success = await connect(portName: portName, baudRate: baudRate);
      if (success) {
        print('✅ Successfully opened $portName');
        return true;
      }
    }
    
    print('\n❌ FAILED to open any serial port!');
    print('\nTroubleshooting steps:');
    print('  1. Check if ESP32 is connected');
    print('  2. Close Arduino IDE Serial Monitor');
    print('  3. Check Device Manager > Ports (COM & LPT)');
    
    return false;
  }

  /// Kết nối với COM port (giống Python)
  Future<bool> connect({String portName = 'COM5', int baudRate = BAUDRATE}) async {
    try {
      // Ngắt kết nối cũ nếu có
      await disconnect();
      
      // Tạo port mới
      _port = SerialPort(portName);
      
      // Cấu hình port (giống Python: timeout=3)
      final config = SerialPortConfig();
      config.baudRate = baudRate;
      config.bits = 8;
      config.stopBits = 1;
      config.parity = SerialPortParity.none;
      config.setFlowControl(SerialPortFlowControl.none);
      
      _port!.config = config;
      
      // Mở port
      if (!_port!.openReadWrite()) {
        final error = SerialPort.lastError;
        if (error != null) {
          if (error.message?.contains('Access is denied') == true) {
            print('✗ $portName is BUSY (access denied)');
          } else {
            print('✗ $portName error: ${error.message}');
          }
        }
        _port?.dispose();
        _port = null;
        return false;
      }
      
      _currentPort = portName;
      _isConnected = true;
      _connectionStateController.add(true);
      
      print('✅ Connected to $portName @ $baudRate baud');
      
      // Đợi 1 giây (giống Python time.sleep(1))
      await Future.delayed(const Duration(seconds: 1));
      
      // Bắt đầu đọc dữ liệu
      _startReading();
      
      return true;
    } catch (e) {
      print('❌ Connection error: $e');
      _isConnected = false;
      _connectionStateController.add(false);
      _port?.dispose();
      _port = null;
      return false;
    }
  }

  /// Đọc dữ liệu liên tục từ COM port
  void _startReading() {
    if (_port == null) return;
    
    _reader = SerialPortReader(_port!);
    
    _reader!.stream.listen(
      (data) {
        // Chuyển bytes thành string
        String received = String.fromCharCodes(data);
        print('📥 Received: $received');
        
        // Thêm vào buffer
        _buffer += received;
        
        // Xử lý từng dòng (nếu có dấu xuống dòng)
        _processBuffer();
      },
      onError: (error) {
        print('❌ Read error: $error');
        _handleDisconnect();
      },
      onDone: () {
        print('⚠️ Port closed');
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

  /// Gửi dữ liệu qua COM port
  Future<void> sendData(String data) async {
    try {
      if (_port != null && _isConnected) {
        _port!.write(data.codeUnits);
        print('📤 Sent: $data');
      } else {
        print('⚠️ Not connected, cannot send data');
      }
    } catch (e) {
      print('❌ Send error: $e');
    }
  }

  /// Ngắt kết nối (giống finally block trong Python)
  Future<void> disconnect() async {
    try {
      print('🔌 Disconnecting...');
      
      // Gửi BYE command (giống Python)
      if (_port != null && _isConnected) {
        try {
          print('📤 Sending disconnect command to ESP32...');
          _port!.write(Uint8List.fromList('BYE\n'.codeUnits));
          await Future.delayed(const Duration(milliseconds: 500));
          print('✓ ESP32 notified');
        } catch (e) {
          print('⚠️ Could not send BYE: $e');
        }
      }
      
      _reader?.close();
      _reader = null;
      
      if (_port != null) {
        _port!.close();
        _port!.dispose();
        _port = null;
      }
      
      _handleDisconnect();
      
      // Đợi Windows giải phóng port (giống Python time.sleep(1.5))
      await Future.delayed(const Duration(milliseconds: 1500));
      
      print('✓ Serial port closed');
    } catch (e) {
      print('❌ Disconnect error: $e');
    }
  }

  void _handleDisconnect() {
    _isConnected = false;
    _currentPort = null;
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
