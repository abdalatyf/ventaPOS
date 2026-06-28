import 'package:flutter/material.dart';
import 'package:flareline_uikit/components/card/common_card.dart';
import 'package:flareline_uikit/core/theme/flareline_colors.dart';
import '../db/database_helper.dart';
import 'main_layout.dart';

class CreatePinScreen extends StatefulWidget {
  const CreatePinScreen({super.key});

  @override
  State<CreatePinScreen> createState() => _CreatePinScreenState();
}

class _CreatePinScreenState extends State<CreatePinScreen> {
  String _pin = '';
  final dbHelper = DatabaseHelper();

  void _onDigitPressed(String digit) {
    if (_pin.length < 4) {
      setState(() {
        _pin += digit;
      });
    }
  }

  void _onBackspace() {
    if (_pin.isNotEmpty) {
      setState(() {
        _pin = _pin.substring(0, _pin.length - 1);
      });
    }
  }

  Future<void> _savePin() async {
    if (_pin.length == 4) {
      await dbHelper.setConfig('pin_code', _pin);
      if (mounted) {
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(builder: (context) => const MainLayout()),
        );
      }
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
              padding: const EdgeInsets.all(24.0),
              child: CommonCard(
                padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 40),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.lock_outline, size: 64, color: FlarelineColors.primary),
                    const SizedBox(height: 16),
                    const Text(
                      'إعداد الرمز السري',
                      style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Color(0xFF111827)),
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      'برجاء إدخال رمز مكون من 4 أرقام للدخول السريع لاحقاً',
                      textAlign: TextAlign.center,
                      style: TextStyle(fontSize: 14, color: Color(0xFF4B5563)),
                    ),
                    const SizedBox(height: 32),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: List.generate(4, (index) {
                        return Container(
                          margin: const EdgeInsets.symmetric(horizontal: 8),
                          width: 24,
                          height: 24,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: index < _pin.length ? FlarelineColors.primary : Colors.grey[300],
                          ),
                        );
                      }),
                    ),
                    const SizedBox(height: 40),
                    _buildNumpad(),
                    const SizedBox(height: 24),
                    SizedBox(
                      width: double.infinity,
                      height: 50,
                      child: ElevatedButton(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: FlarelineColors.primary,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                        ),
                        onPressed: _pin.length == 4 ? _savePin : null,
                        child: const Text('حفظ الرمز السري', style: TextStyle(color: Colors.white, fontSize: 16)),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildNumpad() {
    return Column(
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
          children: ['1', '2', '3'].map((e) => _numButton(e)).toList(),
        ),
        const SizedBox(height: 16),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
          children: ['4', '5', '6'].map((e) => _numButton(e)).toList(),
        ),
        const SizedBox(height: 16),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
          children: ['7', '8', '9'].map((e) => _numButton(e)).toList(),
        ),
        const SizedBox(height: 16),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
          children: [
            const SizedBox(width: 64, height: 64), // placeholder
            _numButton('0'),
            GestureDetector(
              onTap: _onBackspace,
              child: Container(
                width: 64,
                height: 64,
                decoration: BoxDecoration(shape: BoxShape.circle, color: Colors.red[50]),
                child: const Center(child: Icon(Icons.backspace, color: Colors.red)),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _numButton(String digit) {
    return GestureDetector(
      onTap: () => _onDigitPressed(digit),
      child: Container(
        width: 64,
        height: 64,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: Colors.grey[100],
        ),
        child: Center(
          child: Text(
            digit,
            style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Color(0xFF111827)),
          ),
        ),
      ),
    );
  }
}
