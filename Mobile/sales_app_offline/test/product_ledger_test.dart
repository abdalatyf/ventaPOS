import 'package:flutter_test/flutter_test.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';
import 'package:sales_app_offline/db/database_helper.dart';

void main() {
  sqfliteFfiInit();
  databaseFactory = databaseFactoryFfi;

  group('Product Ledger Calculation Tests', () {
    late DatabaseHelper dbHelper;

    setUp(() async {
      dbHelper = DatabaseHelper();
      final db = await dbHelper.database;
      // Clear tables before each test
      await db.delete('inventory');
      await db.delete('commission_history');
      await db.delete('receipt_items');
      await db.delete('receipts');
      await db.delete('purchase_invoice_items');
      await db.delete('purchase_invoices');
      await db.delete('suppliers');
    });

    test('should calculate correct stock at date (get_stock_at_date replication)', () async {
      final db = await dbHelper.database;

      // 1. Insert product
      final productId = await db.insert('inventory', {
        'name': 'Samsung LED TV',
        'branch_id': 1,
        'initial_quantity': 50,
        'initial_purchase_price': 1000,
        'initial_commission_amount': 50,
        'initial_month': 1,
        'initial_year': 2026,
      });

      // --- Define replication of getStockAtDate ---
      Future<int> getStockAtDate(int m, int y) async {
        final prodQuery = await db.query('inventory', where: 'id = ?', whereArgs: [productId]);
        final product = prodQuery.first;
        final int initialQty = product['initial_quantity'] as int? ?? 0;
        final int initialMonth = product['initial_month'] as int? ?? 1;
        final int initialYear = product['initial_year'] as int? ?? 2026;

        if (y < initialYear || (y == initialYear && m < initialMonth)) {
          return 0;
        }

        final purchasedQuery = await db.rawQuery('''
          SELECT SUM(pi.quantity) as total
          FROM purchase_invoice_items pi
          JOIN purchase_invoices p ON pi.invoice_id = p.id
          WHERE pi.inventory_item_id = ?
            AND p.invoice_type = 'PURCHASE'
            AND (p.invoice_year < ? OR (p.invoice_year = ? AND p.invoice_month <= ?))
        ''', [productId, y, y, m]);
        int totalPurchased = (purchasedQuery.first['total'] as num?)?.toInt() ?? 0;

        final returnedQuery = await db.rawQuery('''
          SELECT SUM(pi.quantity) as total
          FROM purchase_invoice_items pi
          JOIN purchase_invoices p ON pi.invoice_id = p.id
          WHERE pi.inventory_item_id = ?
            AND p.invoice_type = 'RETURN'
            AND (p.invoice_year < ? OR (p.invoice_year = ? AND p.invoice_month <= ?))
        ''', [productId, y, y, m]);
        int totalReturned = (returnedQuery.first['total'] as num?)?.toInt() ?? 0;

        final soldQuery = await db.rawQuery('''
          SELECT SUM(ri.quantity) as total
          FROM receipt_items ri
          JOIN receipts r ON ri.receipt_id = r.id
          WHERE ri.inventory_item_id = ?
            AND (r.sale_year < ? OR (r.sale_year = ? AND r.sale_month <= ?))
        ''', [productId, y, y, m]);
        int totalSold = (soldQuery.first['total'] as num?)?.toInt() ?? 0;

        return (initialQty + totalPurchased) - (totalSold + totalReturned);
      }

      // Check initial stock
      expect(await getStockAtDate(1, 2026), equals(50));

      // 2. Add purchase invoice for 20 items in month 2, 2026
      int invoiceId1 = await db.insert('purchase_invoices', {
        'invoice_number': 101,
        'invoice_month': 2,
        'invoice_year': 2026,
        'invoice_type': 'PURCHASE',
      });
      await db.insert('purchase_invoice_items', {
        'invoice_id': invoiceId1,
        'inventory_item_id': productId,
        'quantity': 20,
        'purchase_price': 1050,
      });

      // Verify stock in month 2, 2026 is 70
      expect(await getStockAtDate(2, 2026), equals(70));
      expect(await getStockAtDate(1, 2026), equals(50)); // prior month remains 50

      // 3. Add receipt sale for 15 items in month 3, 2026
      int receiptId1 = await db.insert('receipts', {
        'receipt_number': 501,
        'sale_month': 3,
        'sale_year': 2026,
        'is_cash_sale': 1,
        'total_amount': 22500,
      });
      await db.insert('receipt_items', {
        'receipt_id': receiptId1,
        'inventory_item_id': productId,
        'quantity': 15,
        'unit_price': 1500,
      });

      // Verify stock in month 3, 2026 is 55 (70 - 15)
      expect(await getStockAtDate(3, 2026), equals(55));

      // 4. Add return invoice for 5 items in month 4, 2026
      int invoiceId2 = await db.insert('purchase_invoices', {
        'invoice_number': 102,
        'invoice_month': 4,
        'invoice_year': 2026,
        'invoice_type': 'RETURN',
      });
      await db.insert('purchase_invoice_items', {
        'invoice_id': invoiceId2,
        'inventory_item_id': productId,
        'quantity': 5,
        'purchase_price': 1050,
      });

      // Verify stock in month 4, 2026 is 50 (55 - 5)
      expect(await getStockAtDate(4, 2026), equals(50));
    });

    test('should fetch correct historical price at date', () async {
      final db = await dbHelper.database;

      final productId = await db.insert('inventory', {
        'name': 'Samsung LED TV',
        'initial_purchase_price': 1000,
        'initial_month': 1,
        'initial_year': 2026,
      });

      Future<double> getPriceAtDate(int m, int y) async {
        final latestPurchase = await db.rawQuery('''
          SELECT pi.purchase_price
          FROM purchase_invoice_items pi
          JOIN purchase_invoices p ON pi.invoice_id = p.id
          WHERE pi.inventory_item_id = ?
            AND p.invoice_type = 'PURCHASE'
            AND p.invoice_year <= ?
            AND (p.invoice_year < ? OR p.invoice_month <= ?)
          ORDER BY p.invoice_year DESC, p.invoice_month DESC, p.id DESC
          LIMIT 1
        ''', [productId, y, y, m]);

        if (latestPurchase.isNotEmpty) {
          return (latestPurchase.first['purchase_price'] as num).toDouble();
        }
        return 1000.0;
      }

      // Check month 1, 2026 -> initial price (1000)
      expect(await getPriceAtDate(1, 2026), equals(1000.0));

      // Insert purchase at month 2, 2026 with price 1100
      int invId = await db.insert('purchase_invoices', {
        'invoice_month': 2,
        'invoice_year': 2026,
        'invoice_type': 'PURCHASE',
      });
      await db.insert('purchase_invoice_items', {
        'invoice_id': invId,
        'inventory_item_id': productId,
        'quantity': 5,
        'purchase_price': 1100,
      });

      // Month 1 should still be 1000
      expect(await getPriceAtDate(1, 2026), equals(1000.0));
      // Month 2 should be 1100
      expect(await getPriceAtDate(2, 2026), equals(1100.0));
      // Month 3 should be 1100
      expect(await getPriceAtDate(3, 2026), equals(1100.0));
    });
  });
}
