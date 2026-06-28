import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';

class DatabaseHelper {
  static final DatabaseHelper instance = DatabaseHelper._init();
  static Database? _database;

  DatabaseHelper._init();
  factory DatabaseHelper() => instance;

  Future<String?> getConfig(String key) async {
    final db = await database;
    final maps = await db.query(
      'config',
      columns: ['value'],
      where: 'key = ?',
      whereArgs: [key],
    );
    if (maps.isNotEmpty) {
      return maps.first['value'] as String?;
    }
    return null;
  }

  Future<void> setConfig(String key, String value, {String? activeRole}) async {
    final db = await database;
    await db.insert(
      'config',
      {
        'key': key,
        'value': value,
        'active_role': activeRole,
      },
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
    if (activeRole != null) {
      await db.insert(
        'config',
        {
          'key': 'role',
          'value': activeRole,
        },
        conflictAlgorithm: ConflictAlgorithm.replace,
      );
    }
  }

  Future<Map<String, dynamic>?> getIdentity() async {
    final db = await database;
    final spIdStr = await getConfig('salesperson_id');
    if (spIdStr != null) {
      final spId = int.tryParse(spIdStr);
      if (spId != null) {
        final maps = await db.query(
          'salespersons',
          where: 'id = ?',
          whereArgs: [spId],
        );
        if (maps.isNotEmpty) {
          return maps.first;
        }
      }
      return {'salesperson_id': spIdStr};
    }
    final maps = await db.query('salespersons', limit: 1);
    if (maps.isNotEmpty) {
      return maps.first;
    }
    return null;
  }

  Future<void> markAsExported(int id) async {
    final db = await database;
    await db.update(
      'receipts',
      {'is_synced': 1},
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  Future<void> deleteAllExportedReceipts() async {
    final db = await database;
    await db.delete(
      'receipts',
      where: 'is_synced = 1',
    );
  }

  Future<void> deleteReceipt(int id) async {
    final db = await database;
    await db.delete(
      'receipts',
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  Future<String?> getBaseUrl() async => await getConfig('base_url');

  Future<String?> getRole() async => await getConfig('role');

  Future<String?> getLastSync() async => await getConfig('last_sync');

  Future<Map<String, dynamic>?> getMachineInfo() async {
    final companyCode = await getConfig('company_code');
    final masterMachineId = await getConfig('master_machine_id');
    final machineId = await getConfig('machine_id');
    return {
      'company_code': companyCode ?? 'default_company',
      'master_machine_id': masterMachineId ?? machineId ?? 'default_machine',
      'machine_id': machineId ?? masterMachineId ?? 'default_machine',
    };
  }

  Map<String, dynamic> _filterKeys(Map<String, dynamic> data, List<String> validColumns) {
    final filtered = <String, dynamic>{};
    for (final col in validColumns) {
      if (data.containsKey(col)) {
        var val = data[col];
        if (val is bool) {
          filtered[col] = val ? 1 : 0;
        } else {
          filtered[col] = val;
        }
      }
    }
    return filtered;
  }

  Future<void> upsertReceipt(Map<String, dynamic> data) async {
    final db = await database;
    final validColumns = [
      'id', 'source', 'receipt_number', 'branch_id', 'customer_name',
      'products_text', 'phone_number', 'address', 'area', 'total_amount',
      'down_payment', 'installment_system', 'salesperson_id', 'sale_year',
      'sale_month', 'is_cash_sale', 'receipt_hash', 'sync_action',
      'is_confirmed', 'created_at', 'updated_at', 'is_synced'
    ];
    final filtered = _filterKeys(data, validColumns);
    await db.insert(
      'receipts',
      filtered,
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<void> upsertProduct(Map<String, dynamic> data) async {
    final db = await database;
    final validColumns = [
      'id', 'name', 'branch_id', 'initial_quantity', 'initial_purchase_price',
      'initial_commission_amount', 'initial_month', 'initial_year',
      'created_at', 'updated_at', 'is_synced'
    ];
    final filtered = _filterKeys(data, validColumns);
    await db.insert(
      'inventory',
      filtered,
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<void> setLastSync(String time) async {
    await setConfig('last_sync', time);
  }

  Future<List<Map<String, dynamic>>> getPendingSyncStatesToProcess() async {
    final db = await database;
    return await db.query('pending_sync_states');
  }

  Future<void> deletePendingSyncState(int id) async {
    final db = await database;
    await db.delete(
      'pending_sync_states',
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  Future<void> markInventoryAsSynced(int id) async {
    final db = await database;
    await db.update(
      'inventory',
      {'is_synced': 1},
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  Future<void> markUserAsSynced(int id) async {
    final db = await database;
    await db.update(
      'salespersons',
      {'is_synced': 1},
      where: 'id = ?',
      whereArgs: [id],
    );
    await db.update(
      'cloud_users',
      {'is_synced': 1},
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  Future<void> incrementSyncRetryCount(int id, [String? errorMessage]) async {
    final db = await database;
    await db.rawUpdate('''
      UPDATE pending_sync_states 
      SET retry_count = retry_count + 1, 
          error_message = ?, 
          last_attempt = ? 
      WHERE id = ?
    ''', [errorMessage, DateTime.now().toIso8601String(), id]);
  }
  
  Future<List<Map<String, dynamic>>> getInventoryItems() async {
    final db = await database;
    return await db.query('inventory');
  }

  Future<List<Map<String, dynamic>>> getSalespersons() async {
    final db = await database;
    return await db.query('salespersons');
  }

  Future<Database> get database async {
    if (_database != null) return _database!;
    _database = await _initDB('ventapos_v2.db');
    return _database!;
  }

  Future<Database> _initDB(String filePath) async {
    final dbPath = await getDatabasesPath();
    final path = join(dbPath, filePath);

    return await openDatabase(
      path,
      version: 1,
      onCreate: _createDB,
      onUpgrade: _upgradeDB,
    );
  }

  Future<void> _createDB(Database db, int version) async {
    // 1. Branch
    await db.execute('''
      CREATE TABLE branches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        is_synced INTEGER DEFAULT 0
      )
    ''');

    // 2. Salesperson
    await db.execute('''
      CREATE TABLE salespersons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        branch_id INTEGER,
        name TEXT,
        cloud_username TEXT,
        cloud_password TEXT,
        device_token TEXT,
        is_device_active INTEGER DEFAULT 0,
        is_synced INTEGER DEFAULT 0
      )
    ''');

    // 3. CloudUser
    await db.execute('''
      CREATE TABLE cloud_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT DEFAULT 'VIEWER',
        is_active INTEGER DEFAULT 1,
        created_at TEXT,
        is_synced INTEGER DEFAULT 0
      )
    ''');

    // 4. InventoryItem
    await db.execute('''
      CREATE TABLE inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        branch_id INTEGER,
        initial_quantity INTEGER DEFAULT 0,
        initial_purchase_price INTEGER DEFAULT 0,
        initial_commission_amount INTEGER DEFAULT 0,
        initial_month INTEGER DEFAULT 1,
        initial_year INTEGER DEFAULT 2026,
        created_at TEXT,
        updated_at TEXT,
        is_synced INTEGER DEFAULT 0
      )
    ''');

    // 5. CommissionHistory
    await db.execute('''
      CREATE TABLE commission_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER,
        commission_amount INTEGER,
        activation_month INTEGER,
        activation_year INTEGER,
        created_at TEXT,
        is_synced INTEGER DEFAULT 0
      )
    ''');

    // 6. Receipt
    await db.execute('''
      CREATE TABLE receipts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT DEFAULT 'DESKTOP',
        receipt_number INTEGER,
        branch_id INTEGER,
        customer_name TEXT,
        products_text TEXT,
        phone_number TEXT,
        address TEXT,
        area TEXT,
        total_amount INTEGER DEFAULT 0,
        down_payment INTEGER DEFAULT 0,
        installment_system TEXT,
        salesperson_id INTEGER,
        sale_year INTEGER,
        sale_month INTEGER,
        is_cash_sale INTEGER DEFAULT 0,
        receipt_hash TEXT,
        sync_action TEXT DEFAULT 'NEW',
        is_confirmed INTEGER DEFAULT 1,
        created_at TEXT,
        updated_at TEXT,
        is_synced INTEGER DEFAULT 0
      )
    ''');

    // 7. SaleItem
    await db.execute('''
      CREATE TABLE receipt_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        receipt_id INTEGER,
        inventory_item_id INTEGER,
        quantity INTEGER DEFAULT 1,
        unit_price INTEGER,
        is_synced INTEGER DEFAULT 0
      )
    ''');

    // 8. InstallmentPayment
    await db.execute('''
      CREATE TABLE installment_payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        receipt_id INTEGER,
        payment_date TEXT,
        amount INTEGER,
        is_synced INTEGER DEFAULT 0
      )
    ''');

    // 9. Expense
    await db.execute('''
      CREATE TABLE expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        branch_id INTEGER,
        amount REAL,
        description TEXT,
        expense_year INTEGER,
        expense_month INTEGER,
        created_at TEXT,
        is_synced INTEGER DEFAULT 0
      )
    ''');

    // 10. Supplier
    await db.execute('''
      CREATE TABLE suppliers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        is_synced INTEGER DEFAULT 0
      )
    ''');

    // 11. Purchase Invoices
    await db.execute('''
      CREATE TABLE purchase_invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_number INTEGER,
        invoice_month INTEGER,
        invoice_year INTEGER,
        invoice_type TEXT,
        supplier_id INTEGER,
        is_synced INTEGER DEFAULT 0
      )
    ''');

    // 12. Purchase Invoice Items
    await db.execute('''
      CREATE TABLE purchase_invoice_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER,
        inventory_item_id INTEGER,
        quantity INTEGER,
        purchase_price INTEGER,
        is_synced INTEGER DEFAULT 0
      )
    ''');

    // 13. Config Table
    await db.execute('''
      CREATE TABLE config (
        key TEXT PRIMARY KEY,
        value TEXT,
        active_role TEXT
      )
    ''');

    // 14. Pending Sync States Table
    await db.execute('''
      CREATE TABLE pending_sync_states (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_type TEXT,
        entity_local_id INTEGER,
        action TEXT,
        payload_json TEXT,
        retry_count INTEGER DEFAULT 0,
        error_message TEXT,
        last_attempt TEXT
      )
    ''');

    // ----------------------------------------------------
    // Seed Mock Data for Testing
    // ----------------------------------------------------
    await db.insert('branches', {'id': 1, 'name': 'الفرع الرئيسي', 'is_synced': 1});
    
    await db.insert('salespersons', {'id': 1, 'branch_id': 1, 'name': 'أحمد محمود', 'is_synced': 1});
    await db.insert('salespersons', {'id': 2, 'branch_id': 1, 'name': 'محمد علي', 'is_synced': 1});

    await db.insert('inventory', {'id': 1, 'name': 'شاشة سامسونج 50 بوصة', 'branch_id': 1, 'initial_quantity': 100, 'initial_purchase_price': 8000, 'is_synced': 1});
    await db.insert('inventory', {'id': 2, 'name': 'لابتوب ديل', 'branch_id': 1, 'initial_quantity': 50, 'initial_purchase_price': 15000, 'is_synced': 1});
    await db.insert('inventory', {'id': 3, 'name': 'ثلاجة توشيبا', 'branch_id': 1, 'initial_quantity': 20, 'initial_purchase_price': 22000, 'is_synced': 1});

    // Seed some mock receipts
    int nowSec = DateTime.now().millisecondsSinceEpoch ~/ 1000;
    int receiptId1 = await db.insert('receipts', {
      'receipt_number': nowSec - 1000,
      'source': 'MOBILE',
      'branch_id': 1,
      'customer_name': 'خالد إبراهيم',
      'phone_number': '01012345678',
      'total_amount': 8000,
      'is_cash_sale': 1,
      'sale_year': 2024,
      'sale_month': 5,
      'salesperson_id': 1,
      'is_synced': 1
    });
    await db.insert('receipt_items', {'receipt_id': receiptId1, 'inventory_item_id': 1, 'quantity': 1, 'unit_price': 8000});

    int receiptId2 = await db.insert('receipts', {
      'receipt_number': nowSec - 500,
      'source': 'MOBILE',
      'branch_id': 1,
      'customer_name': 'منى أحمد',
      'phone_number': '01111111111',
      'total_amount': 15000,
      'is_cash_sale': 0,
      'down_payment': 5000,
      'sale_year': 2024,
      'sale_month': 5,
      'salesperson_id': 2,
      'is_synced': 1
    });
    await db.insert('receipt_items', {'receipt_id': receiptId2, 'inventory_item_id': 2, 'quantity': 1, 'unit_price': 15000});
    await db.insert('installment_payments', {'receipt_id': receiptId2, 'payment_date': '2024-06-01', 'amount': 5000});
    await db.insert('installment_payments', {'receipt_id': receiptId2, 'payment_date': '2024-07-01', 'amount': 5000});
  }

  Future<void> _upgradeDB(Database db, int oldVersion, int newVersion) async {
    // If upgrading from older versions, handle here
  }
}
