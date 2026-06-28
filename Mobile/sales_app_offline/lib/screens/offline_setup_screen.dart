import 'package:flutter/material.dart';

class OfflineSetupScreen extends StatelessWidget {
  const OfflineSetupScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('إعداد وضع الأوفلاين')),
      body: const Center(
        child: Text('واجهة إعداد قاعدة البيانات محلياً (قيد التطوير)'),
      ),
    );
  }
}
