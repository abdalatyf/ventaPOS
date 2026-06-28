import 'package:flutter/material.dart';
import '../db/database_helper.dart';
import 'package:flareline_uikit/components/card/common_card.dart';
import 'package:flareline_uikit/components/forms/outborder_text_form_field.dart';
import 'package:flareline_uikit/core/theme/flareline_colors.dart';

class ManageBranchesScreen extends StatefulWidget {
  const ManageBranchesScreen({super.key});

  @override
  State<ManageBranchesScreen> createState() => _ManageBranchesScreenState();
}

class _ManageBranchesScreenState extends State<ManageBranchesScreen> {
  List<Map<String, dynamic>> _branches = [];
  final TextEditingController _nameCtrl = TextEditingController();

  @override
  void initState() {
    super.initState();
    _loadBranches();
  }

  Future<void> _loadBranches() async {
    final db = await DatabaseHelper.instance.database;
    final data = await db.query('branches', orderBy: 'id DESC');
    setState(() => _branches = data);
  }

  Future<bool> _saveBranch({int? id}) async {
    final name = _nameCtrl.text.trim();
    if (name.isEmpty) return false;
    final scaffoldMessenger = ScaffoldMessenger.of(context);
    final db = await DatabaseHelper.instance.database;

    List<Map<String, dynamic>> existing;
    if (id == null) {
      existing = await db.query(
        'branches',
        where: 'name = ?',
        whereArgs: [name],
        limit: 1,
      );
    } else {
      existing = await db.query(
        'branches',
        where: 'name = ? AND id != ?',
        whereArgs: [name, id],
        limit: 1,
      );
    }

    if (existing.isNotEmpty) {
      scaffoldMessenger.showSnackBar(
        SnackBar(
          content: Text("خطأ: الاسم '$name' موجود مسبقاً."),
          backgroundColor: ButtonColors.danger,
        ),
      );
      return false;
    }

    if (id == null) {
      await db.insert('branches', {'name': name, 'is_synced': 0});
      scaffoldMessenger.showSnackBar(
        const SnackBar(content: Text('تمت إضافة الفرع بنجاح.')),
      );
    } else {
      await db.update('branches', {'name': name, 'is_synced': 0}, where: 'id = ?', whereArgs: [id]);
      scaffoldMessenger.showSnackBar(
        const SnackBar(content: Text('تم تعديل الفرع بنجاح.')),
      );
    }

    _nameCtrl.clear();
    _loadBranches();
    return true;
  }

  Future<void> _deleteBranch(int id) async {
    final scaffoldMessenger = ScaffoldMessenger.of(context);
    final db = await DatabaseHelper.instance.database;

    // Check salespersons
    final salespersons = await db.query(
      'salespersons',
      where: 'branch_id = ?',
      whereArgs: [id],
      limit: 1,
    );

    // Check receipts
    final receipts = await db.query(
      'receipts',
      where: 'branch_id = ?',
      whereArgs: [id],
      limit: 1,
    );

    if (salespersons.isNotEmpty || receipts.isNotEmpty) {
      scaffoldMessenger.showSnackBar(
        const SnackBar(
          content: Text("خطأ: لا يمكن حذف هذا الفرع لأنه يحتوي على بيانات (موظفين/فواتير)."),
          backgroundColor: ButtonColors.danger,
        ),
      );
      return;
    }

    await db.delete(
      'branches',
      where: 'id = ?',
      whereArgs: [id],
    );

    scaffoldMessenger.showSnackBar(
      const SnackBar(content: Text('تم حذف الفرع بنجاح.')),
    );
    _loadBranches();
  }

  void _showForm([Map<String, dynamic>? branch]) {
    if (branch != null) {
      _nameCtrl.text = branch['name'];
    } else {
      _nameCtrl.clear();
    }

    final formKey = GlobalKey<FormState>();

    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: Text(
            branch == null ? 'إضافة فرع' : 'تعديل فرع',
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
                  labelText: 'اسم الفرع',
                  hintText: 'أدخل اسم الفرع',
                  validator: (value) {
                    if (value == null || value.trim().isEmpty) {
                      return 'اسم الفرع مطلوب';
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
                  bool success = await _saveBranch(id: branch?['id']);
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
        title: const Text('إدارة الفروع'),
        backgroundColor: FlarelineColors.primary,
        foregroundColor: Colors.white,
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showForm(),
        backgroundColor: ButtonColors.primary,
        child: const Icon(Icons.add, color: Colors.white),
      ),
      body: _branches.isEmpty
          ? const Center(
              child: Text(
                'لا يوجد فروع بعد.',
                style: TextStyle(
                  color: FlarelineColors.darkTextBody,
                  fontSize: 16,
                ),
              ),
            )
          : ListView.builder(
              padding: const EdgeInsets.symmetric(vertical: 12),
              itemCount: _branches.length,
              itemBuilder: (context, index) {
                final b = _branches[index];
                return CommonCard(
                  margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
                  padding: const EdgeInsets.all(8),
                  child: ListTile(
                    title: Text(
                      b['name'],
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
                          onPressed: () => _showForm(b),
                        ),
                        IconButton(
                          icon: const Icon(Icons.delete, color: ButtonColors.danger),
                          onPressed: () => _deleteBranch(b['id']),
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
