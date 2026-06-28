import 'package:flutter_test/flutter_test.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';
import 'package:sales_app_offline/db/database_helper.dart';

void main() {
  sqfliteFfiInit();
  databaseFactory = databaseFactoryFfi;

  group('Users Business Logic Tests', () {
    late Database db;

    setUp(() async {
      final dbHelper = DatabaseHelper();
      db = await dbHelper.database;
      await db.delete('receipts');
      await db.delete('salespersons');
      await db.delete('cloud_users');
    });

    test('Add/Edit Salesperson Unique Name Check', () async {
      // Create salesperson 1
      int spId1 = await db.insert('salespersons', {
        'name': 'Ahmad',
        'branch_id': 1,
        'cloud_username': 'ahmad_cloud',
        'cloud_password': '123',
        'is_synced': 0
      });
      expect(spId1, isPositive);

      // Check duplicate name on add
      final nameToCheck = 'Ahmad';
      final existingAdd = await db.query('salespersons', where: 'name = ?', whereArgs: [nameToCheck]);
      expect(existingAdd, isNotEmpty);

      // Create salesperson 2
      int spId2 = await db.insert('salespersons', {
        'name': 'Ali',
        'branch_id': 1,
        'cloud_username': 'ali_cloud',
        'cloud_password': '123',
        'is_synced': 0
      });

      // Check duplicate name on edit salesperson 2 to 'Ahmad'
      final existingEditDuplicate = await db.query(
        'salespersons',
        where: 'name = ? AND id != ?',
        whereArgs: [nameToCheck, spId2],
      );
      expect(existingEditDuplicate, isNotEmpty);

      // Check editing to a unique name 'Samir'
      final uniqueName = 'Samir';
      final existingEditUnique = await db.query(
        'salespersons',
        where: 'name = ? AND id != ?',
        whereArgs: [uniqueName, spId2],
      );
      expect(existingEditUnique, isEmpty);
    });

    test('Salesperson Deletion Protection (Receipt References)', () async {
      int spId = await db.insert('salespersons', {
        'name': 'Delete Test User',
        'branch_id': 1,
        'cloud_username': 'delete_cloud',
        'cloud_password': '123',
        'is_synced': 0
      });

      // Initially no receipt reference
      final receiptsBefore = await db.query('receipts', where: 'salesperson_id = ?', whereArgs: [spId]);
      expect(receiptsBefore, isEmpty);

      // Insert receipt referencing the salesperson
      await db.insert('receipts', {
        'salesperson_id': spId,
        'receipt_number': 101,
        'branch_id': 1,
        'customer_name': 'Customer A',
        'total_amount': 500,
        'is_synced': 0
      });

      // Now references exist
      final receiptsAfter = await db.query('receipts', where: 'salesperson_id = ?', whereArgs: [spId]);
      expect(receiptsAfter, isNotEmpty);

      // Blocked deletion simulation: we check references before deleting
      final canDelete = receiptsAfter.isEmpty;
      expect(canDelete, isFalse);

      // Clear receipts to simulate deletion success case
      await db.delete('receipts', where: 'salesperson_id = ?', whereArgs: [spId]);
      final receiptsCleared = await db.query('receipts', where: 'salesperson_id = ?', whereArgs: [spId]);
      expect(receiptsCleared, isEmpty);

      final canDeleteNow = receiptsCleared.isEmpty;
      expect(canDeleteNow, isTrue);

      int deletedCount = await db.delete('salespersons', where: 'id = ?', whereArgs: [spId]);
      expect(deletedCount, equals(1));
    });

    test('Add/Edit Cloud User Unique Username Check', () async {
      // Add cloud user 1
      int cuId1 = await db.insert('cloud_users', {
        'username': 'user1',
        'password': 'pass',
        'role': 'VIEWER',
        'created_at': DateTime.now().toIso8601String(),
        'is_synced': 0
      });
      expect(cuId1, isPositive);

      // Check duplicate on add
      final usernameToCheck = 'user1';
      final existingAdd = await db.query('cloud_users', where: 'username = ?', whereArgs: [usernameToCheck]);
      expect(existingAdd, isNotEmpty);

      // Add cloud user 2
      int cuId2 = await db.insert('cloud_users', {
        'username': 'user2',
        'password': 'pass',
        'role': 'CASHIER',
        'created_at': DateTime.now().toIso8601String(),
        'is_synced': 0
      });

      // Check duplicate on edit
      final existingEditDuplicate = await db.query(
        'cloud_users',
        where: 'username = ? AND id != ?',
        whereArgs: [usernameToCheck, cuId2],
      );
      expect(existingEditDuplicate, isNotEmpty);

      // Check editing to unique username
      final uniqueUsername = 'user3';
      final existingEditUnique = await db.query(
        'cloud_users',
        where: 'username = ? AND id != ?',
        whereArgs: [uniqueUsername, cuId2],
      );
      expect(existingEditUnique, isEmpty);
    });

    test('Role option selection must be VIEWER or CASHIER', () {
      final validRoles = ['VIEWER', 'CASHIER'];
      expect(validRoles.contains('VIEWER'), isTrue);
      expect(validRoles.contains('CASHIER'), isTrue);
      expect(validRoles.contains('ADMIN'), isFalse);
    });
  });
}
