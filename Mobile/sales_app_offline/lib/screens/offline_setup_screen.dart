import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../db/database_helper.dart';
import 'dashboard_screen.dart';

class OfflineSetupScreen extends StatefulWidget {
  const OfflineSetupScreen({super.key});

  @override
  State<OfflineSetupScreen> createState() => _OfflineSetupScreenState();
}

class _OfflineSetupScreenState extends State<OfflineSetupScreen> {
  @override
  void initState() {
    super.initState();
    _mockSetup();
  }

  Future<void> _mockSetup() async {
    // محاكاة إعداد سريع عشان نقدر ندخل نجرب البرنامج ونعمل فواتير
    final dbHelper = DatabaseHelper();
    await dbHelper.setConfig('salesperson_id', '1', activeRole: 'salesperson');
    await dbHelper.setConfig('branch_id', '1');
    await dbHelper.setConfig('base_url', 'offline');
    
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('app_mode', 'Offline');

    if (!mounted) return;
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(builder: (context) => const DashboardScreen()),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF4F6F8),
      body: const Center(
        child: CircularProgressIndicator(color: Color(0xFF1A4571)),
      ),
    );
  }
}
