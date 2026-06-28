import 'package:flutter/material.dart';
import '../db/database_helper.dart';
import 'package:flareline_uikit/components/card/common_card.dart';
import 'package:flareline_uikit/components/forms/outborder_text_form_field.dart';
import 'package:flareline_uikit/core/theme/flareline_colors.dart';

class ManageUsersScreen extends StatefulWidget {
  const ManageUsersScreen({super.key});

  @override
  State<ManageUsersScreen> createState() => _ManageUsersScreenState();
}

class _ManageUsersScreenState extends State<ManageUsersScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: FlarelineColors.background,
      appBar: AppBar(
        title: const Text('إدارة المستخدمين'),
        backgroundColor: FlarelineColors.primary,
        foregroundColor: Colors.white,
        bottom: TabBar(
          controller: _tabController,
          labelColor: Colors.white,
          unselectedLabelColor: Colors.white70,
          indicatorColor: Colors.white,
          tabs: const [
            Tab(text: 'المندوبين'),
            Tab(text: 'المستخدمين السحابيين'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: const [
          _SalespersonTab(),
          _CloudUserTab(),
        ],
      ),
    );
  }
}

// ----------------------------------------------------------------------
// Salesperson Tab
// ----------------------------------------------------------------------
class _SalespersonTab extends StatefulWidget {
  const _SalespersonTab();

  @override
  State<_SalespersonTab> createState() => _SalespersonTabState();
}

class _SalespersonTabState extends State<_SalespersonTab> {
  List<Map<String, dynamic>> _salespersons = [];
  
