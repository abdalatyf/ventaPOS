import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import '../db/database_helper.dart';
import 'print_views.dart';

import 'package:flareline_uikit/components/card/common_card.dart';
import 'package:flareline_uikit/components/forms/outborder_text_form_field.dart';
import 'package:flareline_uikit/core/theme/flareline_colors.dart';

class SearchReceiptsScreen extends StatefulWidget {
  const SearchReceiptsScreen({super.key});

  @override
  State<SearchReceiptsScreen> createState() => _SearchReceiptsScreenState();
}

class _SearchReceiptsScreenState extends State<SearchReceiptsScreen> {
  final TextEditingController _searchCtrl = TextEditingController();
  int? _filterYear;
  int? _filterMonth;

  List<Map<String, dynamic>> _receipts = [];

  @override
  void initState() {
    super.initState();
    _loadReceipts();
  }

  Future<void> _loadReceipts() async {
    String q = _searchCtrl.text;

    if (kIsWeb) {
      if (!mounted) return;
      setState(() {
        _receipts = [
          {
            'id': 1, 'receipt_number': 123456, 'customer_name': 'خالد إبراهيم (موك)',
            'total_amount': 8000, 'sale_year': 2024, 'sale_month': 5
          },
          {
            'id': 2, 'receipt_number': 123457, 'customer_name': 'منى أحمد (موك)',
            'total_amount': 15000, 'sale_year': 2024, 'sale_month': 5
          }
        ];
        if (q.isNotEmpty) {
          _receipts = _receipts.where((r) => r['customer_name'].toString().contains(q) || r['receipt_number'].toString().contains(q)).toList();
        }
      });
      return;
    }

    final db = await DatabaseHelper.instance.database;
    
    String where = '1=1';
    List<dynamic> whereArgs = [];

    if (q.isNotEmpty) {
      where += ' AND (customer_name LIKE ? OR receipt_number LIKE ?)';
      whereArgs.add('%$q%');
      whereArgs.add('%$q%');
    }

    if (_filterYear != null) {
      where += ' AND sale_year = ?';
      whereArgs.add(_filterYear);
    }
    if (_filterMonth != null) {
      where += ' AND sale_month = ?';
      whereArgs.add(_filterMonth);
    }

    final data = await db.query('receipts', where: where, whereArgs: whereArgs, orderBy: 'id DESC');
    setState(() {
      _receipts = data;
    });
  }

  Future<void> _showReceiptDetails(int receiptId) async {
    final db = await DatabaseHelper.instance.database;
    final items = await db.query('receipt_items', where: 'receipt_id = ?', whereArgs: [receiptId]);
    final installments = await db.query('installment_payments', where: 'receipt_id = ?', whereArgs: [receiptId]);

    if (!mounted) return;
    
    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('Receipt Details'),
          content: SingleChildScrollView(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Items:', style: TextStyle(fontWeight: FontWeight.bold)),
                ...items.map((e) => Text("Product ID: ${e['inventory_item_id']} | Qty: ${e['quantity']} | Price: ${e['unit_price']}")),
                const SizedBox(height: 16),
                const Text('Installments:', style: TextStyle(fontWeight: FontWeight.bold)),
                if (installments.isEmpty) const Text("No installments (Cash Sale)"),
                ...installments.map((e) => Text("Date: ${e['payment_date']} | Amount: ${e['amount']}")),
              ],
            ),
          ),
          actions: [
            ElevatedButton.icon(
              icon: const Icon(Icons.print),
              label: const Text('Print A4'),
              onPressed: () {
                Navigator.pop(context); // Close dialog
                Navigator.push(context, MaterialPageRoute(builder: (_) => ReceiptPrintScreen(receiptId: receiptId)));
              },
            ),
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('إغلاق'),
            ),
          ],
        );
      }
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF4F6F8),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: CommonCard(
              title: 'البحث والفلترة',
              child: Column(
                children: [
                  OutBorderTextFormField(
                    controller: _searchCtrl,
                    labelText: 'ابحث بالاسم أو رقم الفاتورة',
                    hintText: 'اكتب للبحث...',
                    onChanged: (val) => _loadReceipts(),
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      Expanded(
                        child: DropdownButtonFormField<int?>(
                          decoration: const InputDecoration(
                            labelText: 'السنة',
                            border: OutlineInputBorder(borderSide: BorderSide(color: FlarelineColors.border, width: 1)),
                            enabledBorder: OutlineInputBorder(borderSide: BorderSide(color: FlarelineColors.border, width: 1)),
                            contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                          ),
                          value: _filterYear,
                          items: [null, 2024, 2025, 2026, 2027].map((y) => DropdownMenuItem(value: y, child: Text(y == null ? 'الكل' : y.toString()))).toList(),
                          onChanged: (val) {
                            setState(() => _filterYear = val);
                            _loadReceipts();
                          },
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: DropdownButtonFormField<int?>(
                          decoration: const InputDecoration(
                            labelText: 'الشهر',
                            border: OutlineInputBorder(borderSide: BorderSide(color: FlarelineColors.border, width: 1)),
                            enabledBorder: OutlineInputBorder(borderSide: BorderSide(color: FlarelineColors.border, width: 1)),
                            contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                          ),
                          value: _filterMonth,
                          items: [null, ...List.generate(12, (i) => i + 1)].map((m) => DropdownMenuItem(value: m, child: Text(m == null ? 'الكل' : m.toString()))).toList(),
                          onChanged: (val) {
                            setState(() => _filterMonth = val);
                            _loadReceipts();
                          },
                        ),
                      ),
                    ],
                  )
                ],
              ),
            ),
          ),
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              itemCount: _receipts.length,
              itemBuilder: (context, index) {
                final r = _receipts[index];
                return Card(
                  margin: const EdgeInsets.only(bottom: 12),
                  elevation: 1,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                  child: ListTile(
                    contentPadding: const EdgeInsets.all(16),
                    leading: CircleAvatar(
                      backgroundColor: FlarelineColors.primary.withOpacity(0.1),
                      child: const Icon(Icons.receipt_long, color: FlarelineColors.primary),
                    ),
                    title: Text('فاتورة #${r['receipt_number']} - ${r['customer_name']}', style: const TextStyle(fontWeight: FontWeight.bold)),
                    subtitle: Text('الإجمالي: ${r['total_amount']} ج.م | التاريخ: ${r['sale_month']}/${r['sale_year']}'),
                    trailing: ElevatedButton(
                      style: ElevatedButton.styleFrom(backgroundColor: FlarelineColors.primary),
                      onPressed: () => _showReceiptDetails(r['id']),
                      child: const Text('التفاصيل', style: TextStyle(color: Colors.white)),
                    ),
                  ),
                );
              },
            ),
          )
        ],
      ),
    );
  }
}
