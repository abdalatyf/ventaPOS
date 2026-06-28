import 'package:flutter/material.dart';
import 'package:flareline_uikit/components/card/common_card.dart';
import 'package:flareline_uikit/components/forms/outborder_text_form_field.dart';
import 'package:flareline_uikit/core/theme/flareline_colors.dart';
import '../db/database_helper.dart';
import 'create_pin_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _companyCodeCtrl = TextEditingController();
  final _usernameCtrl = TextEditingController();
  final _passwordCtrl = TextEditingController();
  bool _isLoading = false;

  final dbHelper = DatabaseHelper();

  Future<void> _loginOnline() async {
    if (_companyCodeCtrl.text.isEmpty || _usernameCtrl.text.isEmpty || _passwordCtrl.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('برجاء ملء جميع الحقول'), backgroundColor: Colors.red),
      );
      return;
    }

    setState(() => _isLoading = true);

    // Simulate Network Request to Verify Company Code and Credentials
    await Future.delayed(const Duration(seconds: 2));

    String role = _usernameCtrl.text.toLowerCase() == 'manager' ? 'MANAGER' : 'SALESPERSON';
    
    // Save basic auth details
    await dbHelper.setConfig('company_code', _companyCodeCtrl.text);
    await dbHelper.setConfig('branch_id', '1', activeRole: role);
    await dbHelper.setConfig('salesperson_id', '1');

    if (mounted) {
      // Direct to PIN creation screen for future offline quick access
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (context) => const CreatePinScreen()),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF4F6F8),
      body: Center(
        child: SingleChildScrollView(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 24.0),
            child: CommonCard(
              padding: const EdgeInsets.all(32.0),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const Icon(Icons.point_of_sale, size: 64, color: FlarelineColors.primary),
                  const SizedBox(height: 16),
                  const Text(
                    'تسجيل الدخول',
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Color(0xFF111827)),
                  ),
                  const SizedBox(height: 32),
                  OutBorderTextFormField(
                    labelText: 'كود الشركة',
                    hintText: 'أدخل الكود المكون من 4 أرقام',
                    controller: _companyCodeCtrl,
                    keyboardType: TextInputType.number,
                  ),
                  const SizedBox(height: 16),
                  OutBorderTextFormField(
                    labelText: 'اسم المستخدم',
                    hintText: 'أدخل اسم المستخدم',
                    controller: _usernameCtrl,
                  ),
                  const SizedBox(height: 16),
                  OutBorderTextFormField(
                    labelText: 'كلمة المرور',
                    hintText: 'أدخل كلمة المرور',
                    controller: _passwordCtrl,
                    obscureText: true,
                  ),
                  const SizedBox(height: 32),
                  SizedBox(
                    height: 50,
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: FlarelineColors.primary,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                      ),
                      onPressed: _isLoading ? null : _loginOnline,
                      child: _isLoading 
                          ? const SizedBox(width: 24, height: 24, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                          : const Text('دخول', style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
