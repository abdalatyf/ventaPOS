import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';

class DatabaseHelper {
  Future<Database> _initDatabase() async {
    String databasesPath = await getDatabasesPath();
    String path = join(databasesPath, 'mobile_sales_v1.db');

    return await openDatabase(
      path, 
      version: 4, 
      onCreate: _onCreate,
      onUpgrade: (db, oldVersion, newVersion) async {
        if (oldVersion < 2) {
          try { await db.execute('ALTER TABLE config ADD COLUMN role TEXT'); } catch(e) {}
          try { await db.execute('ALTER TABLE receipts ADD COLUMN receipt_hash TEXT'); } catch(e) {}
        }
        if (oldVersion < 3) {
          try { await db.execute('ALTER TABLE inventory ADD COLUMN branch_id INTEGER'); } catch(e) {}
          try { await db.execute('ALTER TABLE receipts ADD COLUMN branch_id INTEGER'); } catch(e) {}
          try { await db.execute('ALTER TABLE receipts ADD COLUMN salesperson_id INTEGER'); } catch(e) {}
          try {
            await db.execute('''
              CREATE TABLE branches (
                id INTEGER PRIMARY KEY,
                name TEXT
              )
            ''');
          } catch(e) {}
          try {
            await db.execute('''
              CREATE TABLE salespeople (
                id INTEGER PRIMARY KEY,
                name TEXT,
                branch_id INTEGER
              )
            ''');
          } catch(e) {}
        }
        if (oldVersion < 4) {
          try { await db.execute("ALTER TABLE receipts ADD COLUMN sync_action TEXT DEFAULT 'NEW'"); } catch(e) {}
        }
      }
    );
  }

  Future<void> _onCreate(Database db, int version) async {}
}
