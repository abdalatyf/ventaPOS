import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'dart:io' show Platform;
import 'package:sqflite_common_ffi/sqflite_ffi.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'services/sync_worker.dart';
import 'screens/login_screen.dart';
import 'screens/dashboard_screen.dart';
import 'screens/mode_selection_screen.dart';
import 'screens/offline_setup_screen.dart';
import 'screens/pin_login_screen.dart';
import 'db/database_helper.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  if (!kIsWeb && (Platform.isWindows || Platform.isLinux || Platform.isMacOS)) {
    sqfliteFfiInit();
    databaseFactory = databaseFactoryFfi;
  }
  SyncWorker().start();
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Sales Offline',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.light,
        scaffoldBackgroundColor: const Color(0xFFF4F6F8),
        primaryColor: const Color(0xFF1A4571),
        colorScheme: const ColorScheme.light(
          primary: Color(0xFF1A4571),
          secondary: Color(0xFF1DA068),
          surface: Colors.white,
          onSurface: Color(0xFF111827),
          background: Color(0xFFF4F6F8),
          onBackground: Color(0xFF111827),
        ),
        textTheme: const TextTheme(
          bodyLarge: TextStyle(color: Color(0xFF111827)),
          bodyMedium: TextStyle(color: Color(0xFF111827)),
        ),
        cardTheme: const CardThemeData(
          color: Colors.white,
          surfaceTintColor: Colors.transparent,
          elevation: 1,
        ),
        fontFamily: 'Cairo',
      ),
      builder: (context, child) {
        return Directionality(textDirection: TextDirection.rtl, child: child!);
      },
      home: const SplashScreen(),
    );
  }
}

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});
  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  @override
  void initState() {
    super.initState();
    _checkIdentity();
  }

  Future<void> _checkIdentity() async {
    final prefs = await SharedPreferences.getInstance();
    final String? appMode = prefs.getString('app_mode');
    
    // Check local database for PIN lock
    final dbHelper = DatabaseHelper();
    final String? savedPin = await dbHelper.getConfig('pin_code');

    await Future.delayed(const Duration(milliseconds: 500));
    if (!mounted) return;

    if (savedPin != null && savedPin.isNotEmpty) {
      // User has already set up the app, jump to Quick PIN Login
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (context) => const PinLoginScreen()),
      );
    } else if (appMode == null) {
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (context) => const ModeSelectionScreen()),
      );
    } else if (appMode == 'Online') {
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (context) => const LoginScreen()),
      );
    } else if (appMode == 'Offline') {
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (context) => const OfflineSetupScreen()),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      backgroundColor: Color(0xFFF4F6F8),
      body: Center(child: CircularProgressIndicator(color: Color(0xFF1A4571))),
    );
  }
}
