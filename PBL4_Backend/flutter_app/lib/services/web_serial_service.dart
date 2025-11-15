import 'dart:async';
import 'dart:html' as html;
import 'dart:js_util' as js_util;

class WebSerialService {
  static final WebSerialService _instance = WebSerialService._internal();
  factory WebSerialService() => _instance;
  WebSerialService._internal();

  dynamic _port;
  dynamic _reader;
  bool _isReading = false;

  // Stream để broadcast dữ liệu nhận được
  final _dataStreamController = StreamController<String>.broadcast();
  Stream<String> get dataStream => _dataStreamController.stream;

  // Stream trạng thái kết nối
  final _connectionStateController = StreamController<bool>.broadcast();
  Stream<bool> get connectionStateStream => _connectionStateController.stream;

  bool _isConnected = false;
  bool get isConnected => _isConnected;

  String _buffer = '';

  /// Kiểm tra Web Serial API có khả dụng không
  bool isWebSerialSupported() {
    return js_util.hasProperty(html.window.navigator, 'serial');
  }

  /// Yêu cầu user chọn serial port
  Future<bool> requestPort() async {
    try {
      if (!isWebSerialSupported()) {
        print('❌ Web Serial API not supported');
        return false;
      }

      print('🔄 Requesting serial port...');

      final navigator = html.window.navigator;
      final serial = js_util.getProperty(navigator, 'serial');

      // Request port with filter for ESP32
      final options = js_util.jsify({
        'filters': [
          {'usbVendorId': 0x10C4}, // Silicon Labs CP210x
          {'usbVendorId': 0x1A86}, // CH340
          {'usbVendorId': 0x0403}, // FTDI
        ]
      });

      _port = await js_util.promiseToFuture(
          js_util.callMethod(serial, 'requestPort', [options]));

      print('✅ Port selected');
      return true;
    } catch (e) {
      print('❌ Error requesting port: $e');
      return false;
    }
  }

  /// Kết nối và mở port
  Future<bool> connect({int baudRate = 115200}) async {
    try {
      if (_port == null) {
        print('⚠️ No port selected. Call requestPort() first.');
        return false;
      }

      print('🔄 Opening port at $baudRate baud...');

      // Open port
      final openOptions = js_util.jsify({
        'baudRate': baudRate,
        'dataBits': 8,
        'stopBits': 1,
        'parity': 'none',
        'flowControl': 'none',
      });

      await js_util
          .promiseToFuture(js_util.callMethod(_port, 'open', [openOptions]));

      _isConnected = true;
      _connectionStateController.add(true);

      print('✅ Port opened');

      // Start reading
      _startReading();

      return true;
    } catch (e) {
      print('❌ Error opening port: $e');
      _isConnected = false;
      _connectionStateController.add(false);
      return false;
    }
  }

  /// Đọc dữ liệu liên tục
  void _startReading() async {
    if (_port == null || _isReading) return;

    _isReading = true;

    try {
      final readable = js_util.getProperty(_port, 'readable');
      _reader = js_util.callMethod(readable, 'getReader', []);

      while (_isReading && _isConnected) {
        try {
          final result = await js_util
              .promiseToFuture(js_util.callMethod(_reader, 'read', []));

          final done = js_util.getProperty(result, 'done');
          if (done == true) {
            print('⚠️ Stream closed');
            break;
          }

          final value = js_util.getProperty(result, 'value');
          if (value != null) {
            // Convert Uint8Array to String
            final List<int> bytes = List<int>.from(value);
            final String received = String.fromCharCodes(bytes);

            print('📥 Received: $received');

            // Add to buffer
            _buffer += received;
            _processBuffer();
          }
        } catch (e) {
          if (_isReading) {
            print('❌ Read error: $e');
          }
          break;
        }
      }
    } catch (e) {
      print('❌ Reading error: $e');
    } finally {
      _isReading = false;
      if (_reader != null) {
        try {
          await js_util
              .promiseToFuture(js_util.callMethod(_reader, 'releaseLock', []));
        } catch (e) {
          print('Error releasing reader: $e');
        }
      }
    }
  }

  /// Xử lý buffer
  void _processBuffer() {
    while (_buffer.contains('\n')) {
      int index = _buffer.indexOf('\n');
      String line = _buffer.substring(0, index).trim();
      _buffer = _buffer.substring(index + 1);

      if (line.isNotEmpty) {
        print('📊 Complete data: $line');
        _dataStreamController.add(line);
      }
    }
  }

  /// Gửi dữ liệu
  Future<void> sendData(String data) async {
    try {
      if (_port == null || !_isConnected) {
        print('⚠️ Not connected');
        return;
      }

      final writable = js_util.getProperty(_port, 'writable');
      final writer = js_util.callMethod(writable, 'getWriter', []);

      final bytes = data.codeUnits;
      final uint8Array = js_util.jsify({'0': bytes});

      await js_util
          .promiseToFuture(js_util.callMethod(writer, 'write', [uint8Array]));

      await js_util
          .promiseToFuture(js_util.callMethod(writer, 'releaseLock', []));

      print('📤 Sent: $data');
    } catch (e) {
      print('❌ Send error: $e');
    }
  }

  /// Ngắt kết nối
  Future<void> disconnect() async {
    try {
      _isReading = false;

      if (_reader != null) {
        try {
          await js_util
              .promiseToFuture(js_util.callMethod(_reader, 'cancel', []));
        } catch (e) {
          print('Error canceling reader: $e');
        }
        _reader = null;
      }

      if (_port != null) {
        try {
          await js_util.promiseToFuture(js_util.callMethod(_port, 'close', []));
        } catch (e) {
          print('Error closing port: $e');
        }
        _port = null;
      }

      _isConnected = false;
      _connectionStateController.add(false);
      _buffer = '';

      print('🔌 Disconnected');
    } catch (e) {
      print('❌ Disconnect error: $e');
    }
  }

  void dispose() {
    disconnect();
    _dataStreamController.close();
    _connectionStateController.close();
  }
}
