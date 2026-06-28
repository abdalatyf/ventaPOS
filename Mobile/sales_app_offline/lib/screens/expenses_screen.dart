import 'package:flutter/material.dart';
import '../db/database_helper.dart';
import 'package:flareline_uikit/components/card/common_card.dart';
import 'package:flareline_uikit/components/forms/outborder_text_form_field.dart';
import 'package:flareline_uikit/core/theme/flareline_colors.dart';

class ExpensesScreen extends StatefulWidget {
  const ExpensesScreen({super.key});

  @override
  State<ExpensesScreen> createState() => _ExpensesScreenState();
}

class _ExpensesScreenState extends State<ExpensesScreen> {
  final _formKey = GlobalKey<FormState>();

  double _amount = 0.0;
  String _description = '';
  int _expenseMonth = DateTime.now().month;
  int _expenseYear = DateTime.now().year;

  int _selectedMonth = DateTime.now().month;
  int _selectedYear = DateTime.now().year;
  List<int> _availableYears = [DateTime.now().year];
  double _totalExpenses = 0.0;

  List<Map<String, dynamic>> _expenses = [];

  @override
  void initState() {
    super.initState();
    _initData();
  }

  Future<void> _initData() async {
    final db = await DatabaseHelper.instance.database;

    // Fetch the last receipt to set default filters
    final lastReceiptList = await db.query(
      'receipts',
      orderBy: 'sale_year DESC, sale_month DESC',
      limit: 1,
    );

    int defaultYear = DateTime.now().year;
    int defaultMonth = DateTime.now().month;

    if (lastReceiptList.isNotEmpty) {
      final lastReceipt = lastReceiptList.first;
      defaultYear = lastReceipt['sale_year'] as int? ?? defaultYear;
      defaultMonth = lastReceipt['sale_month'] as int? ?? defaultMonth;
    }

    // Fetch unique receipt years for the available years dropdown
    final receiptYearsQuery = await db.rawQuery('SELECT DISTINCT sale_year FROM receipts');
    final receiptYears = receiptYearsQuery
        .map((row) => row['sale_year'] as int?)
        .where((y) => y != null)
        .cast<int>()
        .toList();

    final yearsSet = {DateTime.now().year, defaultYear, ...receiptYears};
    final availableYears = yearsSet.toList();
    availableYears.sort((a, b) => b.compareTo(a));

    setState(() {
      _selectedYear = defaultYear;
      _selectedMonth = defaultMonth;
      _availableYears = availableYears;
    });

    await _loadExpenses();
  }

  Future<void> _loadExpenses() async {
    final db = await DatabaseHelper.instance.database;
    final data = await db.query(
      'expenses',
      where: 'expense_year = ? AND expense_month = ?',
      whereArgs: [_selectedYear, _selectedMonth],
      orderBy: 'id DESC',
    );

    double total = 0.0;
    for (var row in data) {
      total += (row['amount'] as num?)?.toDouble() ?? 0.0;
    }

    setState(() {
      _expenses = data;
      _totalExpenses = total;
    });
  }

