import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import '../db/database_helper.dart';

import 'package:flareline_uikit/components/card/common_card.dart';
import 'package:flareline_uikit/components/forms/outborder_text_form_field.dart';
import 'package:flareline_uikit/core/theme/flareline_colors.dart';

class AddReceiptScreen extends StatefulWidget {
  const AddReceiptScreen({super.key});

  @override
  State<AddReceiptScreen> createState() => _AddReceiptScreenState();
}

class _AddReceiptScreenState extends State<AddReceiptScreen> {
  final _formKey = GlobalKey<FormState>();

  // DB & Auth Data
  final dbHelper = DatabaseHelper();
  String _role = 'SALESPERSON';
  int _loggedInSalespersonId = 1;
  int _branchId = 1;
  
  List<Map<String, dynamic>> _allProducts = [];
  List<Map<String, dynamic>> _filteredProducts = [];
  List<Map<String, dynamic>> _allSalespersons = [];
  bool _isLoading = true;

  // Sale Type & Customer
  bool isCashSale = false; // Default Installment
  int? selectedSalespersonId;
  String customerName = '';
  String phone = '';
  String address = '';
  String area = '';
  int saleYear = DateTime.now().year;
  int saleMonth = DateTime.now().month;

  // Products
  final TextEditingController _searchCtrl = TextEditingController();
  List<Map<String, dynamic>> items = [];

  // Payment
  int downPayment = 0;
  final TextEditingController _installmentSystemController = TextEditingController();
  List<Map<String, int>> installmentSystems = [
    {'months': 0, 'amount': 0},
    {'months': 0, 'amount': 0},
    {'months': 0, 'amount': 0},
  ];

  @override
  void initState() {
    super.initState();
    _loadData();
    _searchCtrl.addListener(_onSearchChanged);
  }

  @override
  void dispose() {
    _searchCtrl.dispose();
    _installmentSystemController.dispose();
    super.dispose();
  }

