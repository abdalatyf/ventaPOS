import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class AppDrawer extends StatelessWidget {
  const AppDrawer({super.key});

  @override
  Widget build(BuildContext context) {
    // Get the current location to highlight the active drawer item
    final String location = GoRouterState.of(context).uri.path;

    return Drawer(
      child: Directionality(
        textDirection: TextDirection.rtl,
        child: Column(
          children: [
            DrawerHeader(
              decoration: BoxDecoration(
                color: Colors.blue.shade700,
              ),
              child: const SizedBox(
                width: double.infinity,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisAlignment: MainAxisAlignment.end,
                  children: [
                    Text(
                      'VentaPOS',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    SizedBox(height: 8),
                    Text(
                      'نظام نقاط البيع وإدارة المخازن',
                      style: TextStyle(
                        color: Colors.white70,
                        fontSize: 14,
                      ),
                    ),
                  ],
                ),
              ),
            ),
            
            // 1. Sales Ledger
            ListTile(
              leading: const Icon(Icons.receipt_long),
              title: const Text('المبيعات والفواتير', style: TextStyle(fontWeight: FontWeight.bold)),
              selected: location.startsWith('/receipts'),
              selectedColor: Colors.blue.shade700,
              selectedTileColor: Colors.blue.shade50,
              onTap: () {
                Navigator.pop(context); // Close drawer
                context.go('/receipts');
              },
            ),
            
            // 2. Purchases & Expenses (Manager Only ideally)
            ListTile(
              leading: const Icon(Icons.money_off),
              title: const Text('المشتريات والمصروفات', style: TextStyle(fontWeight: FontWeight.bold)),
              selected: location.startsWith('/purchases'), // Placeholder
              selectedColor: Colors.blue.shade700,
              selectedTileColor: Colors.blue.shade50,
              onTap: () {
                Navigator.pop(context);
                // context.go('/purchases');
              },
            ),

            const Divider(),
            
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
              child: Align(
                alignment: Alignment.centerRight,
                child: Text('الإدارة (المزيد)', style: TextStyle(color: Colors.grey, fontWeight: FontWeight.bold)),
              ),
            ),

            // 3. Setup / Administration (Inventory etc)
            ListTile(
              leading: const Icon(Icons.inventory_2_outlined),
              title: const Text('المنتجات (الإدارة)'),
              selected: location.startsWith('/inventory'),
              selectedColor: Colors.blue.shade700,
              selectedTileColor: Colors.blue.shade50,
              onTap: () {
                Navigator.pop(context);
                context.go('/inventory');
              },
            ),

            // 4. Reports
            ListTile(
              leading: const Icon(Icons.bar_chart),
              title: const Text('التقارير'),
              selected: location.startsWith('/reports'), // Placeholder
              selectedColor: Colors.blue.shade700,
              selectedTileColor: Colors.blue.shade50,
              onTap: () {
                Navigator.pop(context);
                // context.go('/reports');
              },
            ),

            // 5. Setup (New feature)
            ListTile(
              leading: const Icon(Icons.settings),
              title: const Text('التأسيس'),
              selected: location.startsWith('/setup'),
              selectedColor: Colors.blue.shade700,
              selectedTileColor: Colors.blue.shade50,
              onTap: () {
                Navigator.pop(context);
                context.go('/setup');
              },
            ),

            // 5. Sync
            ListTile(
              leading: const Icon(Icons.sync),
              title: const Text('المزامنة والطابعات'),
              selected: location.startsWith('/sync'),
              selectedColor: Colors.blue.shade700,
              selectedTileColor: Colors.blue.shade50,
              onTap: () {
                Navigator.pop(context);
                context.go('/sync');
              },
            ),

            const Spacer(),
            const Divider(),
            ListTile(
              leading: const Icon(Icons.logout, color: Colors.red),
              title: const Text('تسجيل الخروج', style: TextStyle(color: Colors.red)),
              onTap: () {
                // Logout logic
              },
            ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }
}
