import 'package:flutter/material.dart';
import '../db/database_helper.dart';
import 'package:flareline_uikit/components/card/common_card.dart';
import 'package:flareline_uikit/components/forms/outborder_text_form_field.dart';
import 'package:flareline_uikit/core/theme/flareline_colors.dart';

class ManageProductsScreen extends StatefulWidget {
  const ManageProductsScreen({super.key});

  @override
  State<ManageProductsScreen> createState() => _ManageProductsScreenState();
}

class _ManageProductsScreenState extends State<ManageProductsScreen> {
  final _formKey = GlobalKey<FormState>();

  String _name = '';
  int _initQty = 0;
  int _initPrice = 0;
  int _initCommission = 0;
  int _initMonth = DateTime.now().month;
  int _initYear = DateTime.now().year;

  List<Map<String, dynamic>> _products = [];

  @override
  void initState() {
    super.initState();
    _loadProducts();
  }

  Future<void> _loadProducts() async {
    final db = await DatabaseHelper.instance.database;
    
    // Load current products
    final data = await db.query('inventory', orderBy: 'id DESC');

    // Self-healing logic: matches lines 80-89 of inventory_views.py
    for (final item in data) {
      final itemId = item['id'] as int;
      final existingCommission = await db.query(
        'commission_history',
        where: 'item_id = ?',
        whereArgs: [itemId],
      );

      if (existingCommission.isEmpty) {
        final defMonth = DateTime.now().month;
        final defYear = DateTime.now().year;

        await db.insert('commission_history', {
          'item_id': itemId,
          'commission_amount': item['initial_commission_amount'] ?? 0,
          'activation_month': item['initial_month'] ?? defMonth,
          'activation_year': item['initial_year'] ?? defYear,
          'created_at': DateTime.now().toIso8601String(),
          'is_synced': 0
        });
      }
    }

    final updatedData = await db.query('inventory', orderBy: 'id DESC');
    setState(() {
      _products = updatedData;
    });
  }

