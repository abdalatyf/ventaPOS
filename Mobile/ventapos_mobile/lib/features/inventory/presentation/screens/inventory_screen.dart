import 'package:flutter/material.dart';
import '../../../../core/widgets/app_drawer.dart';

class InventoryScreen extends StatelessWidget {
  const InventoryScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      drawer: const AppDrawer(),
      appBar: AppBar(
        title: const Text('المنتجات', style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.blue.shade700,
        foregroundColor: Colors.white,
      ),
      body: const Center(
        child: Text('شاشة إدارة المنتجات - سيتم برمجتها لاحقاً', style: TextStyle(fontSize: 18)),
      ),
    );
  }
}
