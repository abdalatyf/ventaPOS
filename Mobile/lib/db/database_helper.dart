import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';

class DatabaseHelper {
  static final DatabaseHelper instance = DatabaseHelper._init();
  static Database? _database;

  DatabaseHelper._init();

  Future<Database> get database async {
    if (_database != null) return _database!;
    _database = await _initDB('ventapos.db');
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
  }

  Future<void> _upgradeDB(Database db, int oldVersion, int newVersion) async {
    // If upgrading from older versions, handle here
  }
}
