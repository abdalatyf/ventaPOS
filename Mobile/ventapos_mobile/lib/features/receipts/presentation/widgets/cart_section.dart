import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../providers/receipt_form_provider.dart';
import 'debounced_typeahead.dart';

class CartSection extends ConsumerStatefulWidget {
  const CartSection({super.key});

  @override
  ConsumerState<CartSection> createState() => _CartSectionState();
}

class _CartSectionState extends ConsumerState<CartSection> {
  Map<String, dynamic>? _selectedProduct;
  final TextEditingController _qtyController = TextEditingController(text: '1');
  final TextEditingController _priceController = TextEditingController();

  @override
  void dispose() {
    _qtyController.dispose();
    _priceController.dispose();
    super.dispose();
  }

  void _onAdd() {
    if (_selectedProduct == null) return;
    
    final qty = int.tryParse(_qtyController.text) ?? 1;
    final price = double.tryParse(_priceController.text) ?? 0.0;
    
    if (qty <= 0 || price <= 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('الكمية والسعر يجب أن يكونا أكبر من صفر')),
      );
      return;
    }

    final maxStock = _selectedProduct!['current_stock'] as int;
    
    final error = ref.read(receiptFormProvider.notifier).addToCart(
      inventoryItemId: _selectedProduct!['id'] as int,
      name: _selectedProduct!['name'] as String,
      quantity: qty,
      price: price,
      maxStock: maxStock,
    );

    if (error != null) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(error)));
    } else {
      // Clear selections
      setState(() {
        _selectedProduct = null;
        _qtyController.text = '1';
        _priceController.text = '';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final repo = ref.watch(receiptRepositoryProvider);
    final state = ref.watch(receiptFormProvider);
    final notifier = ref.read(receiptFormProvider.notifier);

    return Card(
      margin: const EdgeInsets.symmetric(vertical: 8.0),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('البضاعة (الخزنة)', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 16),
            
            DebouncedTypeahead<Map<String, dynamic>>(
              initialValue: _selectedProduct != null ? _selectedProduct!['name'] as String : '',
              suggestionsCallback: (pattern) => repo.searchProducts(pattern),
              textInputAction: TextInputAction.next,
              itemBuilder: (context, suggestion) {
                return ListTile(
                  title: Text(suggestion['name'] as String),
                  subtitle: Text('المتاح: ${suggestion['current_stock']}'),
                );
              },
              onSuggestionSelected: (suggestion) {
                setState(() {
                  _selectedProduct = suggestion;
                  _priceController.text = (suggestion['current_price'] as num).toString();
                });
              },
              displayStringForOption: (s) => s['name'] as String,
              decoration: const InputDecoration(labelText: 'ابحث عن الصنف...'),
            ),
            const SizedBox(height: 16),

            Row(
              children: [
                Expanded(
                  flex: 1,
                  child: TextField(
                    controller: _qtyController,
                    keyboardType: TextInputType.number,
                    textInputAction: TextInputAction.next,
                    decoration: const InputDecoration(labelText: 'الكمية'),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  flex: 2,
                  child: TextField(
                    controller: _priceController,
                    keyboardType: TextInputType.number,
                    textInputAction: TextInputAction.done,
                    onSubmitted: (_) => _onAdd(),
                    decoration: const InputDecoration(labelText: 'سعر البيع'),
                  ),
                ),
                const SizedBox(width: 8),
                ElevatedButton(
                  onPressed: _onAdd,
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 16),
                  ),
                  child: const Text('إضافة'),
                ),
              ],
            ),
            const SizedBox(height: 16),

            if (state.cart.isNotEmpty)
              Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  ListView.builder(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    itemCount: state.cart.length,
                    itemBuilder: (context, index) {
                      final item = state.cart[index];
                      return Card(
                        color: Colors.blue.shade50,
                        elevation: 0,
                        margin: const EdgeInsets.only(bottom: 8.0),
                        child: ListTile(
                          title: Text(item.name, style: const TextStyle(fontWeight: FontWeight.bold)),
                          subtitle: Text('الكمية: ${item.quantity} × السعر: ${item.price} = ${item.total} ج'),
                          trailing: IconButton(
                            icon: const Icon(Icons.delete, color: Colors.red),
                            onPressed: () => notifier.removeFromCart(index),
                          ),
                        ),
                      );
                    },
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'إجمالي الفاتورة: ${state.totalCartValue} ج',
                    style: const TextStyle(
                      fontSize: 18, 
                      fontWeight: FontWeight.bold, 
                      color: Colors.green
                    ),
                    textAlign: TextAlign.end,
                  ),
                ],
              ),
          ],
        ),
      ),
    );
  }
}
