import 'package:flutter/material.dart';
import 'package:flareline_uikit/components/card/common_card.dart';
import 'package:flareline_uikit/core/theme/flareline_colors.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'login_screen.dart';
import 'offline_setup_screen.dart';

class ModeSelectionScreen extends StatelessWidget {
  const ModeSelectionScreen({super.key});

  Future<void> _selectMode(BuildContext context, String mode) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('app_mode', mode);

    if (!context.mounted) return;

    if (mode == 'Online') {
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (context) => const LoginScreen()),
      );
    } else {
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (context) => const OfflineSetupScreen()),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF4F6F8),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24.0),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const Icon(Icons.point_of_sale, size: 80, color: FlarelineColors.primary),
                  const SizedBox(height: 24),
                  const Text(
                    'مرحباً بك في VentaPOS',
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: Color(0xFF111827)),
                  ),
                  const SizedBox(height: 48),
                  
                  _buildModeCard(
                    context,
                    title: 'أونلاين',
                    icon: Icons.wifi,
                    mode: 'Online',
                    color: FlarelineColors.primary,
                  ),
                  const SizedBox(height: 24),
                  _buildModeCard(
                    context,
                    title: 'أوفلاين',
                    icon: Icons.wifi_off,
                    mode: 'Offline',
                    color: const Color(0xFF1DA068),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildModeCard(BuildContext context, {required String title, required IconData icon, required String mode, required Color color}) {
    return GestureDetector(
      onTap: () => _selectMode(context, mode),
      child: CommonCard(
        padding: const EdgeInsets.all(32.0),
        child: Column(
          children: [
            Icon(icon, size: 64, color: color),
            const SizedBox(height: 16),
            Text(
              title,
              style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Color(0xFF111827)),
            ),
          ],
        ),
      ),
    );
  }
}
