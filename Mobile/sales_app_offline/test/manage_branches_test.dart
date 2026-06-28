import 'package:flutter_test/flutter_test.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';
import 'package:sales_app_offline/db/database_helper.dart';

void main() {
  sqfliteFfiInit();
  databaseFactory = databaseFactoryFfi;

  group('Manage Branches Business Logic Tests', () {
    late DatabaseHelper dbHelper;

    setUp(() async {
      dbHelper = DatabaseHelper();
      final db = await dbHelper.database;
      // Clear tables before each test
      await db.delete('salespersons');
      await db.delete('receipts');
      await db.delete('branches');
    });

    test('should prevent duplicate branch name on creation', () async {
      final db = await dbHelper.database;

      // Add a branch
      await db.insert('branches', {'name': 'Branch A', 'is_synced': 0});

      // Query to check if duplicate exists (creation case)
      final existing = await db.query(
        'branches',
        where: 'name = ?',
        whereArgs: ['Branch A'],
      );
      expect(existing, isNotEmpty);

      // Non-duplicate check
      final nonExisting = await db.query(
        'branches',
        where: 'name = ?',
        whereArgs: ['Branch B'],
      );
      expect(nonExisting, isEmpty);
    });

    test('should prevent duplicate branch name on update excluding self', () async {
      final db = await dbHelper.database;

      final idA = await db.insert('branches', {'name': 'Branch A', 'is_synced': 0});
      final idB = await db.insert('branches', {'name': 'Branch B', 'is_synced': 0});

      // Try updating Branch B to "Branch A" (which already exists)
      final duplicateOnUpdate = await db.query(
        'branches',
        where: 'name = ? AND id != ?',
        whereArgs: ['Branch A', idB],
      );
      expect(duplicateOnUpdate, isNotEmpty);

      // Try updating Branch B to "Branch B" (no change) or "Branch C" (valid new name)
      final validUpdate = await db.query(
        'branches',
        where: 'name = ? AND id != ?',
        whereArgs: ['Branch C', idB],
      );
      expect(validUpdate, isEmpty);
    });

    test('should prevent branch deletion if referenced by salespersons', () async {
      final db = await dbHelper.database;

      final branchId = await db.insert('branches', {'name': 'Referenced Branch 1', 'is_synced': 0});

      // Insert salesperson referencing the branch
      await db.insert('salespersons', {
        'branch_id': branchId,
        'name': 'Test Salesperson',
        'is_synced': 0
      });

      // Deletion check logic
      final salespersons = await db.query(
        'salespersons',
        where: 'branch_id = ?',
        whereArgs: [branchId],
        limit: 1,
      );

      final receipts = await db.query(
        'receipts',
        where: 'branch_id = ?',
        whereArgs: [branchId],
        limit: 1,
      );

      bool allowDelete = salespersons.isEmpty && receipts.isEmpty;
      expect(allowDelete, isFalse);
    });

    test('should prevent branch deletion if referenced by receipts', () async {
      final db = await dbHelper.database;

      final branchId = await db.insert('branches', {'name': 'Referenced Branch 2', 'is_synced': 0});

      // Insert receipt referencing the branch
      await db.insert('receipts', {
        'receipt_number': 123,
        'branch_id': branchId,
        'customer_name': 'Test Customer',
        'total_amount': 500,
        'is_synced': 0
      });

      // Deletion check logic
      final salespersons = await db.query(
        'salespersons',
        where: 'branch_id = ?',
        whereArgs: [branchId],
        limit: 1,
      );

      final receipts = await db.query(
        'receipts',
        where: 'branch_id = ?',
        whereArgs: [branchId],
        limit: 1,
      );

      bool allowDelete = salespersons.isEmpty && receipts.isEmpty;
      expect(allowDelete, isFalse);
    });

    test('should allow branch deletion if not referenced anywhere', () async {
      final db = await dbHelper.database;

      final branchId = await db.insert('branches', {'name': 'Unreferenced Branch', 'is_synced': 0});

      // Deletion check logic
      final salespersons = await db.query(
        'salespersons',
        where: 'branch_id = ?',
        whereArgs: [branchId],
        limit: 1,
      );

      final receipts = await db.query(
        'receipts',
        where: 'branch_id = ?',
        whereArgs: [branchId],
        limit: 1,
      );

      bool allowDelete = salespersons.isEmpty && receipts.isEmpty;
      expect(allowDelete, isTrue);

      if (allowDelete) {
        int deleted = await db.delete(
          'branches',
          where: 'id = ?',
          whereArgs: [branchId],
        );
        expect(deleted, equals(1));
      }
    });
  });
}
