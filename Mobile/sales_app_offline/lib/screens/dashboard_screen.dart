import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import '../db/database_helper.dart';
import 'package:flareline_uikit/components/card/common_card.dart';
import 'package:flareline_uikit/core/theme/flareline_colors.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  int totalCashInflow = 0;
  int netCashInHand = 0;
  int inventoryValue = 0;

  List<Map<String, dynamic>> teamPerformance = [];
  List<Map<String, dynamic>> topProducts = [];

  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    if (kIsWeb) {
      if (mounted) {
        setState(() {
          totalCashInflow = 15000;
          netCashInHand = 12000;
          inventoryValue = 50000;
          teamPerformance = [
            {'name': 'أحمد محمود', 'cash_sales': 5000, 'total_sales': 7000},
            {'name': 'محمد علي', 'cash_sales': 2000, 'total_sales': 3000},
          ];
          topProducts = [
            {'name': 'شاشة سامسونج', 'sold_qty': 15},
            {'name': 'لابتوب ديل', 'sold_qty': 8},
          ];
          _isLoading = false;
        });
      }
      return;
    }

    try {
      final db = await DatabaseHelper.instance.database;

      // 1. Total Cash Inflow
      final cashSales = await db.rawQuery('SELECT SUM(total_amount) as s FROM receipts WHERE is_cash_sale = 1');
      final downPayments = await db.rawQuery('SELECT SUM(down_payment) as s FROM receipts WHERE is_cash_sale = 0');
      int cash = (cashSales.first['s'] as num?)?.toInt() ?? 0;
      int down = (downPayments.first['s'] as num?)?.toInt() ?? 0;
      int totalIn = cash + down;

      // 2. Expenses
      final exp = await db.rawQuery('SELECT SUM(amount) as s FROM expenses');
      int totalExp = (exp.first['s'] as num?)?.toInt() ?? 0;

      // 3. Inventory Value
      final inv = await db.rawQuery('SELECT SUM(initial_quantity * initial_purchase_price) as s FROM inventory');
      int invVal = (inv.first['s'] as num?)?.toInt() ?? 0;

      // 4. Team Performance
      final team = await db.rawQuery('''
        SELECT s.name, 
          SUM(CASE WHEN r.is_cash_sale = 1 THEN r.total_amount ELSE 0 END) as cash_sales,
          SUM(r.total_amount) as total_sales
        FROM salespersons s
        LEFT JOIN receipts r ON s.id = r.salesperson_id
        GROUP BY s.id, s.name
      ''');

      // 5. Top Products (By Quantity Sold)
      final topP = await db.rawQuery('''
        SELECT i.name, SUM(ri.quantity) as sold_qty
        FROM inventory i
        JOIN receipt_items ri ON i.id = ri.inventory_item_id
        GROUP BY i.id, i.name
        ORDER BY sold_qty DESC
        LIMIT 5
      ''');

      if (mounted) {
        setState(() {
          totalCashInflow = totalIn;
          netCashInHand = totalIn - totalExp;
          inventoryValue = invVal;
          teamPerformance = team;
          topProducts = topP;
        });
      }
    } catch (e) {
      debugPrint('Error loading dashboard data: $e');
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    return Scaffold(
      backgroundColor: const Color(0xFFF4F6F8),
      body: RefreshIndicator(
        onRefresh: _loadData,
        color: FlarelineColors.primary,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            const Text('مؤشرات الأداء الرئيسية (KPIs)', style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: FlarelineColors.darkBlackText)),
            const SizedBox(height: 16),
            Column(
              children: [
                Row(
                  children: [
                    _buildKpiCard('النقدية الواردة', totalCashInflow.toString(), ButtonColors.success, Icons.monetization_on),
                    const SizedBox(width: 12),
                    _buildKpiCard('صافي الخزنة', netCashInHand.toString(), ButtonColors.primary, Icons.account_balance_wallet),
                  ],
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    _buildKpiCard('قيمة المخزون', inventoryValue.toString(), ButtonColors.warn, Icons.inventory),
                  ],
                ),
              ],
            ),
            const SizedBox(height: 32),
            const Text('أداء المندوبين', style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: FlarelineColors.darkBlackText)),
            const SizedBox(height: 10),
            CommonCard(
              child: SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: DataTable(
                  headingRowColor: WidgetStateProperty.resolveWith<Color?>((Set<WidgetState> states) {
                    return FlarelineColors.gray;
                  }),
                  columns: const [
                    DataColumn(label: Text('المندوب', style: TextStyle(fontWeight: FontWeight.bold, color: FlarelineColors.darkBlackText))),
                    DataColumn(label: Text('مبيعات كاش', style: TextStyle(fontWeight: FontWeight.bold, color: FlarelineColors.darkBlackText))),
                    DataColumn(label: Text('إجمالي المبيعات', style: TextStyle(fontWeight: FontWeight.bold, color: FlarelineColors.darkBlackText))),
                  ],
                  rows: teamPerformance.map((t) => DataRow(cells: [
                    DataCell(Text(t['name'].toString(), style: const TextStyle(color: FlarelineColors.darkBlackText))),
                    DataCell(Text('${t['cash_sales'] ?? 0} ج.م', style: const TextStyle(color: ButtonColors.success, fontWeight: FontWeight.bold))),
                    DataCell(Text('${t['total_sales'] ?? 0} ج.م', style: const TextStyle(color: FlarelineColors.darkBlackText))),
                  ])).toList(),
                ),
              ),
            ),
            const SizedBox(height: 32),
            const Text('الأصناف الأكثر مبيعاً', style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: FlarelineColors.darkBlackText)),
            const SizedBox(height: 10),
            CommonCard(
              child: Column(
                children: topProducts.map((p) => ListTile(
                  leading: CircleAvatar(
                    backgroundColor: ButtonColors.warn.withOpacity(0.2),
                    child: const Icon(Icons.star, color: ButtonColors.warn),
                  ),
                  title: Text(p['name'].toString(), style: const TextStyle(fontWeight: FontWeight.bold, color: FlarelineColors.darkBlackText)),
                  trailing: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(
                      color: ButtonColors.primary.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text('الكمية المباعة: ${p['sold_qty']}', style: const TextStyle(color: ButtonColors.primary, fontWeight: FontWeight.bold)),
                  ),
                )).toList(),
              ),
            ),
            const SizedBox(height: 40),
          ],
        ),
      ),
    );
  }

  Widget _buildKpiCard(String title, String val, Color c, IconData icon) {
    return Expanded(
      child: CommonCard(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(child: Text(title, style: const TextStyle(fontWeight: FontWeight.bold, color: FlarelineColors.darkTextBody, fontSize: 14))),
                Icon(icon, color: c, size: 28),
              ],
            ),
            const SizedBox(height: 16),
            Text('$val ج.م', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: FlarelineColors.darkBlackText)),
          ],
        ),
      ),
    );
  }
}