  Future<void> _addProduct() async {
    if (!_formKey.currentState!.validate()) return;
    _formKey.currentState!.save();

    final nameTrimmed = _name.trim();
    if (nameTrimmed.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('خطأ: يجب إدخال اسم الصنف')),
      );
      return;
    }

    final db = await DatabaseHelper.instance.database;

    // Check if name already exists in the local database
    final existing = await db.query(
      'inventory',
      where: 'name = ?',
      whereArgs: [nameTrimmed],
    );

    if (existing.isNotEmpty) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('خطأ: اسم الصنف موجود مسبقاً')),
        );
      }
      return;
    }

    // Insert product
    final id = await db.insert('inventory', {
      'name': nameTrimmed,
      'branch_id': 1, // Dummy
      'initial_quantity': _initQty,
      'initial_purchase_price': _initPrice,
      'initial_commission_amount': _initCommission,
      'initial_month': _initMonth,
      'initial_year': _initYear,
      'created_at': DateTime.now().toIso8601String(),
      'updated_at': DateTime.now().toIso8601String(),
      'is_synced': 0
    });

    // Create a record in commission_history table
    await db.insert('commission_history', {
      'item_id': id,
      'commission_amount': _initCommission,
      'activation_month': _initMonth,
      'activation_year': _initYear,
      'created_at': DateTime.now().toIso8601String(),
      'is_synced': 0
    });

    _formKey.currentState!.reset();
    setState(() {
      _name = '';
      _initQty = 0;
      _initPrice = 0;
      _initCommission = 0;
      _initMonth = DateTime.now().month;
      _initYear = DateTime.now().year;
    });

    _loadProducts();

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('تم إضافة المنتج بنجاح!')),
      );
    }
  }

  Future<void> _showEditDialog(Map<String, dynamic> product) async {
    final editFormKey = GlobalKey<FormState>();
    String editName = product['name'] ?? '';
    int editQty = product['initial_quantity'] ?? 0;
    int editPrice = product['initial_purchase_price'] ?? 0;
    int editCommission = product['initial_commission_amount'] ?? 0;
    int editMonth = product['initial_month'] ?? DateTime.now().month;
    int editYear = product['initial_year'] ?? DateTime.now().year;

    if (!mounted) return;

    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: Text('تعديل المنتج - ${product['name']}', style: const TextStyle(fontWeight: FontWeight.bold)),
          content: SingleChildScrollView(
            child: Form(
              key: editFormKey,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  OutBorderTextFormField(
                    labelText: 'اسم المنتج',
                    initialValue: editName,
                    validator: (val) => val == null || val.trim().isEmpty ? 'مطلوب' : null,
                    onSaved: (val) => editName = val ?? '',
                  ),
                  const SizedBox(height: 12),
                  OutBorderTextFormField(
                    labelText: 'الكمية الابتدائية',
                    initialValue: editQty.toString(),
                    keyboardType: TextInputType.number,
                    validator: (val) => (val == null || int.tryParse(val) == null) ? 'قيمة غير صالحة' : null,
                    onSaved: (val) => editQty = int.tryParse(val ?? '') ?? 0,
                  ),
                  const SizedBox(height: 12),
                  OutBorderTextFormField(
                    labelText: 'سعر الشراء الابتدائي',
                    initialValue: editPrice.toString(),
                    keyboardType: TextInputType.number,
                    validator: (val) => (val == null || int.tryParse(val) == null) ? 'قيمة غير صالحة' : null,
                    onSaved: (val) => editPrice = int.tryParse(val ?? '') ?? 0,
                  ),
                  const SizedBox(height: 12),
                  OutBorderTextFormField(
                    labelText: 'العمولة الابتدائية',
                    initialValue: editCommission.toString(),
                    keyboardType: TextInputType.number,
                    validator: (val) => (val == null || int.tryParse(val) == null) ? 'قيمة غير صالحة' : null,
                    onSaved: (val) => editCommission = int.tryParse(val ?? '') ?? 0,
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(
                        child: OutBorderTextFormField(
                          labelText: 'الشهر الابتدائي',
                          initialValue: editMonth.toString(),
                          keyboardType: TextInputType.number,
                          validator: (val) {
                            if (val == null || val.isEmpty) return 'مطلوب';
                            final m = int.tryParse(val);
                            if (m == null || m < 1 || m > 12) return 'غير صالح';
                            return null;
                          },
                          onSaved: (val) => editMonth = int.tryParse(val ?? '') ?? DateTime.now().month,
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: OutBorderTextFormField(
                          labelText: 'السنة الابتدائية',
                          initialValue: editYear.toString(),
                          keyboardType: TextInputType.number,
                          validator: (val) {
                            if (val == null || val.isEmpty) return 'مطلوب';
                            final y = int.tryParse(val);
                            if (y == null || y < 2000 || y > 2100) return 'غير صالح';
                            return null;
                          },
                          onSaved: (val) => editYear = int.tryParse(val ?? '') ?? DateTime.now().year,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('إلغاء'),
            ),
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: FlarelineColors.primary,
                foregroundColor: Colors.white,
              ),
              onPressed: () async {
                if (!editFormKey.currentState!.validate()) return;
                editFormKey.currentState!.save();

                final nameTrimmed = editName.trim();
                if (nameTrimmed.isEmpty) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('خطأ: يجب إدخال اسم الصنف')),
                  );
                  return;
                }

                final db = await DatabaseHelper.instance.database;

                // Check if name already exists in the local database (for another product)
                final existing = await db.query(
                  'inventory',
                  where: 'name = ? AND id != ?',
                  whereArgs: [nameTrimmed, product['id']],
                );

                if (existing.isNotEmpty) {
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('خطأ: اسم الصنف موجود مسبقاً')),
                    );
                  }
                  return;
                }

                // Update product
                await db.update('inventory', {
                  'name': nameTrimmed,
                  'initial_quantity': editQty,
                  'initial_purchase_price': editPrice,
                  'initial_commission_amount': editCommission,
                  'initial_month': editMonth,
                  'initial_year': editYear,
                  'updated_at': DateTime.now().toIso8601String(),
                  'is_synced': 0
                }, where: 'id = ?', whereArgs: [product['id']]);

                if (context.mounted) {
                  Navigator.pop(context);
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('تم تعديل المنتج بنجاح!')),
                  );
                }

                _loadProducts();
              },
              child: const Text('حفظ'),
            ),
          ],
        );
      },
    );
  }

  Future<void> _deleteProduct(int productId, String productName) async {
    final db = await DatabaseHelper.instance.database;

    // Check if the product is referenced in sales receipts (receipt_items)
    final receiptRefs = await db.query(
      'receipt_items',
      where: 'inventory_item_id = ?',
      whereArgs: [productId],
    );

    // Check if the product is referenced in purchase invoices (purchase_invoice_items)
    final purchaseRefs = await db.query(
      'purchase_invoice_items',
      where: 'inventory_item_id = ?',
      whereArgs: [productId],
    );

    if (receiptRefs.isNotEmpty || purchaseRefs.isNotEmpty) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('خطأ: لا يمكن الحذف لوجود عمليات مرتبطة به.'),
            backgroundColor: Colors.red,
          ),
        );
      }
      return;
    }

    // Confirm deletion
    if (!mounted) return;
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('تأكيد الحذف', style: TextStyle(fontWeight: FontWeight.bold)),
          content: Text('هل أنت متأكد من حذف الصنف "$productName"؟'),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('إلغاء'),
            ),
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: ButtonColors.danger,
                foregroundColor: Colors.white,
              ),
              onPressed: () => Navigator.pop(context, true),
              child: const Text('حذف'),
            ),
          ],
        );
      },
    );

    if (confirm == true) {
      // Cascade delete commission history and product
      await db.delete('commission_history', where: 'item_id = ?', whereArgs: [productId]);
      await db.delete('inventory', where: 'id = ?', whereArgs: [productId]);

      _loadProducts();

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('تم حذف الصنف "$productName" بنجاح.')),
        );
      }
    }
  }

  Future<void> _showCommissionModal(int productId, String productName) async {
    final db = await DatabaseHelper.instance.database;
    int cMonth = DateTime.now().month;
    int cYear = DateTime.now().year;
    int cAmount = 0;
    final commissionFormKey = GlobalKey<FormState>();

    if (!mounted) return;

    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: Text('Commission History - $productName'),
          content: Form(
            key: commissionFormKey,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                OutBorderTextFormField(
                  labelText: 'Month',
                  initialValue: cMonth.toString(),
                  keyboardType: TextInputType.number,
                  validator: (val) {
                    if (val == null || val.isEmpty) return 'Required';
                    final m = int.tryParse(val);
                    if (m == null || m < 1 || m > 12) return 'Invalid month';
                    return null;
                  },
                  onSaved: (val) => cMonth = int.parse(val!),
                ),
                const SizedBox(height: 12),
                OutBorderTextFormField(
                  labelText: 'Year',
                  initialValue: cYear.toString(),
                  keyboardType: TextInputType.number,
                  validator: (val) {
                    if (val == null || val.isEmpty) return 'Required';
                    final y = int.tryParse(val);
                    if (y == null || y < 2000 || y > 2100) return 'Invalid year';
                    return null;
                  },
                  onSaved: (val) => cYear = int.parse(val!),
                ),
                const SizedBox(height: 12),
                OutBorderTextFormField(
                  labelText: 'Amount',
                  keyboardType: TextInputType.number,
                  validator: (val) {
                    if (val == null || val.isEmpty) return 'Required';
                    if (int.tryParse(val) == null) return 'Invalid amount';
                    return null;
                  },
                  onSaved: (val) => cAmount = int.parse(val!),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('إلغاء'),
            ),
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: FlarelineColors.primary,
                foregroundColor: Colors.white,
              ),
              onPressed: () async {
                if (!commissionFormKey.currentState!.validate()) return;
                commissionFormKey.currentState!.save();

                await db.insert('commission_history', {
                  'item_id': productId,
                  'commission_amount': cAmount,
                  'activation_month': cMonth,
                  'activation_year': cYear,
                  'created_at': DateTime.now().toIso8601String(),
                  'is_synced': 0
                });
                if (context.mounted) {
                  Navigator.pop(context);
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Commission Added!')));
                }
              },
              child: const Text('إضافة تسوية'),
            ),
          ],
        );
      }
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('إدارة المنتجات')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(8.0),
            child: CommonCard(
              title: 'Add New Product',
              margin: EdgeInsets.zero,
              child: Form(
                key: _formKey,
                child: Column(
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: OutBorderTextFormField(
                            labelText: 'Name',
                            validator: (val) => val == null || val.trim().isEmpty ? 'Required' : null,
                            onSaved: (val) => _name = val ?? '',
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: OutBorderTextFormField(
                            labelText: 'Initial Qty',
                            keyboardType: TextInputType.number,
                            validator: (val) => (val == null || int.tryParse(val) == null) ? 'Required' : null,
                            onSaved: (val) => _initQty = int.tryParse(val!) ?? 0,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        Expanded(
                          child: OutBorderTextFormField(
                            labelText: 'Initial Price',
                            keyboardType: TextInputType.number,
                            validator: (val) => (val == null || int.tryParse(val) == null) ? 'Required' : null,
                            onSaved: (val) => _initPrice = int.tryParse(val!) ?? 0,
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: OutBorderTextFormField(
                            labelText: 'Initial Comm',
                            keyboardType: TextInputType.number,
                            validator: (val) => (val == null || int.tryParse(val) == null) ? 'Required' : null,
                            onSaved: (val) => _initCommission = int.tryParse(val!) ?? 0,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        Expanded(
                          child: OutBorderTextFormField(
                            labelText: 'Start Month',
                            initialValue: _initMonth.toString(),
                            keyboardType: TextInputType.number,
                            validator: (val) {
                              if (val == null || val.isEmpty) return 'Required';
                              final m = int.tryParse(val);
                              if (m == null || m < 1 || m > 12) return 'Invalid';
                              return null;
                            },
                            onSaved: (val) => _initMonth = int.tryParse(val!) ?? DateTime.now().month,
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: OutBorderTextFormField(
                            labelText: 'Start Year',
                            initialValue: _initYear.toString(),
                            keyboardType: TextInputType.number,
                            validator: (val) {
                              if (val == null || val.isEmpty) return 'Required';
                              final y = int.tryParse(val);
                              if (y == null || y < 2000 || y > 2100) return 'Invalid';
                              return null;
                            },
                            onSaved: (val) => _initYear = int.tryParse(val!) ?? DateTime.now().year,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: FlarelineColors.primary,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                      ),
                      onPressed: _addProduct,
                      child: const Text('إضافة منتج'),
                    )
                  ],
                ),
              ),
            ),
          ),
          const Divider(),
          Expanded(
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: SingleChildScrollView(
                child: DataTable(
                  columns: const [
                    DataColumn(label: Text('الرقم')),
                    DataColumn(label: Text('الاسم')),
                    DataColumn(label: Text('الكمية')),
                    DataColumn(label: Text('السعر')),
                    DataColumn(label: Text('العمولة')),
                    DataColumn(label: Text('إجراءات')),
                  ],
                  rows: _products.map((p) {
                    int qty = p['initial_quantity'] ?? 0;
                    bool isLow = qty <= 5;

                    return DataRow(
                      color: WidgetStateProperty.resolveWith<Color?>(
                        (Set<WidgetState> states) {
                          return isLow ? Colors.red.shade100 : null;
                        },
                      ),
                      cells: [
                        DataCell(Text(p['id'].toString())),
                        DataCell(Text(p['name'].toString())),
                        DataCell(Text(qty.toString())),
                        DataCell(Text(p['initial_purchase_price'].toString())),
                        DataCell(Text(p['initial_commission_amount'].toString())),
                        DataCell(
                          Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              ElevatedButton(
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: FlarelineColors.primary,
                                  foregroundColor: Colors.white,
                                  padding: const EdgeInsets.symmetric(horizontal: 8),
                                ),
                                onPressed: () => _showCommissionModal(p['id'], p['name']),
                                child: const Text('Comm. History', style: TextStyle(fontSize: 11)),
                              ),
                              IconButton(
                                icon: const Icon(Icons.edit, color: Colors.blue),
                                onPressed: () => _showEditDialog(p),
                              ),
                              IconButton(
                                icon: const Icon(Icons.delete, color: ButtonColors.danger),
                                onPressed: () => _deleteProduct(p['id'], p['name']),
                              ),
                            ],
                          ),
                        ),
                      ],
                    );
                  }).toList(),
                ),
              ),
            ),
          )
        ],
      ),
    );
  }
}
