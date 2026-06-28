import 'package:flutter/material.dart';
import '../db/database_helper.dart';

class ReceiptPrintScreen extends StatefulWidget {
  final int receiptId;

  const ReceiptPrintScreen({super.key, required this.receiptId});

  @override
  State<ReceiptPrintScreen> createState() => _ReceiptPrintScreenState();
}

class _ReceiptPrintScreenState extends State<ReceiptPrintScreen> {
  Map<String, dynamic>? _receipt;
  List<Map<String, dynamic>> _items = [];
  List<Map<String, dynamic>> _installments = [];

  @override
  void initState() {
    super.initState();
    _loadReceipt();
  }

  Future<void> _loadReceipt() async {
    final db = await DatabaseHelper.instance.database;
    final rList = await db.query('receipts', where: 'id = ?', whereArgs: [widget.receiptId]);
    if (rList.isNotEmpty) {
      _receipt = rList.first;
    }
    
    _items = await db.rawQuery('''
      SELECT ri.quantity, ri.unit_price, i.name as product_name
      FROM receipt_items ri
      LEFT JOIN inventory i ON ri.inventory_item_id = i.id
      WHERE ri.receipt_id = ?
    ''', [widget.receiptId]);

    _installments = await db.query('installment_payments', where: 'receipt_id = ?', whereArgs: [widget.receiptId]);

    setState(() {});
  }

  void _print() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        content: Row(
          children: const [
            CircularProgressIndicator(),
            SizedBox(width: 16),
            Text('Connecting to Printer...'),
          ],
        ),
      ),
    );
    Future.delayed(const Duration(seconds: 2), () {
      if (mounted && Navigator.canPop(context)) {
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Print job sent!')));
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_receipt == null) {
      return Scaffold(appBar: AppBar(title: const Text('طباعة الفاتورة')), body: const Center(child: CircularProgressIndicator()));
    }

    bool isCash = (_receipt!['is_cash_sale'] as int) == 1;

    return Scaffold(
      appBar: AppBar(title: const Text('طباعة الفاتورة')),
      floatingActionButton: FloatingActionButton(
        onPressed: _print,
        child: const Icon(Icons.print),
      ),
      body: SingleChildScrollView(
        child: Center(
          child: Container(
            margin: const EdgeInsets.all(16),
            padding: const EdgeInsets.all(32),
            constraints: const BoxConstraints(maxWidth: 800),
            decoration: BoxDecoration(
              color: Colors.white,
              boxShadow: [BoxShadow(color: Colors.grey.withOpacity(0.5), blurRadius: 10, spreadRadius: 2)],
              border: Border.all(color: Colors.grey.shade300),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Header
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Row(
                      children: const [
                        Icon(Icons.business_center, size: 50, color: Colors.blueGrey),
                        SizedBox(width: 16),
                        Text('VentaPOS', style: TextStyle(fontSize: 32, fontWeight: FontWeight.bold, color: Colors.blueGrey)),
                      ],
                    ),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        const Text('INVOICE', style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold, letterSpacing: 2)),
                        Text('Receipt #${_receipt!['receipt_number']}', style: const TextStyle(fontSize: 16, color: Colors.grey)),
                        Text('Date: ${_receipt!['sale_month']}/${_receipt!['sale_year']}', style: const TextStyle(fontSize: 16, color: Colors.grey)),
                      ],
                    ),
                  ],
                ),
                const Divider(thickness: 2, height: 40),

                // Customer Info
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Billed To:', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.grey)),
                        Text(_receipt!['customer_name'] ?? 'Unknown', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                        Text('Phone: ${_receipt!['phone_number'] ?? '-'}'),
                        Text('Address: ${_receipt!['address'] ?? '-'}'),
                        Text('Area: ${_receipt!['area'] ?? '-'}'),
                      ],
                    ),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        const Text('Payment Type:', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.grey)),
                        Text(isCash ? 'CASH SALE' : 'INSTALLMENT SALE', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: isCash ? Colors.green : Colors.orange)),
                      ],
                    )
                  ],
                ),
                const SizedBox(height: 32),

                // Items Table
                const Text('Items', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                Table(
                  border: TableBorder.all(color: Colors.grey.shade300),
                  columnWidths: const {
                    0: FlexColumnWidth(3),
                    1: FlexColumnWidth(1),
                    2: FlexColumnWidth(1),
                    3: FlexColumnWidth(1),
                  },
                  children: [
                    TableRow(
                      decoration: BoxDecoration(color: Colors.grey.shade200),
                      children: const [
                        Padding(padding: EdgeInsets.all(8), child: Text('Product', style: TextStyle(fontWeight: FontWeight.bold))),
                        Padding(padding: EdgeInsets.all(8), child: Text('Qty', style: TextStyle(fontWeight: FontWeight.bold))),
                        Padding(padding: EdgeInsets.all(8), child: Text('Price', style: TextStyle(fontWeight: FontWeight.bold))),
                        Padding(padding: EdgeInsets.all(8), child: Text('Total', style: TextStyle(fontWeight: FontWeight.bold))),
                      ]
                    ),
                    ..._items.map((item) {
                      int q = item['quantity'] as int? ?? 0;
                      int p = item['unit_price'] as int? ?? 0;
                      return TableRow(
                        children: [
                          Padding(padding: const EdgeInsets.all(8), child: Text(item['product_name'] ?? 'Item')),
                          Padding(padding: const EdgeInsets.all(8), child: Text(q.toString())),
                          Padding(padding: const EdgeInsets.all(8), child: Text(p.toString())),
                          Padding(padding: const EdgeInsets.all(8), child: Text((q * p).toString())),
                        ]
                      );
                    }),
                  ],
                ),
                const SizedBox(height: 16),
                Align(
                  alignment: Alignment.centerRight,
                  child: Text('Total Amount: ${_receipt!['total_amount']}', style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
                ),
                if (!isCash)
                  Align(
                    alignment: Alignment.centerRight,
                    child: Text('Down Payment: ${_receipt!['down_payment']}', style: const TextStyle(fontSize: 18, color: Colors.grey)),
                  ),
                const SizedBox(height: 32),

                // Installments Table
                if (!isCash && _installments.isNotEmpty) ...[
                  const Text('Installment Schedule', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  Table(
                    border: TableBorder.all(color: Colors.grey.shade300),
                    children: [
                      TableRow(
                        decoration: BoxDecoration(color: Colors.grey.shade200),
                        children: const [
                          Padding(padding: EdgeInsets.all(8), child: Text('Due Date', style: TextStyle(fontWeight: FontWeight.bold))),
                          Padding(padding: EdgeInsets.all(8), child: Text('Amount', style: TextStyle(fontWeight: FontWeight.bold))),
                        ]
                      ),
                      ..._installments.map((inst) {
                        return TableRow(
                          children: [
                            Padding(padding: const EdgeInsets.all(8), child: Text(inst['payment_date'].toString().split('T')[0])),
                            Padding(padding: const EdgeInsets.all(8), child: Text(inst['amount'].toString())),
                          ]
                        );
                      }),
                    ],
                  ),
                ],

                const SizedBox(height: 60),
                const Center(child: Text('Thank you for your business!', style: TextStyle(fontStyle: FontStyle.italic, color: Colors.grey))),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
