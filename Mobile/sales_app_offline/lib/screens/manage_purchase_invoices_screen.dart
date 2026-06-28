import 'package:flutter/material.dart';
import '../db/database_helper.dart';
import 'package:flareline_uikit/components/card/common_card.dart';
import 'package:flareline_uikit/components/forms/outborder_text_form_field.dart';
import 'package:flareline_uikit/core/theme/flareline_colors.dart';

class PurchasesScreen extends StatefulWidget {
  const PurchasesScreen({super.key});

  @override
  State<PurchasesScreen> createState() => _PurchasesScreenState();
}

class _PurchasesScreenState extends State<PurchasesScreen> {
  final _formKey = GlobalKey<FormState>();

  int _invoiceNumber = 1;
  String _invoiceType = 'PURCHASE';
  int _supplierId = 1;
  int _inventoryItemId = 1;
  int _quantity = 1;
  int _purchasePrice = 0;
  
  List<Map<String, dynamic>> _invoices = [];
  List<Map<String, dynamic>> _suppliers = [];
  List<Map<String, dynamic>> _products = [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final db = await DatabaseHelper.instance.database;
    final data = await db.rawQuery('''
      SELECT p.id, p.invoice_number, p.invoice_type, p.invoice_month, p.invoice_year, pi.quantity, pi.purchase_price, s.name as supplier_name, i.name as product_name
      FROM purchase_invoices p 
      LEFT JOIN purchase_invoice_items pi ON p.id = pi.invoice_id
      LEFT JOIN suppliers s ON p.supplier_id = s.id
      LEFT JOIN inventory i ON pi.inventory_item_id = i.id
      ORDER BY p.id DESC
    ''');
    
    final suppliers = await db.query('suppliers');
    final products = await db.query('inventory');

    if (mounted) {
      setState(() {
        _invoices = data;
        _suppliers = suppliers;
        _products = products;
        if (suppliers.isNotEmpty) _supplierId = suppliers.first['id'] as int;
        if (products.isNotEmpty) _inventoryItemId = products.first['id'] as int;
      });
    }
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    _formKey.currentState!.save();

    final db = await DatabaseHelper.instance.database;
    
    await db.transaction((txn) async {
      int invId = await txn.insert('purchase_invoices', {
        'invoice_number': _invoiceNumber,
        'invoice_month': DateTime.now().month,
        'invoice_year': DateTime.now().year,
        'invoice_type': _invoiceType,
        'supplier_id': _supplierId,
        'is_synced': 0
      });

      await txn.insert('purchase_invoice_items', {
        'invoice_id': invId,
        'inventory_item_id': _inventoryItemId,
        'quantity': _quantity,
        'purchase_price': _purchasePrice,
        'is_synced': 0
      });
      
      // Update inventory directly
      // In Django, saving purchase updates stock. PURCHASE increases, RETURN decreases.
      final oldProduct = await txn.query('inventory', where: 'id = ?', whereArgs: [_inventoryItemId], limit: 1);
      if (oldProduct.isNotEmpty) {
         int currentQty = oldProduct.first['initial_quantity'] as int;
         int newQty = _invoiceType == 'PURCHASE' ? currentQty + _quantity : currentQty - _quantity;
         await txn.update('inventory', {'initial_quantity': newQty, 'is_synced': 0}, where: 'id = ?', whereArgs: [_inventoryItemId]);
      }
    });

    _load();
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('تم إضافة الفاتورة بنجاح')));
    }
  }

  void _showForm() {
    showDialog(
      context: context,
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setModalState) {
            return AlertDialog(
              title: const Text('إضافة فاتورة مشتريات', style: TextStyle(fontWeight: FontWeight.bold, color: FlarelineColors.darkBlackText)),
              content: SingleChildScrollView(
                child: Form(
                  key: _formKey,
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      OutBorderTextFormField(
                        labelText: 'رقم الفاتورة',
                        keyboardType: TextInputType.number,
                        initialValue: _invoiceNumber.toString(),
                        onSaved: (val) => _invoiceNumber = int.tryParse(val!) ?? 1,
                        validator: (val) => val == null || val.isEmpty ? 'مطلوب' : null,
                      ),
                      const SizedBox(height: 12),
                      DropdownButtonFormField<String>(
                        value: _invoiceType,
                        items: const [
                          DropdownMenuItem(value: 'PURCHASE', child: Text('مشتريات (دخول للمخزن)')),
                          DropdownMenuItem(value: 'RETURN', child: Text('مرتجع (خروج من المخزن)')),
                        ],
                        onChanged: (val) => setModalState(() => _invoiceType = val!),
                        decoration: const InputDecoration(
                          labelText: 'النوع',
                          border: OutlineInputBorder(borderSide: BorderSide(color: FlarelineColors.border)),
                        ),
                      ),
                      const SizedBox(height: 12),
                      DropdownButtonFormField<int>(
                        value: _suppliers.any((s) => s['id'] == _supplierId) ? _supplierId : null,
                        items: _suppliers.map((s) => DropdownMenuItem<int>(
                          value: s['id'] as int,
                          child: Text(s['name'] as String),
                        )).toList(),
                        onChanged: (val) => setModalState(() => _supplierId = val!),
                        decoration: const InputDecoration(
                          labelText: 'المورد',
                          border: OutlineInputBorder(borderSide: BorderSide(color: FlarelineColors.border)),
                        ),
                      ),
                      const SizedBox(height: 12),
                      DropdownButtonFormField<int>(
                        value: _products.any((p) => p['id'] == _inventoryItemId) ? _inventoryItemId : null,
                        items: _products.map((p) => DropdownMenuItem<int>(
                          value: p['id'] as int,
                          child: Text(p['name'] as String),
                        )).toList(),
                        onChanged: (val) => setModalState(() => _inventoryItemId = val!),
                        decoration: const InputDecoration(
                          labelText: 'الصنف',
                          border: OutlineInputBorder(borderSide: BorderSide(color: FlarelineColors.border)),
                        ),
                      ),
                      const SizedBox(height: 12),
                      OutBorderTextFormField(
                        labelText: 'الكمية',
                        keyboardType: TextInputType.number,
                        initialValue: _quantity.toString(),
                        onSaved: (val) => _quantity = int.tryParse(val!) ?? 1,
                        validator: (val) => val == null || val.isEmpty ? 'مطلوب' : null,
                      ),
                      const SizedBox(height: 12),
                      OutBorderTextFormField(
                        labelText: 'سعر الشراء',
                        keyboardType: TextInputType.number,
                        initialValue: _purchasePrice.toString(),
                        onSaved: (val) => _purchasePrice = int.tryParse(val!) ?? 0,
                        validator: (val) => val == null || val.isEmpty ? 'مطلوب' : null,
                      ),
                    ],
                  ),
                ),
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(context),
                  child: const Text('إلغاء', style: TextStyle(color: FlarelineColors.darkTextBody)),
                ),
                ElevatedButton(
                  style: ElevatedButton.styleFrom(backgroundColor: ButtonColors.primary),
                  onPressed: () {
                    _save();
                    Navigator.pop(context);
                  },
                  child: const Text('حفظ', style: TextStyle(color: Colors.white)),
                ),
              ],
            );
          }
        );
      }
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: FlarelineColors.background,
      appBar: AppBar(
        title: const Text('إدارة المشتريات'),
        backgroundColor: FlarelineColors.primary,
        foregroundColor: Colors.white,
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _showForm,
        backgroundColor: ButtonColors.primary,
        child: const Icon(Icons.add, color: Colors.white),
      ),
      body: _invoices.isEmpty
          ? const Center(child: Text('لا توجد فواتير بعد.', style: TextStyle(color: FlarelineColors.darkTextBody, fontSize: 16)))
          : ListView.builder(
              padding: const EdgeInsets.symmetric(vertical: 12),
              itemCount: _invoices.length,
              itemBuilder: (context, index) {
                final p = _invoices[index];
                bool isPurchase = p['invoice_type'] == 'PURCHASE';
                return CommonCard(
                  margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
                  padding: const EdgeInsets.all(8),
                  child: ListTile(
                    leading: CircleAvatar(
                      backgroundColor: isPurchase ? Colors.green.withOpacity(0.2) : Colors.red.withOpacity(0.2),
                      child: Icon(
                        isPurchase ? Icons.arrow_downward : Icons.arrow_upward, 
                        color: isPurchase ? Colors.green : Colors.red
                      ),
                    ),
                    title: Text(
                      'فاتورة #${p['invoice_number']} - ${p['supplier_name'] ?? 'مورد غير معروف'}',
                      style: const TextStyle(fontWeight: FontWeight.bold, color: FlarelineColors.darkBlackText),
                    ),
                    subtitle: Text(
                      'الصنف: ${p['product_name'] ?? 'غير معروف'}\nالكمية: ${p['quantity']} | السعر: ${p['purchase_price']}\nالتاريخ: ${p['invoice_year']}/${p['invoice_month']}',
                      style: const TextStyle(color: FlarelineColors.darkTextBody),
                    ),
                  ),
                );
              },
            ),
    );
  }
}