  final _nameCtrl = TextEditingController();
  final _branchCtrl = TextEditingController();
  final _cUserCtrl = TextEditingController();
  final _cPassCtrl = TextEditingController();

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _nameCtrl.dispose();
    _branchCtrl.dispose();
    _cUserCtrl.dispose();
    _cPassCtrl.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    final db = await DatabaseHelper.instance.database;
    final data = await db.query('salespersons', orderBy: 'id DESC');
    setState(() => _salespersons = data);
  }

  Future<bool> _save({int? id}) async {
    final name = _nameCtrl.text.trim();
    if (name.isEmpty) return false;

    final db = await DatabaseHelper.instance.database;

    // Unique check: check if salesperson name exists in the database.
    // If yes, display error "خطأ: الاسم '...' موجود مسبقاً." via SnackBar.
    List<Map<String, dynamic>> existing;
    if (id == null) {
      existing = await db.query(
        'salespersons',
        where: 'name = ?',
        whereArgs: [name],
        limit: 1,
      );
    } else {
      existing = await db.query(
        'salespersons',
        where: 'name = ? AND id != ?',
        whereArgs: [name, id],
        limit: 1,
      );
    }

    if (existing.isNotEmpty) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text("خطأ: الاسم '$name' موجود مسبقاً."),
            backgroundColor: ButtonColors.danger,
          ),
        );
      }
      return false;
    }

    final map = {
      'name': name,
      'branch_id': int.tryParse(_branchCtrl.text) ?? 1,
      'cloud_username': _cUserCtrl.text,
      'cloud_password': _cPassCtrl.text,
      'is_synced': 0
    };

    if (id == null) {
      await db.insert('salespersons', map);
    } else {
      await db.update('salespersons', map, where: 'id = ?', whereArgs: [id]);
    }

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(id == null ? 'تمت إضافة المندوب بنجاح.' : 'تم تعديل المندوب بنجاح.'),
        ),
      );
    }

    _load();
    return true;
  }

  Future<void> _deleteSalesperson(int id, String name) async {
    final db = await DatabaseHelper.instance.database;

    // Deletion protection: check if salesperson is referenced in receipts table (check salesperson_id = id)
    final references = await db.query(
      'receipts',
      where: 'salesperson_id = ?',
      whereArgs: [id],
      limit: 1,
    );

    if (references.isNotEmpty) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text("خطأ: لا يمكن حذف هذا الموظف لوجود فواتير أو حركات مرتبطة به."),
            backgroundColor: ButtonColors.danger,
          ),
        );
      }
      return;
    }

    if (!mounted) return;
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('تأكيد الحذف', style: TextStyle(fontWeight: FontWeight.bold)),
          content: Text('هل أنت متأكد من حذف المندوب "$name"؟'),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('إلغاء', style: TextStyle(color: FlarelineColors.darkTextBody)),
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
      final db = await DatabaseHelper.instance.database;
      await db.delete('salespersons', where: 'id = ?', whereArgs: [id]);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('تم حذف المندوب "$name" بنجاح.')),
        );
      }
      _load();
    }
  }

  void _showForm([Map<String, dynamic>? s]) {
    if (s != null) {
      _nameCtrl.text = s['name'] ?? '';
      _branchCtrl.text = s['branch_id']?.toString() ?? '1';
      _cUserCtrl.text = s['cloud_username'] ?? '';
      _cPassCtrl.text = s['cloud_password'] ?? '';
    } else {
      _nameCtrl.clear();
      _branchCtrl.text = '1';
      _cUserCtrl.clear();
      _cPassCtrl.clear();
    }

    final formKey = GlobalKey<FormState>();

    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: Text(
            s == null ? 'إضافة مندوب' : 'تعديل مندوب',
            style: const TextStyle(
              color: FlarelineColors.darkBlackText,
              fontWeight: FontWeight.bold,
            ),
          ),
          content: SingleChildScrollView(
            child: Form(
              key: formKey,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  OutBorderTextFormField(
                    controller: _nameCtrl,
                    labelText: 'الاسم',
                    hintText: 'أدخل الاسم',
                    validator: (value) {
                      if (value == null || value.trim().isEmpty) {
                        return 'الاسم مطلوب';
                      }
                      return null;
                    },
                  ),
                  const SizedBox(height: 12),
                  OutBorderTextFormField(
                    controller: _branchCtrl,
                    labelText: 'رقم الفرع',
                    hintText: 'أدخل رقم الفرع',
                    keyboardType: TextInputType.number,
                    validator: (value) {
                      if (value == null || value.trim().isEmpty) {
                        return 'رقم الفرع مطلوب';
                      }
                      if (int.tryParse(value) == null) {
                        return 'يجب إدخال رقم صحيح';
                      }
                      return null;
                    },
                  ),
                  const SizedBox(height: 12),
                  OutBorderTextFormField(
                    controller: _cUserCtrl,
                    labelText: 'اسم مستخدم السحابة',
                    hintText: 'أدخل اسم مستخدم السحابة',
                  ),
                  const SizedBox(height: 12),
                  OutBorderTextFormField(
                    controller: _cPassCtrl,
                    labelText: 'كلمة مرور السحابة',
                    hintText: 'أدخل كلمة مرور السحابة',
                    obscureText: true,
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
              style: ElevatedButton.styleFrom(
                backgroundColor: ButtonColors.primary,
              ),
              onPressed: () async {
                if (formKey.currentState!.validate()) {
                  final navigator = Navigator.of(context);
                  bool success = await _save(id: s?['id']);
                  if (success && navigator.mounted) {
                    navigator.pop();
                  }
                }
              },
              child: const Text('حفظ', style: TextStyle(color: Colors.white)),
            ),
          ],
        );
      }
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: FlarelineColors.background,
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showForm(),
        backgroundColor: ButtonColors.primary,
        child: const Icon(Icons.add, color: Colors.white),
      ),
      body: _salespersons.isEmpty
          ? const Center(
              child: Text(
                'لا يوجد مندوبين بعد.',
                style: TextStyle(
                  color: FlarelineColors.darkTextBody,
                  fontSize: 16,
                ),
              ),
            )
          : ListView.builder(
              padding: const EdgeInsets.symmetric(vertical: 12),
              itemCount: _salespersons.length,
              itemBuilder: (context, index) {
                final s = _salespersons[index];
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
                    subtitle: Text(
                      'الفرع: ${s['branch_id']} | CloudUser: ${s['cloud_username'] ?? ''}',
                      style: const TextStyle(color: FlarelineColors.darkTextBody),
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
                          onPressed: () => _deleteSalesperson(s['id'], s['name']),
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

// ----------------------------------------------------------------------
// CloudUser Tab
// ----------------------------------------------------------------------
class _CloudUserTab extends StatefulWidget {
  const _CloudUserTab();

  @override
  State<_CloudUserTab> createState() => _CloudUserTabState();
}

class _CloudUserTabState extends State<_CloudUserTab> {
  List<Map<String, dynamic>> _cloudUsers = [];
  
  final _userCtrl = TextEditingController();
  final _passCtrl = TextEditingController();
  String _role = 'VIEWER';

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _userCtrl.dispose();
    _passCtrl.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    final db = await DatabaseHelper.instance.database;
    final data = await db.query('cloud_users', orderBy: 'id DESC');
    setState(() => _cloudUsers = data);
  }

  Future<bool> _save({int? id}) async {
    final username = _userCtrl.text.trim();
    if (username.isEmpty) return false;

    final db = await DatabaseHelper.instance.database;

    // Unique check: check if username exists in the local database.
    // If yes, display error "اسم المستخدم موجود مسبقاً." via SnackBar.
    List<Map<String, dynamic>> existing;
    if (id == null) {
      existing = await db.query(
        'cloud_users',
        where: 'username = ?',
        whereArgs: [username],
        limit: 1,
      );
    } else {
      existing = await db.query(
        'cloud_users',
        where: 'username = ? AND id != ?',
        whereArgs: [username, id],
        limit: 1,
      );
    }

    if (existing.isNotEmpty) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text("اسم المستخدم موجود مسبقاً."),
            backgroundColor: ButtonColors.danger,
          ),
        );
      }
      return false;
    }

    final map = {
      'username': username,
      'password': _passCtrl.text,
      'role': _role,
      'created_at': DateTime.now().toIso8601String(),
      'is_synced': 0
    };

    if (id == null) {
      await db.insert('cloud_users', map);
    } else {
      // Don't override created_at
      map.remove('created_at');
      await db.update('cloud_users', map, where: 'id = ?', whereArgs: [id]);
    }

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(id == null ? 'تمت إضافة مستخدم السحابة بنجاح.' : 'تم تعديل مستخدم السحابة بنجاح.'),
        ),
      );
    }

    _load();
    return true;
  }

  Future<void> _deleteCloudUser(int id, String username) async {
    if (!mounted) return;
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('تأكيد الحذف', style: TextStyle(fontWeight: FontWeight.bold)),
          content: Text('هل أنت متأكد من حذف مستخدم السحابة "$username"؟'),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('إلغاء', style: TextStyle(color: FlarelineColors.darkTextBody)),
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
      final db = await DatabaseHelper.instance.database;
      await db.delete('cloud_users', where: 'id = ?', whereArgs: [id]);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('تم حذف مستخدم السحابة "$username" بنجاح.')),
        );
      }
      _load();
    }
  }

  void _showForm([Map<String, dynamic>? c]) {
    if (c != null) {
      _userCtrl.text = c['username'] ?? '';
      _passCtrl.text = c['password'] ?? '';
      _role = c['role'] ?? 'VIEWER';
    } else {
      _userCtrl.clear();
      _passCtrl.clear();
      _role = 'VIEWER';
    }

    final formKey = GlobalKey<FormState>();

    showDialog(
      context: context,
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setModalState) {
            return AlertDialog(
              title: Text(
                c == null ? 'إضافة مستخدم سحابي' : 'تعديل مستخدم سحابي',
                style: const TextStyle(
                  color: FlarelineColors.darkBlackText,
                  fontWeight: FontWeight.bold,
                ),
              ),
              content: SingleChildScrollView(
                child: Form(
                  key: formKey,
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      OutBorderTextFormField(
                        controller: _userCtrl,
                        labelText: 'اسم المستخدم',
                        hintText: 'أدخل اسم المستخدم',
                        validator: (value) {
                          if (value == null || value.trim().isEmpty) {
                            return 'اسم المستخدم مطلوب';
                          }
                          return null;
                        },
                      ),
                      const SizedBox(height: 12),
                      OutBorderTextFormField(
                        controller: _passCtrl,
                        labelText: 'كلمة المرور',
                        hintText: 'أدخل كلمة المرور',
                        obscureText: true,
                        validator: (value) {
                          if (value == null || value.isEmpty) {
                            return 'كلمة المرور مطلوبة';
                          }
                          return null;
                        },
                      ),
                      const SizedBox(height: 12),
                      DropdownButtonFormField<String>(
                        initialValue: _role,
                        items: const [
                          DropdownMenuItem(value: 'VIEWER', child: Text('مراقب')),
                          DropdownMenuItem(value: 'CASHIER', child: Text('كاشير')),
                        ],
                        onChanged: (val) => setModalState(() => _role = val!),
                        decoration: const InputDecoration(
                          labelText: 'الدور',
                          border: OutlineInputBorder(
                            borderSide: BorderSide(color: FlarelineColors.border, width: 1),
                          ),
                          enabledBorder: OutlineInputBorder(
                            borderSide: BorderSide(color: FlarelineColors.border, width: 1),
                          ),
                        ),
                      )
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
                  style: ElevatedButton.styleFrom(
                    backgroundColor: ButtonColors.primary,
                  ),
                  onPressed: () async {
                    if (formKey.currentState!.validate()) {
                      final navigator = Navigator.of(context);
                      bool success = await _save(id: c?['id']);
                      if (success && navigator.mounted) {
                        navigator.pop();
                      }
                    }
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
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showForm(),
        backgroundColor: ButtonColors.primary,
        child: const Icon(Icons.add, color: Colors.white),
      ),
      body: _cloudUsers.isEmpty
          ? const Center(
              child: Text(
                'لا يوجد مستخدمين سحابيين بعد.',
                style: TextStyle(
                  color: FlarelineColors.darkTextBody,
                  fontSize: 16,
                ),
              ),
            )
          : ListView.builder(
              padding: const EdgeInsets.symmetric(vertical: 12),
              itemCount: _cloudUsers.length,
              itemBuilder: (context, index) {
                final c = _cloudUsers[index];
                return CommonCard(
                  margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
                  padding: const EdgeInsets.all(8),
                  child: ListTile(
                    title: Text(
                      c['username'],
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: FlarelineColors.darkBlackText,
                      ),
                    ),
                    subtitle: Text(
                      'الدور: ${c['role']}',
                      style: const TextStyle(color: FlarelineColors.darkTextBody),
                    ),
                    trailing: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        IconButton(
                          icon: const Icon(Icons.edit, color: ButtonColors.secondary),
                          onPressed: () => _showForm(c),
                        ),
                        IconButton(
                          icon: const Icon(Icons.delete, color: ButtonColors.danger),
                          onPressed: () => _deleteCloudUser(c['id'], c['username']),
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
