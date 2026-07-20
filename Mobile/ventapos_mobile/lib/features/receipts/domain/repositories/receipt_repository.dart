import '../../../../core/database/database_helper.dart';
import '../models/receipt_form_state.dart';

class ReceiptRepository {
  final DatabaseHelper _dbHelper = DatabaseHelper.instance;

  Future<List<String>> searchCustomerField(String term, String field) async {
    final db = await _dbHelper.database;
    // We search the receipts table for previous customers
    final maps = await db.query(
      'receipts',
      columns: [field],
      where: '$field LIKE ? AND is_cash_sale = 0',
      whereArgs: ['%$term%'],
      distinct: true,
      limit: 10,
    );

    return maps.map((e) => e[field] as String).where((e) => e.isNotEmpty).toList();
  }

  Future<List<Map<String, dynamic>>> searchProducts(String term) async {
    final db = await _dbHelper.database;
    final maps = await db.query(
      'inventory_items',
      columns: ['id', 'name', 'current_stock', 'current_price'],
      where: 'name LIKE ? AND is_deleted = 0 AND current_stock > 0',
      whereArgs: ['%$term%'],
      limit: 10,
    );
    return maps;
  }

  Future<List<Map<String, dynamic>>> getSalespeople() async {
    final db = await _dbHelper.database;
    return await db.query('salespeople', columns: ['id', 'name']);
  }

  Future<void> saveReceipt(ReceiptFormState state) async {
    final db = await _dbHelper.database;

    // We use a transaction so either everything inserts or nothing does
    await db.transaction((txn) async {
      // 1. Get branch ID from config or default to 1
      final configMap = await txn.query('app_config', where: 'key = ?', whereArgs: ['branch_id']);
      int branchId = 1;
      if (configMap.isNotEmpty) {
        branchId = int.tryParse(configMap.first['value'] as String) ?? 1;
      }

      // Default salesperson to 1 if null
      int salespersonId = state.customer.salespersonId ?? 1;

      // 2. Insert into receipts table
      // Note: receipt_number is pending (0) locally since it's taken from the PC app later.
      final receiptId = await txn.insert('receipts', {
        'branch_id': branchId,
        'salesperson_id': salespersonId,
        'receipt_number': 0, 
        'customer_name': state.isCashSale ? 'عميل نقدي' : state.customer.name,
        'phone_number': state.isCashSale ? '' : state.customer.phone,
        'address': state.isCashSale ? '' : state.customer.address,
        'area': state.isCashSale ? '' : state.customer.area,
        'total_amount': state.totalCartValue,
        'down_payment': state.isCashSale ? state.totalCartValue : state.downPayment,
        'installment_system': state.isCashSale ? '' : _buildInstallmentSystemString(state.groups),
        'sale_year': state.saleYear,
        'sale_month': state.saleMonth,
        'is_cash_sale': state.isCashSale ? 1 : 0,
        'products_text': _buildProductsText(state.cart),
        'is_exported': 0, // Pending sync
        'created_at_local': DateTime.now().toIso8601String(),
      });

      // 3. Insert sale_items
      for (var item in state.cart) {
        await txn.insert('sale_items', {
          'receipt_id': receiptId,
          'inventory_item_id': item.inventoryItemId,
          'quantity': item.quantity,
          'unit_price': item.price,
        });

        // Optional: Update local inventory stock here if required by requirements
        // Currently, we'll let sync handle the ultimate truth, but decrementing locally 
        // prevents double-selling.
        await txn.rawUpdate(
          'UPDATE inventory_items SET current_stock = current_stock - ? WHERE id = ?',
          [item.quantity, item.inventoryItemId]
        );
      }

      // 4. Insert installment_payments (only if not cash sale)
      if (!state.isCashSale) {
        for (var inst in state.schedule) {
          final paymentDateStr = DateTime(inst.year, inst.month, 1).toIso8601String();
          await txn.insert('installment_payments', {
            'receipt_id': receiptId,
            'payment_date': paymentDateStr,
            'amount': inst.amount,
          });
        }
      }
    });
  }

  String _buildInstallmentSystemString(List<InstallmentGroup> groups) {
    final activeGroups = groups.where((g) => (g.amount ?? 0) > 0 && (g.count ?? 0) > 0);
    return activeGroups.map((g) => '${g.amount}*${g.count}').join(' + ');
  }

  String _buildProductsText(List<CartItem> cart) {
    return cart.map((c) => '${c.name} (${c.quantity})').join(', ');
  }
}
