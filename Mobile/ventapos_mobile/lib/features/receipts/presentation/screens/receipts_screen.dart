import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/widgets/app_drawer.dart';

import '../../providers/receipt_view_provider.dart';
import '../widgets/receipt_card_view.dart';
import '../widgets/receipt_horizontal_view.dart';
import '../widgets/receipt_accordion_view.dart';
import '../widgets/receipt_master_detail_view.dart';

class ReceiptsScreen extends ConsumerWidget {
  const ReceiptsScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final viewMode = ref.watch(receiptViewModeProvider);
    final receipts = ref.watch(dummyReceiptsProvider);

    return Scaffold(
      backgroundColor: const Color(0xFFF4F6F9),
      drawer: const AppDrawer(),
      appBar: AppBar(
        title: const Text('سجل الفواتير', style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.blue.shade700,
        foregroundColor: Colors.white,
        actions: [
          Padding(
            padding: const EdgeInsets.only(left: 16.0),
            child: DropdownButton<ReceiptViewMode>(
              value: viewMode,
              dropdownColor: Colors.white,
              icon: const Icon(Icons.arrow_drop_down, color: Colors.white),
              underline: const SizedBox(),
              style: const TextStyle(color: Colors.blue, fontSize: 13, fontWeight: FontWeight.bold),
              selectedItemBuilder: (BuildContext context) {
                return ReceiptViewMode.values.map<Widget>((ReceiptViewMode item) {
                  return Center(
                    child: Text(
                      _getModeName(item),
                      style: const TextStyle(color: Colors.white),
                    ),
                  );
                }).toList();
              },
              items: ReceiptViewMode.values.map((ReceiptViewMode mode) {
                return DropdownMenuItem<ReceiptViewMode>(
                  value: mode,
                  child: Text(_getModeName(mode)),
                );
              }).toList(),
              onChanged: (ReceiptViewMode? newValue) {
                if (newValue != null) {
                  ref.read(receiptViewModeProvider.notifier).setMode(newValue);
                }
              },
            ),
          )
        ],
      ),
      body: _buildBody(viewMode, receipts),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () {
          context.go('/receipts/add');
        },
        backgroundColor: Colors.blue.shade700,
        foregroundColor: Colors.white,
        icon: const Icon(Icons.add),
        label: const Text('إضافة فاتورة', style: TextStyle(fontWeight: FontWeight.bold)),
      ),
    );
  }

  String _getModeName(ReceiptViewMode mode) {
    switch (mode) {
      case ReceiptViewMode.masterDetail:
        return 'رئيسي/تفاصيل';
      case ReceiptViewMode.card:
        return 'بطاقات شاملة';
      case ReceiptViewMode.horizontal:
        return 'جدول أفقي';
      case ReceiptViewMode.accordion:
        return 'قوائم منسدلة';
    }
  }

  Widget _buildBody(ReceiptViewMode mode, receipts) {
    switch (mode) {
      case ReceiptViewMode.masterDetail:
        return ReceiptMasterDetailView(receipts: receipts);
      case ReceiptViewMode.card:
        return ReceiptCardView(receipts: receipts);
      case ReceiptViewMode.horizontal:
        return ReceiptHorizontalView(receipts: receipts);
      case ReceiptViewMode.accordion:
        return ReceiptAccordionView(receipts: receipts);
    }
  }
}
