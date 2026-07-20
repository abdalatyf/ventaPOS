import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../providers/receipt_form_provider.dart';
import 'debounced_typeahead.dart';

class CustomerInfoSection extends ConsumerStatefulWidget {
  const CustomerInfoSection({Key? key}) : super(key: key);

  @override
  ConsumerState<CustomerInfoSection> createState() => _CustomerInfoSectionState();
}

class _CustomerInfoSectionState extends ConsumerState<CustomerInfoSection> {
  List<Map<String, dynamic>> _salespeople = [];

  @override
  void initState() {
    super.initState();
    _loadSalespeople();
  }

  Future<void> _loadSalespeople() async {
    final repo = ref.read(receiptRepositoryProvider);
    final sp = await repo.getSalespeople();
    setState(() {
      _salespeople = sp;
    });
  }

  @override
  Widget build(BuildContext context) {
    final repo = ref.watch(receiptRepositoryProvider);
    final customer = ref.watch(receiptFormProvider.select((state) => state.customer));
    final notifier = ref.read(receiptFormProvider.notifier);

    return Card(
      margin: const EdgeInsets.symmetric(vertical: 8.0),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('بيانات العميل', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 16),
            // Name
            DebouncedTypeahead<String>(
              initialValue: customer.name,
              suggestionsCallback: (pattern) => repo.searchCustomerField(pattern, 'customer_name'),
              itemBuilder: (context, suggestion) => ListTile(title: Text(suggestion)),
              onSuggestionSelected: (suggestion) {
                notifier.updateCustomerField(name: suggestion);
              },
              displayStringForOption: (s) => s,
              decoration: const InputDecoration(labelText: 'اسم العميل'),
              textInputAction: TextInputAction.next,
            ),
            const SizedBox(height: 16),
            // Phone
            DebouncedTypeahead<String>(
              initialValue: customer.phone,
              suggestionsCallback: (pattern) => repo.searchCustomerField(pattern, 'phone_number'),
              itemBuilder: (context, suggestion) => ListTile(title: Text(suggestion)),
              onSuggestionSelected: (suggestion) {
                notifier.updateCustomerField(phone: suggestion);
              },
              displayStringForOption: (s) => s,
              decoration: const InputDecoration(labelText: 'تليفون العميل'),
              textInputAction: TextInputAction.next,
            ),
            const SizedBox(height: 16),
            // Area
            DebouncedTypeahead<String>(
              initialValue: customer.area,
              suggestionsCallback: (pattern) => repo.searchCustomerField(pattern, 'area'),
              itemBuilder: (context, suggestion) => ListTile(title: Text(suggestion)),
              onSuggestionSelected: (suggestion) {
                notifier.updateCustomerField(area: suggestion);
              },
              displayStringForOption: (s) => s,
              decoration: const InputDecoration(labelText: 'المنطقة'),
              textInputAction: TextInputAction.next,
            ),
            const SizedBox(height: 16),
            // Address
            DebouncedTypeahead<String>(
              initialValue: customer.address,
              suggestionsCallback: (pattern) => repo.searchCustomerField(pattern, 'address'),
              itemBuilder: (context, suggestion) => ListTile(title: Text(suggestion)),
              onSuggestionSelected: (suggestion) {
                notifier.updateCustomerField(address: suggestion);
              },
              displayStringForOption: (s) => s,
              decoration: const InputDecoration(labelText: 'العنوان'),
              textInputAction: TextInputAction.next,
            ),
            const SizedBox(height: 16),
            // Salesperson Dropdown
            DropdownButtonFormField<int?>(
              value: customer.salespersonId,
              decoration: const InputDecoration(labelText: 'المندوب / مسؤول المبيعات'),
              items: [
                const DropdownMenuItem(value: null, child: Text('-- اختياري --')),
                ..._salespeople.map((sp) {
                  return DropdownMenuItem<int?>(
                    value: sp['id'] as int,
                    child: Text(sp['name'] as String),
                  );
                }).toList(),
              ],
              onChanged: (val) {
                if (val == null) {
                  notifier.updateCustomerField(clearSalesperson: true);
                } else {
                  notifier.updateCustomerField(salespersonId: val);
                }
              },
            ),
          ],
        ),
      ),
    );
  }
}
