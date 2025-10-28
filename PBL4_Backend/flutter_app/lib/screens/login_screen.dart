import 'package:flutter/material.dart';
import '../api/api_service.dart';
import 'package:shared_preferences/shared_preferences.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final ApiService api = ApiService();
  final TextEditingController emailController = TextEditingController();
  final TextEditingController passwordController = TextEditingController();
  bool isLoading = false;

 void handleLogin() async {
  setState(() => isLoading = true);

  final res = await api.login(
    emailController.text.trim(),
    passwordController.text.trim(),
  );

  setState(() => isLoading = false);

  if (res.containsKey('access_token')) {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('access_token', res['access_token']); // ✅ Lưu token

    Navigator.pushReplacementNamed(context, '/home');
  } else {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          res['detail'] is List
              ? res['detail'][0].toString()
              : res['detail'].toString(),
        ),
      ),
    );
  }
}


  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Đăng nhập')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            TextField(controller: emailController, decoration: const InputDecoration(labelText: 'Email')),
            TextField(controller: passwordController, obscureText: true, decoration: const InputDecoration(labelText: 'Mật khẩu')),
            const SizedBox(height: 20),
            isLoading
                ? const CircularProgressIndicator()
                : ElevatedButton(onPressed: handleLogin, child: const Text('Đăng nhập')),
            TextButton(
              onPressed: () => Navigator.pushNamed(context, '/register'),
              child: const Text('Chưa có tài khoản? Đăng ký'),
            )
          ],
        ),
      ),
    );
  }
}
