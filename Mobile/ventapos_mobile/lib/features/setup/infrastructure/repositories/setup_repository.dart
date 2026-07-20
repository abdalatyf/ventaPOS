import 'package:sqflite/sqflite.dart';
import '../../../../core/database/database_helper.dart';
import '../../domain/models/inventory_item_model.dart';
import '../../domain/models/salesperson_model.dart';
import '../../domain/models/supplier_model.dart';
import '../../domain/models/commission_history_model.dart';

class SetupRepository {
  final DatabaseHelper _dbHelper = DatabaseHelper.instance;

  Future<Database> get db async => await _dbHelper.database;

  // Inventory Items
  Future<List<InventoryItemModel>> getInventoryItems() async {
    final database = await db;
    final List<Map<String, dynamic>> maps = await database.query(
      'inventory_items',
      where: 'is_deleted = ?',
      whereArgs: [0],
    );
    return maps.map((map) => InventoryItemModel.fromJson(map)).toList();
  }

  Future<int> addInventoryItem(InventoryItemModel item) async {
    final database = await db;
    final map = item.toJson();
    map.remove('id'); // SQLite auto-increments if id is not provided, wait actually inventory_items might not auto increment but let's assume it doesn't wait
    // Actually the schema in tables.dart says:
    // id INTEGER PRIMARY KEY, (no AUTOINCREMENT)
    // Wait, let's check tables.dart: inventory_items has `id INTEGER PRIMARY KEY,`
    // SQLite makes INTEGER PRIMARY KEY an alias for ROWID and auto-increments it anyway.
    return await database.insert('inventory_items', map);
  }

  Future<int> updateInventoryItem(InventoryItemModel item) async {
    final database = await db;
    return await database.update(
      'inventory_items',
      item.toJson(),
      where: 'id = ?',
      whereArgs: [item.id],
    );
  }

  Future<int> deleteInventoryItem(int id) async {
    final database = await db;
    // Soft delete
    return await database.update(
      'inventory_items',
      {'is_deleted': 1},
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  // Commission History
  Future<List<CommissionHistoryModel>> getCommissionHistory(int itemId) async {
    final database = await db;
    final List<Map<String, dynamic>> maps = await database.query(
      'commission_history',
      where: 'inventory_item_id = ?',
      whereArgs: [itemId],
      orderBy: 'start_year DESC, start_month DESC',
    );
    return maps.map((map) => CommissionHistoryModel.fromJson(map)).toList();
  }

  Future<int> addCommissionHistory(CommissionHistoryModel commission) async {
    final database = await db;
    final map = commission.toJson();
    map.remove('id');
    return await database.insert('commission_history', map);
  }

  // Salespersons
  Future<List<SalespersonModel>> getSalespersons() async {
    final database = await db;
    final List<Map<String, dynamic>> maps = await database.query(
      'salespeople',
    );
    return maps.map((map) => SalespersonModel.fromJson(map)).toList();
  }

  Future<int> addSalesperson(SalespersonModel salesperson) async {
    final database = await db;
    final map = salesperson.toJson();
    map.remove('id');
    return await database.insert('salespeople', map);
  }

  Future<int> updateSalesperson(SalespersonModel salesperson) async {
    final database = await db;
    return await database.update(
      'salespeople',
      salesperson.toJson(),
      where: 'id = ?',
      whereArgs: [salesperson.id],
    );
  }

  Future<int> deleteSalesperson(int id) async {
    final database = await db;
    return await database.delete(
      'salespeople',
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  // Suppliers
  Future<List<SupplierModel>> getSuppliers() async {
    final database = await db;
    final List<Map<String, dynamic>> maps = await database.query(
      'suppliers',
    );
    return maps.map((map) => SupplierModel.fromJson(map)).toList();
  }

  Future<int> addSupplier(SupplierModel supplier) async {
    final database = await db;
    final map = supplier.toJson();
    map.remove('id');
    return await database.insert('suppliers', map);
  }

  Future<int> deleteSupplier(int id) async {
    final database = await db;
    return await database.delete(
      'suppliers',
      where: 'id = ?',
      whereArgs: [id],
    );
  }
}
