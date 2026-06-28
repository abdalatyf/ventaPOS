import 'package:flutter/material.dart';
import 'package:flareline_uikit/components/card/common_card.dart';
import 'package:flareline_uikit/core/theme/flareline_colors.dart';
import '../db/database_helper.dart';
import '../services/sync_worker.dart';

class SyncHubScreen extends StatefulWidget {
  const SyncHubScreen({super.key});

  @override
  State<SyncHubScreen> createState() => _SyncHubScreenState();
}

class _SyncHubScreenState extends State<SyncHubScreen> {
  Map<String, int> _unsyncedCounts = {};
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _loadCounts();
  }

  Future<void> _loadCounts() async {
    final db = await DatabaseHelper.instance.database;
    final tables = [
      'receipts', 'receipt_items', 'installment_payments',
      'expenses', 'purchase_invoices', 'purchase_invoice_items',
      'inventory', 'commission_history', 'branches', 
      'salespersons', 'cloud_users', 'suppliers'
    ];

    Map<String, int> counts = {};
    for (String table in tables) {
      final res = await db.rawQuery('SELECT COUNT(*) as c FROM $table WHERE is_synced = 0');
      int c = (res.first['c'] as int?) ?? 0;
      if (c > 0) {
        counts[table] = c;
      }
    }

    if (mounted) {
      setState(() {
        _unsyncedCounts = counts;
      });
    }
  }

  Future<void> _handleSync() async {
    setState(() {
      _isLoading = true;
    });

    try {
      final success = await SyncWorker().syncNow();
      if (mounted) {
        if (success) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('تمت المزامنة بنجاح')),
          );
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('فشلت المزامنة')),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('فشلت المزامنة')),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
        await _loadCounts();
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    int totalUnsynced = _unsyncedCounts.values.fold(0, (sum, val) => sum + val);

    return Scaffold(
      backgroundColor: FlarelineColors.background,
      appBar: AppBar(
        title: const Text('مركز المزامنة'),
        backgroundColor: FlarelineColors.primary,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            const Icon(Icons.cloud_sync, size: 80, color: FlarelineColors.primary),
            const SizedBox(height: 16),
            Text(
              'إجمالي العناصر المعلقة: $totalUnsynced',
              style: const TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
                color: FlarelineColors.darkBlackText,
              ),
            ),
            const SizedBox(height: 24),
            Expanded(
              child: ListView(
                children: _unsyncedCounts.entries.map((e) => CommonCard(
                  margin: const EdgeInsets.symmetric(vertical: 6),
                  padding: const EdgeInsets.all(8),
                  child: ListTile(
                    leading: const Icon(Icons.table_chart, color: FlarelineColors.primary),
                    title: Text(
                      e.key.toUpperCase(),
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        color: FlarelineColors.darkBlackText,
                      ),
                    ),
                    trailing: CircleAvatar(
                      backgroundColor: FlarelineColors.primary,
                      foregroundColor: Colors.white,
                      child: Text(e.value.toString()),
                    ),
                  ),
                )).toList(),
              ),
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                minimumSize: const Size.fromHeight(60),
                backgroundColor: ButtonColors.primary,
              ),
              onPressed: (totalUnsynced == 0 || _isLoading) ? null : _handleSync,
              child: _isLoading
                  ? const CircularProgressIndicator(color: Colors.white)
                  : const Text(
                      'بدء المزامنة الآن',
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
            ),
          ],
        ),
      ),
    );
  }
}
