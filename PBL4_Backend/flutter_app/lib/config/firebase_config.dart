import 'package:firebase_core/firebase_core.dart';

class FirebaseConfig {
  // Dùng chung API key cho Android và Web
  static const String apiKey = 'AIzaSyCancHOOZLpBlGTZo9SZI8HNS22B71Fu1E';
  static const String projectId = 'imu-detection-app';
  static const String messagingSenderId = '325893434883';
  static const String storageBucket = 'imu-detection-app.firebasestorage.app';
  static const String databaseURL =
      'https://imu-detection-app-default-rtdb.asia-southeast1.firebasedatabase.app/';

  static const FirebaseOptions android = FirebaseOptions(
    apiKey: apiKey,
    appId: 'com.example.flutter_app',
    messagingSenderId: messagingSenderId,
    projectId: projectId,
    databaseURL: databaseURL,
    storageBucket: storageBucket,
  );

  static const FirebaseOptions web = FirebaseOptions(
    apiKey: apiKey,
    authDomain: "$projectId.firebaseapp.com",
    databaseURL: databaseURL,
    projectId: projectId,
    storageBucket: storageBucket,
    messagingSenderId: messagingSenderId,
    appId: "1:$messagingSenderId:web:dc4ac63209218e26d12836",
  );
}