  Future<void> _loadData() async {
    try {
      String? r = await dbHelper.getConfig('role');
      if (r != null) _role = r;

      String? sIdStr = await dbHelper.getConfig('salesperson_id');
      if (sIdStr != null) _loggedInSalespersonId = int.tryParse(sIdStr) ?? 1;

      String? bIdStr = await dbHelper.getConfig('branch_id');
      if (bIdStr != null) _branchId = int.tryParse(bIdStr) ?? 1;

      final products = await dbHelper.getInventoryItems();
      final salespersons = await dbHelper.getSalespersons();

      if (mounted) {
        setState(() {
          _allProducts = products;
          _filteredProducts = products;
          _allSalespersons = salespersons;
          
          if (_role == 'SALESPERSON') {
            selectedSalespersonId = _loggedInSalespersonId;
          } else {
            if (_allSalespersons.isNotEmpty) {
              selectedSalespersonId = _allSalespersons.first['id'];
            }
          }
          _isLoading = false;
        });
      }
    } catch (e) {
      debugPrint('Error loading data: $e');
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _onSearchChanged() {
    String q = _searchCtrl.text.toLowerCase();
    setState(() {
      _filteredProducts = _allProducts.where((p) {
        return p['name'].toString().toLowerCase().contains(q);
      }).toList();
    });
  }

  int get totalAmount {
    return items.fold(0, (sum, item) => sum + (int.tryParse(item['quantity'].toString()) ?? 0) * (int.tryParse(item['unit_price'].toString()) ?? 0));
  }

  Future<void> _saveReceipt() async {
    if (!_formKey.currentState!.validate()) return;
    _formKey.currentState!.save();

    if (items.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('برجاء إضافة منتجات للفاتورة'), backgroundColor: Colors.red));
      return;
    }
    
    if (!isCashSale && customerName.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('اسم العميل مطلوب في التقسيط'), backgroundColor: Colors.red));
      return;
    }

    setState(() => _isLoading = true);

    try {
      final db = await dbHelper.database;
      await db.transaction((txn) async {
        int receiptId = await txn.insert('receipts', {
          'source': 'MOBILE',
          'receipt_number': DateTime.now().millisecondsSinceEpoch ~/ 1000,
          'branch_id': _branchId,
          'customer_name': isCashSale ? 'كاش' : customerName,
          'phone_number': isCashSale ? '' : phone,
          'address': isCashSale ? '' : address,
          'area': isCashSale ? '' : area,
          'total_amount': totalAmount,
          'down_payment': downPayment,
          'installment_system': _installmentSystemController.text,
          'salesperson_id': selectedSalespersonId,
          'sale_year': saleYear,
          'sale_month': saleMonth,
          'is_cash_sale': isCashSale ? 1 : 0,
          'sync_action': 'NEW',
          'is_confirmed': 1,
          'created_at': DateTime.now().toIso8601String(),
          'updated_at': DateTime.now().toIso8601String(),
          'is_synced': 0
        });

        for (var item in items) {
          await txn.insert('receipt_items', {
            'receipt_id': receiptId,
            'inventory_item_id': item['inventory_item_id'],
            'quantity': item['quantity'],
            'unit_price': item['unit_price'],
            'is_synced': 0
          });
        }

        if (!isCashSale) {
          DateTime startDate = DateTime(saleYear, saleMonth, 1);
          for (int i = 0; i < 3; i++) {
            int months = installmentSystems[i]['months']!;
            int amount = installmentSystems[i]['amount']!;
            if (months > 0 && amount > 0) {
              for (int m = 1; m <= months; m++) {
                DateTime pDate = DateTime(startDate.year, startDate.month + m, 1);
                await txn.insert('installment_payments', {
                  'receipt_id': receiptId,
                  'payment_date': pDate.toIso8601String(),
                  'amount': amount,
                  'is_synced': 0
                });
              }
            }
          }
        }
      });

      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('تم حفظ الفاتورة بنجاح!')));
      Navigator.pop(context); 
    } catch (e) {
      if (!mounted) return;
      setState(() => _isLoading = false);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('خطأ أثناء الحفظ: $e'), backgroundColor: Colors.red));
    }
  }

  void _showAddProductDialog(Map<String, dynamic> product) {
    int qty = 1;
    int price = product['initial_purchase_price'] ?? 0;

    showDialog(
      context: context,
      builder: (ctx) {
        return StatefulBuilder(
          builder: (context, setDialogState) {
            return AlertDialog(
              backgroundColor: Colors.white,
              title: Text(product['name'], style: const TextStyle(fontWeight: FontWeight.bold, color: FlarelineColors.primary)),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  OutBorderTextFormField(
                    labelText: 'الكمية',
                    initialValue: qty.toString(),
                    keyboardType: TextInputType.number,
                    textInputAction: TextInputAction.next,
                    onChanged: (v) => qty = int.tryParse(v) ?? 1,
                  ),
                  const SizedBox(height: 16),
                  OutBorderTextFormField(
                    labelText: 'سعر البيع',
                    initialValue: price.toString(),
                    keyboardType: TextInputType.number,
                    textInputAction: TextInputAction.done,
                    onChanged: (v) => price = int.tryParse(v) ?? 0,
                  ),
                ],
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(ctx),
                  child: const Text('إلغاء', style: TextStyle(color: Colors.grey)),
                ),
                ElevatedButton(
                  style: ElevatedButton.styleFrom(backgroundColor: FlarelineColors.primary),
                  onPressed: () {
                    setState(() {
                      items.add({
                        'inventory_item_id': product['id'],
                        'name': product['name'],
                        'quantity': qty,
                        'unit_price': price,
                      });
                    });
                    Navigator.pop(ctx);
                  },
                  child: const Text('إضافة للفاتورة', style: TextStyle(color: Colors.white)),
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
    if (_isLoading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    return Scaffold(
      backgroundColor: const Color(0xFFF4F6F8),
      appBar: AppBar(
        title: const Text('إضافة فاتورة', style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        foregroundColor: FlarelineColors.primary,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.save),
            onPressed: _saveReceipt,
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // --- نوع الفاتورة ---
              CommonCard(
                title: 'نوع الفاتورة',
                child: Row(
                  children: [
                    Expanded(
                      child: RadioListTile<bool>(
                        title: const Text('تقسيط', style: TextStyle(fontWeight: FontWeight.bold)),
                        value: false,
                        groupValue: isCashSale,
                        activeColor: FlarelineColors.primary,
                        onChanged: (val) => setState(() => isCashSale = val!),
                      ),
                    ),
                    Expanded(
                      child: RadioListTile<bool>(
                        title: const Text('كاش', style: TextStyle(fontWeight: FontWeight.bold)),
                        value: true,
                        groupValue: isCashSale,
                        activeColor: FlarelineColors.primary,
                        onChanged: (val) => setState(() => isCashSale = val!),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              // --- المندوب للمديرين ---
              if (_role == 'MANAGER') ...[
                CommonCard(
                  title: 'المندوب',
                  child: DropdownButtonFormField<int>(
                    decoration: const InputDecoration(border: OutlineInputBorder()),
                    value: selectedSalespersonId,
                    items: _allSalespersons.map((s) {
                      return DropdownMenuItem<int>(
                        value: s['id'],
                        child: Text(s['name']),
                      );
                    }).toList(),
                    onChanged: (val) => setState(() => selectedSalespersonId = val),
                  ),
                ),
                const SizedBox(height: 16),
              ],

              // --- بيانات العميل ---
              if (!isCashSale) ...[
                CommonCard(
                  title: 'بيانات العميل',
                  child: Column(
                    children: [
                      OutBorderTextFormField(
                        labelText: 'اسم العميل',
                        initialValue: customerName,
                        textInputAction: TextInputAction.next,
                        onSaved: (val) => customerName = val ?? '',
                        validator: (val) => val == null || val.isEmpty ? 'مطلوب' : null,
                      ),
                      const SizedBox(height: 16),
                      OutBorderTextFormField(
                        labelText: 'رقم الهاتف',
                        initialValue: phone,
                        keyboardType: TextInputType.phone,
                        textInputAction: TextInputAction.next,
                        onSaved: (val) => phone = val ?? '',
                      ),
                      const SizedBox(height: 16),
                      OutBorderTextFormField(
                        labelText: 'العنوان',
                        initialValue: address,
                        textInputAction: TextInputAction.next,
                        onSaved: (val) => address = val ?? '',
                      ),
                      const SizedBox(height: 16),
                      OutBorderTextFormField(
                        labelText: 'المنطقة',
                        initialValue: area,
                        textInputAction: TextInputAction.done,
                        onSaved: (val) => area = val ?? '',
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
              ],

              // --- المنتجات ---
              CommonCard(
                title: 'إضافة المنتجات',
                child: Column(
                  children: [
                    TextField(
                      controller: _searchCtrl,
                      decoration: InputDecoration(
                        hintText: 'ابحث بالاسم لإضافة منتج...',
                        prefixIcon: const Icon(Icons.search, color: FlarelineColors.primary),
                        filled: true,
                        fillColor: Colors.grey[100],
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(8),
                          borderSide: BorderSide.none,
                        ),
                      ),
                      textInputAction: TextInputAction.search,
                    ),
                    if (_searchCtrl.text.isNotEmpty) ...[
                      const SizedBox(height: 8),
                      Container(
                        height: 150,
                        decoration: BoxDecoration(
                          border: Border.all(color: Colors.grey[300]!),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: _filteredProducts.isEmpty
                            ? const Center(child: Text('لا يوجد نتائج'))
                            : ListView.separated(
                                itemCount: _filteredProducts.length,
                                separatorBuilder: (_, __) => const Divider(height: 1),
                                itemBuilder: (context, index) {
                                  final p = _filteredProducts[index];
                                  return ListTile(
                                    title: Text(p['name'], style: const TextStyle(fontWeight: FontWeight.bold)),
                                    trailing: const Icon(Icons.add_circle, color: FlarelineColors.primary),
                                    onTap: () {
                                      FocusScope.of(context).unfocus();
                                      _searchCtrl.clear();
                                      _showAddProductDialog(p);
                                    },
                                  );
                                },
                              ),
                      ),
                    ],
                    const SizedBox(height: 16),
                    if (items.isNotEmpty) ...[
                      const Text('المنتجات في الفاتورة:', style: TextStyle(fontWeight: FontWeight.bold)),
                      const SizedBox(height: 8),
                      ListView.separated(
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
                        itemCount: items.length,
                        separatorBuilder: (_, __) => const Divider(),
                        itemBuilder: (context, index) {
                          final item = items[index];
                          return ListTile(
                            contentPadding: EdgeInsets.zero,
                            title: Text(item['name'], style: const TextStyle(fontWeight: FontWeight.bold)),
                            subtitle: Text('الكمية: ${item['quantity']} | السعر: ${item['unit_price']} ج.م'),
                            trailing: IconButton(
                              icon: const Icon(Icons.delete, color: Colors.red),
                              onPressed: () => setState(() => items.removeAt(index)),
                            ),
                          );
                        },
                      ),
                    ],
                  ],
                ),
              ),
              const SizedBox(height: 16),

              // --- الدفع ---
              CommonCard(
                color: FlarelineColors.primary,
                child: Center(
                  child: Column(
                    children: [
                      const Text('إجمالي الفاتورة', style: TextStyle(color: Colors.white70, fontSize: 16)),
                      const SizedBox(height: 8),
                      Text('$totalAmount ج.م', style: const TextStyle(color: Colors.white, fontSize: 32, fontWeight: FontWeight.bold)),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),

              if (isCashSale)
                const CommonCard(
                  child: Padding(
                    padding: EdgeInsets.all(16.0),
                    child: Center(
                      child: Text('فاتورة كاش - لا يوجد أقساط', style: TextStyle(fontSize: 16, color: Colors.green, fontWeight: FontWeight.bold)),
                    ),
                  ),
                )
              else ...[
                CommonCard(
                  title: 'التقسيط',
                  child: Column(
                    children: [
                      OutBorderTextFormField(
                        labelText: 'المبلغ المدفوع مقدماً',
                        initialValue: downPayment.toString(),
                        keyboardType: TextInputType.number,
                        textInputAction: TextInputAction.next,
                        onChanged: (val) => downPayment = int.tryParse(val) ?? 0,
                      ),
                      const SizedBox(height: 24),
                      const Text('أنظمة التقسيط', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                      const SizedBox(height: 16),
                      for (int i = 0; i < 3; i++) ...[
                        Row(
                          children: [
                            Expanded(
                              child: OutBorderTextFormField(
                                labelText: 'المدة (أشهر)',
                                initialValue: installmentSystems[i]['months'].toString(),
                                keyboardType: TextInputType.number,
                                textInputAction: TextInputAction.next,
                                onChanged: (val) => installmentSystems[i]['months'] = int.tryParse(val) ?? 0,
                              ),
                            ),
                            const SizedBox(width: 16),
                            Expanded(
                              child: OutBorderTextFormField(
                                labelText: 'القسط الشهري',
                                initialValue: installmentSystems[i]['amount'].toString(),
                                keyboardType: TextInputType.number,
                                textInputAction: i == 2 ? TextInputAction.done : TextInputAction.next,
                                onChanged: (val) => installmentSystems[i]['amount'] = int.tryParse(val) ?? 0,
                              ),
                            ),
                          ],
                        ),
                        if (i < 2) const SizedBox(height: 16),
                      ]
                    ],
                  ),
                ),
              ],
              const SizedBox(height: 24),
              SizedBox(
                height: 50,
                child: ElevatedButton.icon(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: FlarelineColors.primary,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                  ),
                  onPressed: _saveReceipt,
                  icon: const Icon(Icons.check_circle, color: Colors.white),
                  label: const Text('حفظ الفاتورة النهائية', style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
                ),
              ),
              const SizedBox(height: 40),
            ],
          ),
        ),
      ),
    );
  }
}
