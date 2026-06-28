import 'package:flutter/material.dart';
import '../db/database_helper.dart';
import 'package:flareline_uikit/components/card/common_card.dart';
import 'package:flareline_uikit/core/theme/flareline_colors.dart';

class SalesReportsScreen extends StatefulWidget {
  const SalesReportsScreen({super.key});

  @override
  State<SalesReportsScreen> createState() => _SalesReportsScreenState();
}

class _SalesReportsScreenState extends State<SalesReportsScreen> {
  int _selectedYear = DateTime.now().year;
  int _selectedMonth = DateTime.now().month;

  int _totalRevenue = 0;
  int _totalExpenses = 0;
  int _netProfit = 0;

  @override
  void initState() {
    super.initState();
    _loadReport();
  }

  Future<void> _loadReport() async {
    final db = await DatabaseHelper.instance.database;

    final revResult = await db.rawQuery('''
      SELECT SUM(total_amount) as s 
      FROM receipts 
      WHERE sale_year = ? AND sale_month = ?
    ''', [_selectedYear, _selectedMonth]);

    final expResult = await db.rawQuery('''
      SELECT SUM(amount) as s 
      FROM expenses 
      WHERE expense_year = ? AND expense_month = ?
    ''', [_selectedYear, _selectedMonth]);

    int rev = (revResult.first['s'] as num?)?.toInt() ?? 0;
    int exp = (expResult.first['s'] as num?)?.toInt() ?? 0;

    setState(() {
      _totalRevenue = rev;
      _totalExpenses = exp;
      _netProfit = rev - exp;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: FlarelineColors.background,
      appBar: AppBar(
        title: const Text('تقرير الأرباح والخسائر'),
        backgroundColor: FlarelineColors.primary,
        foregroundColor: Colors.white,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            CommonCard(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  Expanded(
                    child: DropdownButtonFormField<int>(
                      value: _selectedYear,
                      decoration: const InputDecoration(
                        labelText: 'السنة',
                        border: OutlineInputBorder(borderSide: BorderSide(color: FlarelineColors.border)),
                      ),
                      items: [2024, 2025, 2026, 2027].map((y) => DropdownMenuItem(value: y, child: Text(y.toString()))).toList(),
                      onChanged: (val) {
                        if (val != null) {
                          setState(() => _selectedYear = val);
                          _loadReport();
                        }
                      },
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: DropdownButtonFormField<int>(
                      value: _selectedMonth,
                      decoration: const InputDecoration(
                        labelText: 'الشهر',
                        border: OutlineInputBorder(borderSide: BorderSide(color: FlarelineColors.border)),
                      ),
                      items: List.generate(12, (i) => i + 1).map((m) => DropdownMenuItem(value: m, child: Text(m.toString()))).toList(),
                      onChanged: (val) {
                        if (val != null) {
                          setState(() => _selectedMonth = val);
                          _loadReport();
                        }
                      },
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 32),
            CommonCard(
              padding: const EdgeInsets.all(16),
              child: ListTile(
                leading: CircleAvatar(
                  backgroundColor: Colors.green.withOpacity(0.2),
                  child: const Icon(Icons.arrow_downward, color: Colors.green),
                ),
                title: const Text('إجمالي الإيرادات', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: FlarelineColors.darkBlackText)),
                trailing: Text(_totalRevenue.toString(), style: const TextStyle(fontSize: 24, color: Colors.green, fontWeight: FontWeight.bold)),
              ),
            ),
            const SizedBox(height: 16),
            CommonCard(
              padding: const EdgeInsets.all(16),
              child: ListTile(
                leading: CircleAvatar(
                  backgroundColor: Colors.red.withOpacity(0.2),
                  child: const Icon(Icons.arrow_upward, color: Colors.red),
                ),
                title: const Text('إجمالي المصروفات', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: FlarelineColors.darkBlackText)),
                trailing: Text(_totalExpenses.toString(), style: const TextStyle(fontSize: 24, color: Colors.red, fontWeight: FontWeight.bold)),
              ),
            ),
            const SizedBox(height: 16),
            CommonCard(
              padding: const EdgeInsets.all(16),
              child: ListTile(
                leading: CircleAvatar(
                  backgroundColor: _netProfit >= 0 ? Colors.blue.withOpacity(0.2) : Colors.orange.withOpacity(0.2),
                  child: Icon(_netProfit >= 0 ? Icons.account_balance_wallet : Icons.warning, color: _netProfit >= 0 ? Colors.blue : Colors.orange),
                ),
                title: const Text('صافي الربح', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: FlarelineColors.darkBlackText)),
                trailing: Text(_netProfit.toString(), style: TextStyle(fontSize: 28, color: _netProfit >= 0 ? Colors.blue : Colors.orange, fontWeight: FontWeight.bold)),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
