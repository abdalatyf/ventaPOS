import 'package:flutter_test/flutter_test.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';
import 'package:sales_app_offline/db/database_helper.dart';
import 'package:sales_app_offline/services/sync_worker.dart';

void main() {
  // Initialize FFI for tests
  sqfliteFfiInit();
  databaseFactory = databaseFactoryFfi;

  group('SyncWorker Tests', () {
    test('syncNow returns true when there are no pending items to sync', () async {
      final dbHelper = DatabaseHelper();
      final db = await dbHelper.database;
      
      // Clean pending sync states
      await db.delete('pending_sync_states');

      // Call syncNow and verify it returns true
      final syncResult = await SyncWorker().syncNow();
      expect(syncResult, isTrue);
    });
  });
}
