import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../db/database_helper.dart';

/// SyncWorker - يقوم بمزامنة جميع الجداول المحلية مع السيرفر المركزي
/// يدعم: المنتجات، المندوبين، الفروع، الموردين، الفواتير، المصروفات، المشتريات، سجلات العمولات
class SyncWorker {
  static final SyncWorker _instance = SyncWorker._internal();
  factory SyncWorker() => _instance;
  SyncWorker._internal();

  Timer? _timer;
  bool _isSyncing = false;
  String _baseUrl = 'http://10.0.2.2:8000'; // للإيميولاتور - يتم تجاوزه بالـ server_url من الـ config

  void start() {
    _timer?.cancel();
    _timer = Timer.periodic(const Duration(seconds: 60), (timer) {
      syncNow();
    });
    syncNow();
  }

  void stop() {
    _timer?.cancel();
  }

  Future<bool> syncNow() async {
    if (_isSyncing) return false;
    _isSyncing = true;

    try {
      final dbHelper = DatabaseHelper();
      final db = await dbHelper.database;
      final machineInfo = await dbHelper.getMachineInfo();
      final machineId = machineInfo?['machine_id'] ?? 'mobile_device';
      final companyCode = machineInfo?['company_code'] ?? '';

      // ── 1. جمع البيانات من pending_sync_states ──────────────────────
      final pendingRows = await dbHelper.getPendingSyncStatesToProcess();

      List<Map<String, dynamic>> products = [];
      List<Map<String, dynamic>> users = [];
      List<Map<String, dynamic>> settings = [];
      List<Map<String, dynamic>> receipts = [];
      List<Map<String, dynamic>> suppliers = [];
      List<Map<String, dynamic>> branches = [];
      List<Map<String, dynamic>> expenses = [];
      List<Map<String, dynamic>> purchaseInvoices = [];
      List<Map<String, dynamic>> commissionHistory = [];

      for (var row in pendingRows) {
        final payload = jsonDecode(row['payload_json'] as String);
        payload['local_id'] = row['entity_local_id'];
        payload['action'] = row['action'];
        switch (row['entity_type']) {
          case 'PRODUCT':    products.add(payload);         break;
          case 'USER':       users.add(payload);            break;
          case 'SETTINGS':   settings.add(payload);         break;
          case 'RECEIPT':    receipts.add(payload);         break;
          case 'SUPPLIER':   suppliers.add(payload);        break;
          case 'BRANCH':     branches.add(payload);         break;
          case 'EXPENSE':    expenses.add(payload);         break;
          case 'PURCHASE':   purchaseInvoices.add(payload); break;
          case 'COMMISSION': commissionHistory.add(payload); break;
        }
      }

      // ── 2. جمع الفواتير غير المزامنة مباشرةً من جدول receipts ────────
      if (receipts.isEmpty) {
        final unsyncedReceipts = await db.query(
          'receipts',
          where: 'is_synced = 0',
        );
        for (var rec in unsyncedReceipts) {
          final recId = rec['id'] as int;
          final items = await db.query('receipt_items', where: 'receipt_id = ?', whereArgs: [recId]);
          final payments = await db.query('installment_payments', where: 'receipt_id = ?', whereArgs: [recId]);
          receipts.add({
            ...rec,
            'local_id': recId,
            'action': 'CREATE',
            'items': items.map((i) => {...i}).toList(),
            'installment_payments': payments.map((p) => {...p}).toList(),
          });
        }
      }

      // ── 3. جمع المصروفات غير المزامنة ──────────────────────────────
      if (expenses.isEmpty) {
        final unsyncedExpenses = await db.query('expenses', where: 'is_synced = 0');
        for (var exp in unsyncedExpenses) {
          expenses.add({...exp, 'local_id': exp['id'], 'action': 'CREATE'});
        }
      }

      // ── 4. جمع المشتريات غير المزامنة ─────────────────────────────
      if (purchaseInvoices.isEmpty) {
        final unsyncedPurchases = await db.query('purchase_invoices', where: 'is_synced = 0');
        for (var inv in unsyncedPurchases) {
          final invId = inv['id'] as int;
          final items = await db.query('purchase_invoice_items', where: 'invoice_id = ?', whereArgs: [invId]);
          purchaseInvoices.add({
            ...inv,
            'local_id': invId,
            'action': 'CREATE',
            'items': items.map((i) => {...i}).toList(),
          });
        }
      }

      // ── 5. جمع الموردين غير المزامنين ─────────────────────────────
      if (suppliers.isEmpty) {
        final unsyncedSuppliers = await db.query('suppliers', where: 'is_synced = 0');
        for (var s in unsyncedSuppliers) {
          suppliers.add({...s, 'local_id': s['id'], 'action': 'CREATE'});
        }
      }

      // ── 6. جمع الفروع غير المزامنة ────────────────────────────────
      if (branches.isEmpty) {
        final unsyncedBranches = await db.query('branches', where: 'is_synced = 0');
        for (var b in unsyncedBranches) {
          branches.add({...b, 'local_id': b['id'], 'action': 'CREATE'});
        }
      }

      // ── 7. جمع المنتجات غير المزامنة ──────────────────────────────
      if (products.isEmpty) {
        final unsyncedProducts = await db.query('inventory', where: 'is_synced = 0');
        for (var p in unsyncedProducts) {
          products.add({...p, 'local_id': p['id'], 'action': 'CREATE'});
        }
      }

      // إذا لا يوجد شيء للمزامنة
      final totalPending = products.length + users.length + receipts.length +
          expenses.length + purchaseInvoices.length + suppliers.length +
          branches.length + commissionHistory.length;
      if (totalPending == 0) {
        _isSyncing = false;
        return true;
      }

      // ── 8. إرسال الـ payload للسيرفر ──────────────────────────────
      final String? serverUrl = await dbHelper.getConfig('server_url');
      final baseUrl = (serverUrl != null && serverUrl.isNotEmpty) ? serverUrl : _baseUrl;
      final targetUrl = '$baseUrl/api/v1/sync/admin-push/';

      final body = jsonEncode({
        'machine_id': machineId,
        'company_code': companyCode,
        'payload': {
          'branches': branches,
          'products': products,
          'users': users,
          'settings': settings.isNotEmpty ? settings.first : {},
          'suppliers': suppliers,
          'expenses': expenses,
          'purchase_invoices': purchaseInvoices,
          'receipts': receipts,
          'commission_history': commissionHistory,
        }
      });

      final response = await http.post(
        Uri.parse(targetUrl),
        headers: {'Content-Type': 'application/json'},
        body: body,
      ).timeout(const Duration(seconds: 30));

      if (response.statusCode == 200) {
        // ── 9. تحديث is_synced = 1 لكل الجداول التي أُرسلت ────────
        await db.transaction((txn) async {
          // من pending_sync_states
          for (var row in pendingRows) {
            await dbHelper.deletePendingSyncState(row['id'] as int);
          }

          // المزامنة المباشرة للجداول
          if (receipts.isNotEmpty) {
            await txn.rawUpdate('UPDATE receipts SET is_synced = 1 WHERE is_synced = 0');
          }
          if (expenses.isNotEmpty) {
            await txn.rawUpdate('UPDATE expenses SET is_synced = 1 WHERE is_synced = 0');
          }
          if (purchaseInvoices.isNotEmpty) {
            await txn.rawUpdate('UPDATE purchase_invoices SET is_synced = 1 WHERE is_synced = 0');
            await txn.rawUpdate('UPDATE purchase_invoice_items SET is_synced = 1 WHERE is_synced = 0');
          }
          if (suppliers.isNotEmpty) {
            await txn.rawUpdate('UPDATE suppliers SET is_synced = 1 WHERE is_synced = 0');
          }
          if (branches.isNotEmpty) {
            await txn.rawUpdate('UPDATE branches SET is_synced = 1 WHERE is_synced = 0');
          }
          if (products.isNotEmpty) {
            await txn.rawUpdate('UPDATE inventory SET is_synced = 1 WHERE is_synced = 0');
          }
        });

        return true;
      } else {
        // تسجيل الفشل على pending_sync_states فقط (الجداول الأخرى ستُعاد في الجولة القادمة)
        for (var row in pendingRows) {
          await dbHelper.incrementSyncRetryCount(
            row['id'] as int,
            'HTTP ${response.statusCode}: ${response.body.substring(0, response.body.length.clamp(0, 200))}',
          );
        }
        return false;
      }
    } catch (e) {
      // تسجيل الخطأ
      try {
        final dbHelper = DatabaseHelper();
        final pendingRows = await dbHelper.getPendingSyncStatesToProcess();
        for (var row in pendingRows) {
          await dbHelper.incrementSyncRetryCount(row['id'] as int, e.toString());
        }
      } catch (_) {}
      return false;
    } finally {
      _isSyncing = false;
    }
  }
}