  Future<void> _saveExpense() async {
    if (!_formKey.currentState!.validate()) return;
    _formKey.currentState!.save();

    final db = await DatabaseHelper.instance.database;
    await db.insert('expenses', {
      'branch_id': 1, // Dummy
      'amount': _amount,
      'description': _description,
      'expense_year': _expenseYear,
      'expense_month': _expenseMonth,
      'created_at': DateTime.now().toIso8601String(),
      'is_synced': 0
    });

    if (!_availableYears.contains(_expenseYear)) {
      _availableYears.add(_expenseYear);
      _availableYears.sort((a, b) => b.compareTo(a));
    }

    setState(() {
      _selectedMonth = _expenseMonth;
      _selectedYear = _expenseYear;
    });

    await _loadExpenses();
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('تم إضافة المصروف بنجاح / Expense Added!')),
      );
    }
  }

  Future<void> _deleteExpense(int id) async {
    final db = await DatabaseHelper.instance.database;
    await db.delete(
      'expenses',
      where: 'id = ?',
      whereArgs: [id],
    );
    await _loadExpenses();
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('تم حذف المصروف بنجاح / Expense Deleted!')),
      );
    }
  }

  void _confirmDelete(int id, String description) {
    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('حذف المصروف / Delete Expense'),
          content: Text('هل أنت متأكد من حذف "$description"؟\nAre you sure you want to delete "$description"?'),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('إلغاء / Cancel', style: TextStyle(color: FlarelineColors.darkTextBody)),
            ),
            ElevatedButton(
              style: ElevatedButton.styleFrom(backgroundColor: ButtonColors.danger),
              onPressed: () {
                _deleteExpense(id);
                Navigator.pop(context);
              },
              child: const Text('حذف / Delete', style: TextStyle(color: Colors.white)),
            ),
          ],
        );
      },
    );
  }

  void _showForm() {
    _amount = 0.0;
    _description = '';
    _expenseMonth = _selectedMonth;
    _expenseYear = _selectedYear;

    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text(
            'إضافة مصروف / Add Expense',
            style: TextStyle(
              color: FlarelineColors.darkBlackText,
              fontWeight: FontWeight.bold,
            ),
          ),
          content: SingleChildScrollView(
            child: Form(
              key: _formKey,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  OutBorderTextFormField(
                    labelText: 'Amount / المبلغ',
                    hintText: 'أدخل المبلغ',
                    keyboardType: TextInputType.number,
                    validator: (val) => val == null || val.trim().isEmpty ? 'المبلغ مطلوب / Required' : null,
                    onSaved: (val) => _amount = double.tryParse(val!) ?? 0.0,
                  ),
                  const SizedBox(height: 12),
                  OutBorderTextFormField(
                    labelText: 'Description / الوصف',
                    hintText: 'أدخل الوصف',
                    validator: (val) => val == null || val.trim().isEmpty ? 'الوصف مطلوب / Required' : null,
                    onSaved: (val) => _description = val!,
                  ),
                  const SizedBox(height: 12),
                  OutBorderTextFormField(
                    labelText: 'Month / الشهر',
                    hintText: 'أدخل الشهر',
                    keyboardType: TextInputType.number,
                    initialValue: _expenseMonth.toString(),
                    validator: (val) {
                      if (val == null || val.trim().isEmpty) return 'الشهر مطلوب / Required';
                      final m = int.tryParse(val);
                      if (m == null || m < 1 || m > 12) return 'شهر غير صالح / Invalid Month';
                      return null;
                    },
                    onSaved: (val) => _expenseMonth = int.tryParse(val!) ?? _expenseMonth,
                  ),
                  const SizedBox(height: 12),
                  OutBorderTextFormField(
                    labelText: 'Year / السنة',
                    hintText: 'أدخل السنة',
                    keyboardType: TextInputType.number,
                    initialValue: _expenseYear.toString(),
                    validator: (val) {
                      if (val == null || val.trim().isEmpty) return 'السنة مطلوبة / Required';
                      final y = int.tryParse(val);
                      if (y == null || y < 1900) return 'سنة غير صالحة / Invalid Year';
                      return null;
                    },
                    onSaved: (val) => _expenseYear = int.tryParse(val!) ?? _expenseYear,
                  ),
                ],
              ),
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancel / إلغاء', style: TextStyle(color: FlarelineColors.darkTextBody)),
            ),
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: ButtonColors.primary,
              ),
              onPressed: () {
                if (_formKey.currentState!.validate()) {
                  _saveExpense();
                  Navigator.pop(context);
                }
              },
              child: const Text('Save / حفظ', style: TextStyle(color: Colors.white)),
            ),
          ],
        );
      },
    );
  }

  Widget _buildFilterCard() {
    return CommonCard(
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              Expanded(
                child: DropdownButtonFormField<int>(
                  value: _selectedMonth,
                  decoration: const InputDecoration(
                    labelText: 'الشهر / Month',
                    border: OutlineInputBorder(),
                  ),
                  items: List.generate(12, (index) => index + 1).map((m) {
                    return DropdownMenuItem<int>(
                      value: m,
                      child: Text(m.toString()),
                    );
                  }).toList(),
                  onChanged: (val) {
                    if (val != null) {
                      setState(() {
                        _selectedMonth = val;
                      });
                      _loadExpenses();
                    }
                  },
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: DropdownButtonFormField<int>(
                  value: _selectedYear,
                  decoration: const InputDecoration(
                    labelText: 'السنة / Year',
                    border: OutlineInputBorder(),
                  ),
                  items: _availableYears.map((y) {
                    return DropdownMenuItem<int>(
                      value: y,
                      child: Text(y.toString()),
                    );
                  }).toList(),
                  onChanged: (val) {
                    if (val != null) {
                      setState(() {
                        _selectedYear = val;
                      });
                      _loadExpenses();
                    }
                  },
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'إجمالي المصروفات / Total Expenses:',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: FlarelineColors.darkBlackText,
                ),
              ),
              Text(
                _totalExpenses.toStringAsFixed(2),
                style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: ButtonColors.danger,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: FlarelineColors.background,
      appBar: AppBar(
        title: const Text('إدارة المصروفات / Manage Expenses'),
        backgroundColor: FlarelineColors.primary,
        foregroundColor: Colors.white,
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _showForm,
        backgroundColor: ButtonColors.primary,
        child: const Icon(Icons.add, color: Colors.white),
      ),
      body: Column(
        children: [
          _buildFilterCard(),
          Expanded(
            child: _expenses.isEmpty
                ? const Center(
                    child: Text(
                      'لا يوجد مصروفات لهذا الشهر.\nNo expenses for this month.',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        color: FlarelineColors.darkTextBody,
                        fontSize: 16,
                      ),
                    ),
                  )
                : ListView.builder(
                    padding: const EdgeInsets.symmetric(vertical: 8),
                    itemCount: _expenses.length,
                    itemBuilder: (context, index) {
                      final e = _expenses[index];
                      return CommonCard(
                        margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
                        padding: const EdgeInsets.all(8),
                        child: ListTile(
                          leading: const CircleAvatar(
                            backgroundColor: Colors.redAccent,
                            child: Icon(Icons.money_off, color: Colors.white),
                          ),
                          title: Text(
                            e['description'] ?? '',
                            style: const TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                              color: FlarelineColors.darkBlackText,
                            ),
                          ),
                          subtitle: Text(
                            'المبلغ: ${e['amount']} | التاريخ: ${e['expense_month']}/${e['expense_year']}',
                            style: const TextStyle(
                              color: FlarelineColors.darkTextBody,
                            ),
                          ),
                          trailing: IconButton(
                            icon: const Icon(Icons.delete, color: Colors.red),
                            onPressed: () => _confirmDelete(e['id'], e['description'] ?? ''),
                          ),
                        ),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }
}

