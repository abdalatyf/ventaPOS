class AppDatabaseTables {
  static const String appConfig = '''
    CREATE TABLE app_config (
        key TEXT PRIMARY KEY,
        value TEXT
    );
  ''';

  static const String branches = '''
    CREATE TABLE branches (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL
    );
  ''';

  static const String salespeople = '''
    CREATE TABLE salespeople (
        id INTEGER PRIMARY KEY,
        branch_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        FOREIGN KEY(branch_id) REFERENCES branches(id)
    );
  ''';

  static const String inventoryItems = '''
    CREATE TABLE inventory_items (
        id INTEGER PRIMARY KEY,
        branch_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        current_stock INTEGER NOT NULL DEFAULT 0,       
        current_price INTEGER NOT NULL DEFAULT 0,       
        current_commission INTEGER NOT NULL DEFAULT 0,
        start_month INTEGER NOT NULL,
        start_year INTEGER NOT NULL,
        is_deleted INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY(branch_id) REFERENCES branches(id)
    );
  ''';

  static const String receipts = '''
    CREATE TABLE receipts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        branch_id INTEGER NOT NULL,
        salesperson_id INTEGER NOT NULL,
        receipt_number INTEGER NOT NULL,
        customer_name TEXT NOT NULL,
        phone_number TEXT,
        address TEXT,
        area TEXT,
        total_amount REAL NOT NULL,
        down_payment REAL NOT NULL,
        installment_system TEXT,
        sale_year INTEGER NOT NULL,
        sale_month INTEGER NOT NULL,
        is_cash_sale INTEGER NOT NULL DEFAULT 0,
        products_text TEXT,
        is_exported INTEGER NOT NULL DEFAULT 0,
        created_at_local TEXT NOT NULL,
        FOREIGN KEY(branch_id) REFERENCES branches(id),
        FOREIGN KEY(salesperson_id) REFERENCES salespeople(id)
    );
  ''';

  static const String saleItems = '''
    CREATE TABLE sale_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        receipt_id INTEGER NOT NULL,
        inventory_item_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        FOREIGN KEY(receipt_id) REFERENCES receipts(id) ON DELETE CASCADE,
        FOREIGN KEY(inventory_item_id) REFERENCES inventory_items(id)
    );
  ''';

  static const String installmentPayments = '''
    CREATE TABLE installment_payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        receipt_id INTEGER NOT NULL,
        payment_date TEXT NOT NULL,
        amount REAL NOT NULL,
        FOREIGN KEY(receipt_id) REFERENCES receipts(id) ON DELETE CASCADE
    );
  ''';

  static const String expenses = '''
    CREATE TABLE expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        branch_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        description TEXT NOT NULL,
        expense_year INTEGER NOT NULL,
        expense_month INTEGER NOT NULL,
        is_exported INTEGER NOT NULL DEFAULT 0,
        created_at_local TEXT NOT NULL,
        FOREIGN KEY(branch_id) REFERENCES branches(id)
    );
  ''';

  static const String inventoryAdjustments = '''
    CREATE TABLE inventory_adjustments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        inventory_item_id INTEGER NOT NULL,
        adjustment_type TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        reason TEXT,
        adjustment_month INTEGER NOT NULL,
        adjustment_year INTEGER NOT NULL,
        is_exported INTEGER NOT NULL DEFAULT 0,
        created_at_local TEXT NOT NULL,
        FOREIGN KEY(inventory_item_id) REFERENCES inventory_items(id)
    );
  ''';

  static const String suppliers = '''
    CREATE TABLE suppliers (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL
    );
  ''';

  static const String purchaseInvoices = '''
    CREATE TABLE purchase_invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        branch_id INTEGER NOT NULL,
        supplier_id INTEGER NOT NULL,
        invoice_number INTEGER NOT NULL,
        invoice_type TEXT NOT NULL,
        invoice_month INTEGER NOT NULL,
        invoice_year INTEGER NOT NULL,
        is_exported INTEGER NOT NULL DEFAULT 0,
        created_at_local TEXT NOT NULL,
        FOREIGN KEY(branch_id) REFERENCES branches(id),
        FOREIGN KEY(supplier_id) REFERENCES suppliers(id)
    );
  ''';

  static const String purchaseInvoiceItems = '''
    CREATE TABLE purchase_invoice_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        purchase_invoice_id INTEGER NOT NULL,
        inventory_item_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        purchase_price INTEGER NOT NULL,
        FOREIGN KEY(purchase_invoice_id) REFERENCES purchase_invoices(id) ON DELETE CASCADE,
        FOREIGN KEY(inventory_item_id) REFERENCES inventory_items(id)
    );
  ''';

  static const String commissionHistory = '''
    CREATE TABLE commission_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        inventory_item_id INTEGER NOT NULL,
        commission_amount INTEGER NOT NULL,
        start_month INTEGER NOT NULL,
        start_year INTEGER NOT NULL,
        created_at_local TEXT NOT NULL,
        FOREIGN KEY(inventory_item_id) REFERENCES inventory_items(id) ON DELETE CASCADE
    );
  ''';

  // List of all creation scripts to run during database initialization
  static const List<String> allTables = [
    appConfig,
    branches,
    salespeople,
    inventoryItems,
    receipts,
    saleItems,
    installmentPayments,
    expenses,
    inventoryAdjustments,
    suppliers,
    purchaseInvoices,
    purchaseInvoiceItems,
    commissionHistory,
  ];
}
