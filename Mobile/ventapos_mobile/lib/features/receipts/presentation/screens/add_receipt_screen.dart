import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../providers/receipt_form_provider.dart';
import '../widgets/customer_info_section.dart';
import '../widgets/cart_section.dart';
import '../widgets/financials_section.dart';

class AddReceiptScreen extends ConsumerWidget {
  const AddReceiptScreen({super.key});

  void _onSave(BuildContext context, WidgetRef ref) async {
    final state = ref.read(receiptFormProvider);
    
    // Show Confirmation Dialog First
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) {
        return Directionality(
          textDirection: TextDirection.rtl,
          child: AlertDialog(
            title: const Text('تأكيد حفظ الفاتورة'),
            content: Text(
              'إجمالي الفاتورة: ${state.totalCartValue} ج\n'
              'المقدم: ${state.downPayment} ج\n'
              'عدد الأصناف: ${state.cart.length}\n\n'
              'هل أنت متأكد من حفظ هذه الفاتورة؟'
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(ctx).pop(false),
                child: const Text('إلغاء', style: TextStyle(color: Colors.red)),
              ),
              ElevatedButton(
                onPressed: () => Navigator.of(ctx).pop(true),
                child: const Text('تأكيد وحفظ'),
              ),
            ],
          ),
        );
      },
    );

    if (confirm != true) return;
    if (!context.mounted) return;

    final notifier = ref.read(receiptFormProvider.notifier);
    final error = await notifier.submitForm();

    if (!context.mounted) return;

    if (error != null) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text(error),
        backgroundColor: Colors.red,
      ));
    } else {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content: Text('تم حفظ الفاتورة بنجاح!'),
        backgroundColor: Colors.green,
      ));
      Navigator.of(context).pop();
    }
  }

  Future<bool> _onWillPop(BuildContext context) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) {
        return Directionality(
          textDirection: TextDirection.rtl,
          child: AlertDialog(
            title: const Text('تأكيد الخروج'),
            content: const Text('هل أنت متأكد من الخروج؟ سيتم مسح بيانات الفاتورة الحالية.'),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(ctx).pop(false),
                child: const Text('بقاء'),
              ),
              TextButton(
                onPressed: () => Navigator.of(ctx).pop(true),
                child: const Text('خروج', style: TextStyle(color: Colors.red)),
              ),
            ],
          ),
        );
      },
    );
    return confirm ?? false;
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(receiptFormProvider);
    final notifier = ref.read(receiptFormProvider.notifier);

    return Directionality(
      textDirection: TextDirection.rtl,
      child: PopScope(
        canPop: false,
        onPopInvoked: (didPop) async {
          if (didPop) return;
          final shouldPop = await _onWillPop(context);
          if (shouldPop && context.mounted) {
            Navigator.of(context).pop();
          }
        },
        child: Scaffold(
          appBar: AppBar(
            title: const Text('نقطة البيع (الفاتورة)'),
          ),
          body: SafeArea(
            child: ListView(
              padding: const EdgeInsets.all(16.0),
              children: [
                // Cash Sale Toggle
                Card(
                  margin: const EdgeInsets.only(bottom: 16.0),
                  child: SwitchListTile(
                    title: const Text('بيع نقدي بالكامل (كاش بدون أقساط)', style: TextStyle(fontWeight: FontWeight.bold)),
                    value: state.isCashSale,
                    onChanged: (val) {
                      notifier.toggleCashSale(val);
                    },
                  ),
                ),

                // Date Selection (always visible)
                Card(
                  margin: const EdgeInsets.only(bottom: 16.0),
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Row(
                      children: [
                        Expanded(
                          child: DropdownButtonFormField<int>(
                            decoration: const InputDecoration(labelText: 'شهر البيع'),
                            value: state.saleMonth,
                            items: List.generate(12, (i) => i + 1).map((m) {
                              return DropdownMenuItem(value: m, child: Text(m.toString()));
                            }).toList(),
                            onChanged: (val) {
                              if (val != null) notifier.setSaleDate(val, state.saleYear);
                            },
                          ),
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: TextFormField(
                            initialValue: state.saleYear.toString(),
                            keyboardType: TextInputType.number,
                            textInputAction: TextInputAction.next,
                            decoration: const InputDecoration(labelText: 'سنة البيع'),
                            onChanged: (val) {
                              final year = int.tryParse(val) ?? state.saleYear;
                              notifier.setSaleDate(state.saleMonth, year);
                            },
                          ),
                        ),
                      ],
                    ),
                  ),
                ),

                // Customer Info (Hidden if Cash Sale)
                if (!state.isCashSale) const CustomerInfoSection(),

                // Cart (Always Visible)
                const CartSection(),

                // Financials (Hidden if Cash Sale)
                if (!state.isCashSale) const FinancialsSection(),
                
                const SizedBox(height: 80), // Padding to avoid being blocked by bottom bar
              ],
            ),
          ),
          bottomNavigationBar: SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.green,
                  padding: const EdgeInsets.symmetric(vertical: 16.0),
                ),
                onPressed: () => _onSave(context, ref),
                child: const Text('حفظ الفاتورة', style: TextStyle(fontSize: 18, color: Colors.white, fontWeight: FontWeight.bold)),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
