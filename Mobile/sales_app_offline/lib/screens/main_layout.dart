import 'package:flutter/material.dart';
import 'package:flareline_uikit/core/theme/flareline_colors.dart';
import 'add_receipt_screen.dart';
import 'search_receipts_screen.dart';
import 'manage_products_screen.dart';
import 'manage_branches_screen.dart';
import 'manage_users_screen.dart';
import 'manage_suppliers_screen.dart';
import 'manage_purchase_invoices_screen.dart';
import 'expenses_screen.dart';
import 'dashboard_screen.dart';
import 'product_ledger_screen.dart';
import 'sales_reports_screen.dart';
import 'sync_hub_screen.dart';

class MainLayout extends StatefulWidget {
  const MainLayout({super.key});

  @override
  State<MainLayout> createState() => _MainLayoutState();
}

class _MainLayoutState extends State<MainLayout> {
  Widget _currentBody = const DashboardScreen();
  String _currentTitle = 'لوحة القيادة';

  void _navigate(Widget screen, String title) {
    setState(() {
      _currentBody = screen;
      _currentTitle = title;
    });
    Navigator.pop(context); // Close the drawer
  }

  Widget _buildNavItem(String title, IconData icon, Widget screen) {
    bool isSelected = _currentTitle == title;
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      decoration: BoxDecoration(
        color: isSelected ? FlarelineColors.primary : Colors.transparent,
        borderRadius: BorderRadius.circular(8),
      ),
      child: ListTile(
        leading: Icon(icon, color: isSelected ? Colors.white : Colors.white70),
        title: Text(title, style: TextStyle(color: isSelected ? Colors.white : Colors.white70)),
        onTap: () => _navigate(screen, title),
      ),
    );
  }

  Widget _buildExpansionTile(String title, IconData icon, List<Widget> children) {
    return ExpansionTile(
      title: Text(title, style: const TextStyle(color: Colors.white70)),
      leading: Icon(icon, color: Colors.white70),
      iconColor: Colors.white,
      collapsedIconColor: Colors.white70,
      childrenPadding: const EdgeInsets.only(right: 16),
      children: children,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_currentTitle, style: const TextStyle(fontWeight: FontWeight.bold, color: FlarelineColors.darkBlackText)),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: FlarelineColors.darkBlackText),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1.0),
          child: Container(color: FlarelineColors.border, height: 1.0),
        ),
      ),
      drawer: Drawer(
        backgroundColor: FlarelineColors.darkBackground,
        child: ListView(
          padding: EdgeInsets.zero,
          children: [
            const DrawerHeader(
              decoration: BoxDecoration(color: FlarelineColors.darkBackground),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  Icon(Icons.point_of_sale, color: Colors.white, size: 40),
                  SizedBox(height: 10),
                  Text('VentaPOS PRO', style: TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold)),
                ],
              ),
            ),
            _buildExpansionTile('المبيعات', Icons.shopping_cart, [
              _buildNavItem('لوحة القيادة', Icons.dashboard, const DashboardScreen()),
              _buildNavItem('إضافة فاتورة', Icons.add_shopping_cart, const AddReceiptScreen()),
              _buildNavItem('البحث في الفواتير', Icons.search, const SearchReceiptsScreen()),
            ]),
            _buildExpansionTile('التأسيس والإدارة', Icons.business, [
              _buildNavItem('إدارة المنتجات', Icons.inventory, const ManageProductsScreen()),
              _buildNavItem('إدارة الفروع', Icons.store, const ManageBranchesScreen()),
              _buildNavItem('المستخدمين', Icons.people, const ManageUsersScreen()),
            ]),
            _buildExpansionTile('المشتريات والمصروفات', Icons.account_balance_wallet, [
              _buildNavItem('الموردين', Icons.local_shipping, const ManageSuppliersScreen()),
              _buildNavItem('المشتريات', Icons.shopping_bag, const PurchasesScreen()),
              _buildNavItem('المصروفات', Icons.money_off, const ExpensesScreen()),
            ]),
            _buildExpansionTile('التقارير والتحليلات', Icons.bar_chart, [
              _buildNavItem('التقارير (P&L)', Icons.analytics, const SalesReportsScreen()),
              _buildNavItem('حركة المنتج', Icons.history, const ProductLedgerScreen()),
            ]),
            _buildExpansionTile('الأدوات', Icons.build, [
              _buildNavItem('مركز المزامنة', Icons.sync, const SyncHubScreen()),
            ]),
          ],
        ),
      ),
      body: Container(
        color: const Color(0xFFF4F6F8), // Match add receipt screen bg
        child: _currentBody,
      ),
    );
  }
}
