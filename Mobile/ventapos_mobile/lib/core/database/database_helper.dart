import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';
import 'tables.dart';

class DatabaseHelper {
  static final DatabaseHelper instance = DatabaseHelper._init();
  static Database? _database;

  DatabaseHelper._init();

  Future<Database> get database async {
    if (_database != null) return _database!;
    _database = await _initDB('ventapos_mobile.db');
    return _database!;
  }

  Future<Database> _initDB(String filePath) async {
    final dbPath = await getDatabasesPath();
    final path = join(dbPath, filePath);

    return await openDatabase(
      path,
      version: 1,
      onCreate: _createDB,
      onConfigure: _onConfigure,
    );
  }

  Future _onConfigure(Database db) async {
    // Enable foreign keys
    await db.execute('PRAGMA foreign_keys = ON');
  }

  Future _createDB(Database db, int version) async {
    // Execute all table creation scripts
    for (String tableScript in AppDatabaseTables.allTables) {
      await db.execute(tableScript);
    }
  }

  // ---------------------------------------------------------
  // Helper methods for AppConfig
  // ---------------------------------------------------------

  Future<void> setConfig(String key, String value) async {
    final db = await instance.database;
    await db.insert(
      'app_config',
      {'key': key, 'value': value},
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<String?> getConfig(String key) async {
    final db = await instance.database;
    final maps = await db.query(
      'app_config',
      columns: ['value'],
      where: 'key = ?',
      whereArgs: [key],
    );

    if (maps.isNotEmpty) {
      return maps.first['value'] as String?;
    } else {
      return null;
    }
  }

  // ---------------------------------------------------------
  // Master Sync Helper
  // ---------------------------------------------------------

  /// Completely wipes local master tables and replaces them with new synced data
  Future<void> syncMasterData(Map<String, dynamic> payload) async {
    final db = await instance.database;
    
    // We use a transaction to ensure either everything syncs or nothing does
    await db.transaction((txn) async {
      // 1. Wipe old master data
      await txn.delete('inventory_items');
      await txn.delete('salespeople');
      await txn.delete('branches');
      
      // 2. Insert Branches
      if (payload['branches'] != null) {
        for (var branch in payload['branches']) {
          await txn.insert('branches', branch);
        }
      }

      // 3. Insert Salespeople
      if (payload['salespeople'] != null) {
        for (var sp in payload['salespeople']) {
          await txn.insert('salespeople', sp);
        }
      }

      // 4. Insert Inventory Items
      if (payload['inventory_items'] != null) {
        for (var item in payload['inventory_items']) {
          await txn.insert('inventory_items', item);
        }
      }
    });
  }

  Future close() async {
    final db = await instance.database;
    db.close();
  }
}
