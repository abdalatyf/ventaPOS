import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../providers/receipt_form_provider.dart';

class FinancialsSection extends ConsumerWidget {
  const FinancialsSection({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(receiptFormProvider);
    final notifier = ref.read(receiptFormProvider.notifier);

    return Card(
      margin: const EdgeInsets.symmetric(vertical: 8.0),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('الماليات: المقدم ونظام التقسيط', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 16),
            
            // Downpayment
            TextFormField(
              initialValue: state.downPayment > 0 ? state.downPayment.toString() : '',
              keyboardType: TextInputType.number,
              textInputAction: TextInputAction.next,
              decoration: const InputDecoration(
                labelText: 'المقدم (كاش)',
                labelStyle: TextStyle(fontWeight: FontWeight.bold, color: Colors.blue),
                border: OutlineInputBorder(),
              ),
              onChanged: (val) {
                notifier.updateDownPayment(double.tryParse(val) ?? 0.0);
              },
            ),
            const SizedBox(height: 24),
            
            Text('نظام التقسيط (٣ مجموعات اختياري)', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),

            // 3 Groups
            ...List.generate(3, (index) {
              final group = state.groups[index];
              return Padding(
                padding: const EdgeInsets.only(bottom: 8.0),
                child: Row(
                  children: [
                    Expanded(
                      child: TextFormField(
                        initialValue: group.amount?.toString() ?? '',
                        keyboardType: TextInputType.number,
                        textInputAction: TextInputAction.next,
                        decoration: InputDecoration(labelText: 'القسط م${index + 1}'),
                        onChanged: (val) {
                          notifier.updateInstallmentGroup(index, amount: double.tryParse(val), count: group.count);
                        },
                      ),
                    ),
                    const Padding(
                      padding: EdgeInsets.symmetric(horizontal: 8.0),
                      child: Text('x', style: TextStyle(fontWeight: FontWeight.bold)),
                    ),
                    Expanded(
                      child: TextFormField(
                        initialValue: group.count?.toString() ?? '',
                        keyboardType: TextInputType.number,
                        textInputAction: TextInputAction.next,
                        decoration: InputDecoration(labelText: 'عدد الشهور م${index + 1}'),
                        onChanged: (val) {
                          notifier.updateInstallmentGroup(index, amount: group.amount, count: int.tryParse(val));
                        },
                      ),
                    ),
                  ],
                ),
              );
            }),
            const SizedBox(height: 24),


            // Validation Summary
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.blue.shade50,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Column(
                children: [
                  _SummaryRow(label: 'إجمالي الفاتورة:', value: state.totalCartValue),
                  _SummaryRow(label: 'المقدم المدفوع:', value: state.downPayment),
                  _SummaryRow(label: 'إجمالي الأقساط:', value: state.totalInstallments),
                  const Divider(),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text('المجموع (المقدم + الأقساط):', style: TextStyle(fontWeight: FontWeight.bold)),
                      Text(
                        '${state.totalPaidAndInstallments} ج', 
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          color: state.isValidTotal ? Colors.green : Colors.red,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _SummaryRow extends StatelessWidget {
  final String label;
  final double value;

  const _SummaryRow({Key? key, required this.label, required this.value}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label),
          Text('$value ج', style: const TextStyle(fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }
}
