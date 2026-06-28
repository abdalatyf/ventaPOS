import 'package:flutter/material.dart';
import '../db/database_helper.dart';
import 'package:flareline_uikit/components/card/common_card.dart';
import 'package:flareline_uikit/components/forms/outborder_text_form_field.dart';
import 'package:flareline_uikit/core/theme/flareline_colors.dart';

class ManageSuppliersScreen extends StatefulWidget {
  const ManageSuppliersScreen({super.key});

  @override
  State<ManageSuppliersScreen> createState() => _ManageSuppliersScreenState();
}

class _ManageSuppliersScreenState extends State<ManageSuppliersScreen> {
  List<Map<String, dynamic>> _suppliers = [];
  final TextEditingController _nameCtrl = TextEditingController();

  @override
  void initState() {
    super.initState();
    _loadSuppliers();
  }

  Future<void> _loadSuppliers() async {
    final db = await DatabaseHelper.instance.database;
    final data = await db.query('suppliers', orderBy: 'id DESC');
    setState(() => _suppliers = data);
  }

  Future<bool> _saveSupplier({int? id}) async {
    final name = _nameCtrl.text.trim();
    if (name.isEmpty) return false;
    final scaffoldMessenger = ScaffoldMessenger.of(context);
    final db = await DatabaseHelper.instance.database;

    List<Map<String, dynamic>> existing;
    if (id == null) {
      existing = await db.query(
        'suppliers',
        where: 'name = ?',
        whereArgs: [name],
        limit: 1,
      );
    } else {
      existing = await db.query(
        'suppliers',
        where: 'name = ? AND id != ?',
        whereArgs: [name, id],
        limit: 1,
      );
    }

    if (existing.isNotEmpty) {
      scaffoldMessenger.showSnackBar(
        const SnackBar(
          content: Text('اسم المورد مسجل بالفعل!'),
          backgroundColor: ButtonColors.danger,
        ),
      );
      return false;
    }

    if (id == null) {
      await db.insert('suppliers', {'name': name, 'is_synced': 0});
      scaffoldMessenger.showSnackBar(
        const SnackBar(content: Text('تمت إضافة المورد بنجاح.')),
      );
    } else {
      await db.update('suppliers', {'name': name, 'is_synced': 0}, where: 'id = ?', whereArgs: [id]);
      scaffoldMessenger.showSnackBar(
        const SnackBar(content: Text('تم تعديل المورد بنجاح.')),
      );
    }

    _nameCtrl.clear();
    _loadSuppliers();
    return true;
  }

  Future<void> _deleteSupplier(int id) async {
    final scaffoldMessenger = ScaffoldMessenger.of(context);
    final db = await DatabaseHelper.instance.database;

    final invoices = await db.query(
      'purchase_invoices',
      where: 'supplier_id = ?',
      whereArgs: [id],
      limit: 1,
    );

    if (invoices.isNotEmpty) {
      scaffoldMessenger.showSnackBar(
        const SnackBar(
          content: Text('لا يمكن الحذف لوجود فواتير مرتبطة به.'),
          backgroundColor: ButtonColors.danger,
        ),
      );
      return;
    }

    await db.delete(
      'suppliers',
      where: 'id = ?',
      whereArgs: [id],
    );

    scaffoldMessenger.showSnackBar(
      const SnackBar(content: Text('تم حذف المورد بنجاح.')),
    );
    _loadSuppliers();
  }

  void _showForm([Map<String, dynamic>? supplier]) {
    if (supplier != null) {
      _nameCtrl.text = supplier['name'];
    } else {
      _nameCtrl.clear();
    }

    final formKey = GlobalKey<FormState>();

    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: Text(
            supplier == null ? 'إضافة مورد' : 'تعديل مورد',
            style: const TextStyle(
              color: FlarelineColors.darkBlackText,
              fontWeight: FontWeight.bold,
            ),
          ),
          content: Form(
            key: formKey,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                OutBorderTextFormField(
                  controller: _nameCtrl,
                  labelText: 'اسم المورد',
                  hintText: 'أدخل اسم المورد',
                  validator: (value) {
                    if (value == null || value.trim().isEmpty) {
                      return 'اسم المورد مطلوب';
                    }
                    return null;
                  },
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('إلغاء', style: TextStyle(color: FlarelineColors.darkTextBody)),
            ),
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: ButtonColors.primary,
              ),
              onPressed: () async {
                if (formKey.currentState!.validate()) {
                  final navigator = Navigator.of(context);
                  bool success = await _saveSupplier(id: supplier?['id']);
                  if (success) {
                    navigator.pop();
                  }
                }
              },
              child: const Text('حفظ', style: TextStyle(color: Colors.white)),
            ),
          ],
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: FlarelineColors.background,
      appBar: AppBar(
        title: const Text('إدارة الموردين'),
        backgroundColor: FlarelineColors.primary,
        foregroundColor: Colors.white,
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showForm(),
        backgroundColor: ButtonColors.primary,
        child: const Icon(Icons.add, color: Colors.white),
      ),
      body: _suppliers.isEmpty
          ? const Center(
              child: Text(
                'لا يوجد موردين بعد.',
                style: TextStyle(
                  color: FlarelineColors.darkTextBody,
                  fontSize: 16,
                ),
              ),
            )
          : ListView.builder(
              padding: const EdgeInsets.symmetric(vertical: 12),
              itemCount: _suppliers.length,
              itemBuilder: (context, index) {
                final s = _suppliers[index];
                return CommonCard(
                  margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
                  padding: const EdgeInsets.all(8),
                  child: ListTile(
                    title: Text(
                      s['name'],
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: FlarelineColors.darkBlackText,
                      ),
                    ),
                    trailing: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        IconButton(
                          icon: const Icon(Icons.edit, color: ButtonColors.secondary),
                          onPressed: () => _showForm(s),
                        ),
                        IconButton(
                          icon: const Icon(Icons.delete, color: ButtonColors.danger),
                          onPressed: () => _deleteSupplier(s['id']),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
    );
  }
}
