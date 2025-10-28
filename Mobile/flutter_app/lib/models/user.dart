class User {
  final String email;
  final String username;

  User({required this.email, required this.username});

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      email: json['email'],
      username: json['username'],
    );
  }
}
