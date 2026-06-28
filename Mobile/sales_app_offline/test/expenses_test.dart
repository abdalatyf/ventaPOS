import 'package:flutter_test/flutter_test.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';
import 'package:sales_app_offline/db/database_helper.dart';

void main() {
  sqfliteFfiInit();
  databaseFactory = databaseFactoryFfi;

  group('Expenses Business Logic Tests', () {
    late Database db;

    setUp(() async {
      final dbHelper = DatabaseHelper();
      db = await dbHelper.database;
      await db.delete('expenses');
      await db.delete('receipts');
    });

    test('Default Month/Year from Last Receipt fallback to System Date', () async {
      // 1. Fallback when there are no receipts
      final lastReceiptListBefore = await db.query(
        'receipts',
        orderBy: 'sale_year DESC, sale_month DESC',
        limit: 1,
      );
      expect(lastReceiptListBefore, isEmpty);
      
      int defaultYearFallback = DateTime.now().year;
      int defaultMonthFallback = DateTime.now().month;

      // 2. Query last receipt after inserting receipts
      await db.insert('receipts', {
        'receipt_number': 1001,
        'source': 'MOBILE',
        'branch_id': 1,
        'customer_name': 'Test Cust',
        'total_amount': 2000,
        'sale_year': 2024,
        'sale_month': 11,
        'salesperson_id': 1,
        'is_synced': 1
      });

      await db.insert('receipts', {
        'receipt_number': 1002,
        'source': 'MOBILE',
        'branch_id': 1,
        'customer_name': 'Test Cust 2',
        'total_amount': 3000,
        'sale_year': 2025,
        'sale_month': 4,
        'salesperson_id': 1,
        'is_synced': 1
      });

      final lastReceiptListAfter = await db.query(
        'receipts',
        orderBy: 'sale_year DESC, sale_month DESC',
        limit: 1,
      );
      expect(lastReceiptListAfter, isNotEmpty);
      
      final lastReceipt = lastReceiptListAfter.first;
      int defaultYearFromReceipt = lastReceipt['sale_year'] as int;
      int defaultMonthFromReceipt = lastReceipt['sale_month'] as int;

      expect(defaultYearFromReceipt, equals(2025));
      expect(defaultMonthFromReceipt, equals(4));
    });

    test('Add, Filter, Aggregate (Total Sum), and Delete Expenses', () async {
      // 1. Add some expenses in different months
      await db.insert('expenses', {
        'branch_id': 1,
        'amount': 150.0,
        'description': 'Office Supplies',
        'expense_year': 2025,
        'expense_month': 4,
        'created_at': DateTime.now().toIso8601String(),
        'is_synced': 0
      });

      await db.insert('expenses', {
        'branch_id': 1,
        'amount': 350.0,
        'description': 'Electricity',
        'expense_year': 2025,
        'expense_month': 4,
        'created_at': DateTime.now().toIso8601String(),
        'is_synced': 0
      });

      await db.insert('expenses', {
        'branch_id': 1,
        'amount': 500.0,
        'description': 'Rent',
        'expense_year': 2025,
        'expense_month': 5,
        'created_at': DateTime.now().toIso8601String(),
        'is_synced': 0
      });

      // 2. Query and Aggregate for 2025-04
      final expensesApril = await db.query(
        'expenses',
        where: 'expense_year = ? AND expense_month = ?',
        whereArgs: [2025, 4],
      );
      expect(expensesApril.length, equals(2));

      double totalApril = 0.0;
      for (var row in expensesApril) {
        totalApril += (row['amount'] as num).toDouble();
      }
      expect(totalApril, equals(500.0));

      // 3. Query and Aggregate for 2025-05
      final expensesMay = await db.query(
        'expenses',
        where: 'expense_year = ? AND expense_month = ?',
        whereArgs: [2025, 5],
      );
      expect(expensesMay.length, equals(1));

      double totalMay = 0.0;
      for (var row in expensesMay) {
        totalMay += (row['amount'] as num).toDouble();
      }
      expect(totalMay, equals(500.0));

      // 4. Delete an expense
      final targetExpenseId = expensesApril.first['id'] as int;
      await db.delete(
        'expenses',
        where: 'id = ?',
        whereArgs: [targetExpenseId],
      );

      final expensesAprilPostDelete = await db.query(
        'expenses',
        where: 'expense_year = ? AND expense_month = ?',
        whereArgs: [2025, 4],
      );
      expect(expensesAprilPostDelete.length, equals(1));
    });
  });
}
