import 'package:flutter_test/flutter_test.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';
import 'package:sales_app_offline/db/database_helper.dart';

void main() {
  // Initialize FFI for tests
  sqfliteFfiInit();
  databaseFactory = databaseFactoryFfi;

  group('DatabaseHelper Config Tests', () {
    test('setConfig and getConfig test', () async {
      final dbHelper = DatabaseHelper();
      final db = await dbHelper.database;
      await db.delete('config');

      // Test config set & get
      await dbHelper.setConfig('test_key', 'test_value');
      final val = await dbHelper.getConfig('test_key');
      expect(val, equals('test_value'));

      // Test active role setup
      await dbHelper.setConfig('role_key', 'some_val', activeRole: 'MANAGER');
      final roleVal = await dbHelper.getConfig('role');
      expect(roleVal, equals('MANAGER'));
    });

    test('getIdentity test', () async {
      final dbHelper = DatabaseHelper();
      final db = await dbHelper.database;
      await db.delete('config');
      await db.delete('salespersons');

      // Set salesperson in config
      await dbHelper.setConfig('salesperson_id', '42');
      // If salesperson not in table, returns fallback map
      final identityMap = await dbHelper.getIdentity();
      expect(identityMap, isNotNull);
      expect(identityMap!['salesperson_id'], equals('42'));

      // Insert salesperson in table
      await db.insert('salespersons', {
        'id': 42,
        'name': 'Test User',
        'branch_id': 1,
        'is_synced': 0
      });

      final identityMap2 = await dbHelper.getIdentity();
      expect(identityMap2, isNotNull);
      expect(identityMap2!['id'], equals(42));
      expect(identityMap2['name'], equals('Test User'));
    });
  });

  group('DatabaseHelper Receipts and Products Tests', () {
    test('upsertReceipt and export tests', () async {
      final dbHelper = DatabaseHelper();
      final db = await dbHelper.database;
      await db.delete('receipts');

      final receiptData = {
        'id': 101,
        'customer_name': 'Test Customer',
        'total_amount': 500,
        'is_synced': 0,
      };

      await dbHelper.upsertReceipt(receiptData);

      final queryRes = await db.query('receipts', where: 'id = ?', whereArgs: [101]);
      expect(queryRes, isNotEmpty);
      expect(queryRes.first['customer_name'], equals('Test Customer'));

      // Mark as exported
      await dbHelper.markAsExported(101);
      final queryRes2 = await db.query('receipts', where: 'id = ?', whereArgs: [101]);
      expect(queryRes2.first['is_synced'], equals(1));

      // Delete all exported receipts
      await dbHelper.deleteAllExportedReceipts();
      final queryRes3 = await db.query('receipts', where: 'id = ?', whereArgs: [101]);
      expect(queryRes3, isEmpty);
    });

    test('upsertProduct test', () async {
      final dbHelper = DatabaseHelper();
      final db = await dbHelper.database;
      await db.delete('inventory');

      final productData = {
        'id': 202,
        'name': 'Test Product',
        'initial_quantity': 10,
        'is_synced': 0,
      };

      await dbHelper.upsertProduct(productData);

      final queryRes = await db.query('inventory', where: 'id = ?', whereArgs: [202]);
      expect(queryRes, isNotEmpty);
      expect(queryRes.first['name'], equals('Test Product'));

      await dbHelper.markInventoryAsSynced(202);
      final queryRes2 = await db.query('inventory', where: 'id = ?', whereArgs: [202]);
      expect(queryRes2.first['is_synced'], equals(1));
    });
  });

  group('DatabaseHelper Sync States Tests', () {
    test('pending sync states test', () async {
      final dbHelper = DatabaseHelper();
      final db = await dbHelper.database;
      await db.delete('pending_sync_states');

      // Insert manually
      final id = await db.insert('pending_sync_states', {
        'entity_type': 'receipt',
        'entity_local_id': 101,
        'action': 'CREATE',
        'payload_json': '{}',
        'retry_count': 0,
      });

      final pending = await dbHelper.getPendingSyncStatesToProcess();
      expect(pending, isNotEmpty);
      expect(pending.first['id'], equals(id));

      await dbHelper.incrementSyncRetryCount(id, 'Error message');
      final pending2 = await dbHelper.getPendingSyncStatesToProcess();
      expect(pending2.first['retry_count'], equals(1));
      expect(pending2.first['error_message'], equals('Error message'));

      await dbHelper.deletePendingSyncState(id);
      final pending3 = await dbHelper.getPendingSyncStatesToProcess();
      expect(pending3, isEmpty);
    });
  });
}
