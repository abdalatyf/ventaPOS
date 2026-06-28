import 'package:flutter_test/flutter_test.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';
import 'package:sales_app_offline/db/database_helper.dart';

void main() {
  sqfliteFfiInit();
  databaseFactory = databaseFactoryFfi;

  group('Supplier Business Logic Tests', () {
    late Database db;

    setUp(() async {
      final dbHelper = DatabaseHelper();
      db = await dbHelper.database;
      await db.delete('purchase_invoices');
      await db.delete('suppliers');
    });

    test('Add and Edit Supplier with Unique Check Validation', () async {
      int sId1 = await db.insert('suppliers', {'name': 'Supplier A', 'is_synced': 0});
      expect(sId1, isPositive);

      final list = await db.query('suppliers', where: 'id = ?', whereArgs: [sId1]);
      expect(list.first['name'], equals('Supplier A'));

      final nameToCheck = 'Supplier A';
      final existingAdd = await db.query('suppliers', where: 'name = ?', whereArgs: [nameToCheck]);
      expect(existingAdd, isNotEmpty);

      int sId2 = await db.insert('suppliers', {'name': 'Supplier B', 'is_synced': 0});
      final renameToCheck = 'Supplier A';
      final existingEdit = await db.query('suppliers', where: 'name = ? AND id != ?', whereArgs: [renameToCheck, sId2]);
      expect(existingEdit, isNotEmpty);
      
      final validRename = 'Supplier C';
      final existingEditValid = await db.query('suppliers', where: 'name = ? AND id != ?', whereArgs: [validRename, sId2]);
      expect(existingEditValid, isEmpty);
    });

    test('Delete Supplier with Deletion Validation', () async {
      int sId = await db.insert('suppliers', {'name': 'Supplier Delete Test', 'is_synced': 0});
      
      final invoicesBefore = await db.query('purchase_invoices', where: 'supplier_id = ?', whereArgs: [sId]);
      expect(invoicesBefore, isEmpty);
      
      await db.insert('purchase_invoices', {
        'invoice_number': 12345,
        'invoice_month': 6,
        'invoice_year': 2026,
        'invoice_type': 'PURCHASE',
        'supplier_id': sId,
        'is_synced': 0
      });

      final invoicesAfter = await db.query('purchase_invoices', where: 'supplier_id = ?', whereArgs: [sId]);
      expect(invoicesAfter, isNotEmpty);
      
      await db.delete('purchase_invoices', where: 'supplier_id = ?', whereArgs: [sId]);
      
      final invoicesCleared = await db.query('purchase_invoices', where: 'supplier_id = ?', whereArgs: [sId]);
      expect(invoicesCleared, isEmpty);
      
      int deletedCount = await db.delete('suppliers', where: 'id = ?', whereArgs: [sId]);
      expect(deletedCount, equals(1));
    });
  });
}
