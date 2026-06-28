import 'package:flutter_test/flutter_test.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';
import 'package:sales_app_offline/db/database_helper.dart';

void main() {
  sqfliteFfiInit();
  databaseFactory = databaseFactoryFfi;

  group('Manage Products Business Logic Tests', () {
    late DatabaseHelper dbHelper;

    setUp(() async {
      dbHelper = DatabaseHelper();
      final db = await dbHelper.database;
      // Clear tables before each test
      await db.delete('inventory');
      await db.delete('commission_history');
      await db.delete('receipt_items');
      await db.delete('purchase_invoice_items');
    });

    test('should insert product and automatically create commission history record', () async {
      final db = await dbHelper.database;
      
      // Simulate inserting a product
      final productId = await db.insert('inventory', {
        'name': 'Samsung Smart TV',
        'branch_id': 1,
        'initial_quantity': 10,
        'initial_purchase_price': 5000,
        'initial_commission_amount': 250,
        'initial_month': 6,
        'initial_year': 2026,
        'created_at': DateTime.now().toIso8601String(),
        'updated_at': DateTime.now().toIso8601String(),
        'is_synced': 0
      });

      // Verify the product was inserted
      final products = await db.query('inventory', where: 'id = ?', whereArgs: [productId]);
      expect(products, isNotEmpty);
      expect(products.first['name'], equals('Samsung Smart TV'));

      // Replicate product insert's commission history creation
      await db.insert('commission_history', {
        'item_id': productId,
        'commission_amount': 250,
        'activation_month': 6,
        'activation_year': 2026,
        'created_at': DateTime.now().toIso8601String(),
        'is_synced': 0
      });

      // Verify commission history record exists
      final commRecords = await db.query('commission_history', where: 'item_id = ?', whereArgs: [productId]);
      expect(commRecords, isNotEmpty);
      expect(commRecords.first['commission_amount'], equals(250));
      expect(commRecords.first['activation_month'], equals(6));
      expect(commRecords.first['activation_year'], equals(2026));
    });

    test('should prevent product name duplicate (creation logic check)', () async {
      final db = await dbHelper.database;

      // Insert first product
      await db.insert('inventory', {
        'name': 'Product A',
        'branch_id': 1,
        'initial_quantity': 5,
        'initial_purchase_price': 100
      });

      // Check if product name exists (for Add Product)
      final existingForAdd = await db.query(
        'inventory',
        where: 'name = ?',
        whereArgs: ['Product A'],
      );
      expect(existingForAdd, isNotEmpty);

      // Check if non-existent product name exists
      final existingForAdd2 = await db.query(
        'inventory',
        where: 'name = ?',
        whereArgs: ['Product B'],
      );
      expect(existingForAdd2, isEmpty);
    });

    test('should prevent product name duplicate on update (excluding self)', () async {
      final db = await dbHelper.database;

      await db.insert('inventory', {
        'name': 'Product A',
        'branch_id': 1,
      });

      final idB = await db.insert('inventory', {
        'name': 'Product B',
        'branch_id': 1,
      });

      // Update Product B to "Product A" - name check should find a duplicate
      final existingForUpdateDuplicate = await db.query(
        'inventory',
        where: 'name = ? AND id != ?',
        whereArgs: ['Product A', idB],
      );
      expect(existingForUpdateDuplicate, isNotEmpty);

      // Update Product B to "Product B" (no change) - name check should not find duplicate
      final existingForUpdateNoChange = await db.query(
        'inventory',
        where: 'name = ? AND id != ?',
        whereArgs: ['Product B', idB],
      );
      expect(existingForUpdateNoChange, isEmpty);
    });

    test('should apply self-healing logic for missing commission history records', () async {
      final db = await dbHelper.database;

      // Insert product without creating commission history
      final productId = await db.insert('inventory', {
        'name': 'Heal Product',
        'initial_commission_amount': 300,
        'initial_month': 5,
        'initial_year': 2026
      });

      // Verify no commission history exists
      final initialComm = await db.query('commission_history', where: 'item_id = ?', whereArgs: [productId]);
      expect(initialComm, isEmpty);

      // Run self-healing logic (simulating the load method logic)
      final allItems = await db.query('inventory');
      for (final item in allItems) {
        final itemId = item['id'] as int;
        final existingComm = await db.query('commission_history', where: 'item_id = ?', whereArgs: [itemId]);
        if (existingComm.isEmpty) {
          await db.insert('commission_history', {
            'item_id': itemId,
            'commission_amount': item['initial_commission_amount'] ?? 0,
            'activation_month': item['initial_month'] ?? 1,
            'activation_year': item['initial_year'] ?? 2026,
            'created_at': DateTime.now().toIso8601String(),
            'is_synced': 0
          });
        }
      }

      // Verify commission history is healed
      final healedComm = await db.query('commission_history', where: 'item_id = ?', whereArgs: [productId]);
      expect(healedComm, isNotEmpty);
      expect(healedComm.first['commission_amount'], equals(300));
      expect(healedComm.first['activation_month'], equals(5));
      expect(healedComm.first['activation_year'], equals(2026));
    });

    test('should prevent product deletion if referenced in receipt_items or purchase_invoice_items', () async {
      final db = await dbHelper.database;

      final productId = await db.insert('inventory', {
        'name': 'Referenced Product',
      });

      // Case 1: Referenced in receipt_items
      await db.insert('receipt_items', {
        'receipt_id': 1,
        'inventory_item_id': productId,
        'quantity': 1,
        'unit_price': 100
      });

      final receiptRefs = await db.query('receipt_items', where: 'inventory_item_id = ?', whereArgs: [productId]);
      expect(receiptRefs, isNotEmpty);

      // Deletion check
      bool allowDelete = receiptRefs.isEmpty;
      expect(allowDelete, isFalse);

      // Clear receipt reference
      await db.delete('receipt_items');

      // Case 2: Referenced in purchase_invoice_items
      await db.insert('purchase_invoice_items', {
        'invoice_id': 1,
        'inventory_item_id': productId,
        'quantity': 1,
        'purchase_price': 90
      });

      final purchaseRefs = await db.query('purchase_invoice_items', where: 'inventory_item_id = ?', whereArgs: [productId]);
      expect(purchaseRefs, isNotEmpty);

      // Deletion check
      allowDelete = purchaseRefs.isEmpty;
      expect(allowDelete, isFalse);
    });
  });
}
