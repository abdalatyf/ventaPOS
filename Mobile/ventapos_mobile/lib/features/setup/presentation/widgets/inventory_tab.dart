import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../application/providers/inventory_provider.dart';
import '../../domain/models/inventory_item_model.dart';
import '../../domain/models/commission_history_model.dart';
import '../../infrastructure/repositories/setup_repository.dart';

class InventoryTab extends ConsumerStatefulWidget {
  const InventoryTab({super.key});

  @override
  ConsumerState<InventoryTab> createState() => _InventoryTabState();
}

class _InventoryTabState extends ConsumerState<InventoryTab> {
  final _formKey = GlobalKey<FormState>();
  
  // Controllers
  final _nameController = TextEditingController();
  final _qtyController = TextEditingController();
  final _priceController = TextEditingController();
  final _commissionController = TextEditingController();
  
  int _selectedMonth = DateTime.now().month;
  int _selectedYear = DateTime.now().year;
  
  InventoryItemModel? _editingItem;
  String _searchQuery = '';

  @override
  void dispose() {
    _nameController.dispose();
    _qtyController.dispose();
    _priceController.dispose();
    _commissionController.dispose();
    super.dispose();
  }

  void _submitForm() {
    if (_formKey.currentState!.validate()) {
      final name = _nameController.text;
      final qty = int.tryParse(_qtyController.text) ?? 0;
      final price = int.tryParse(_priceController.text) ?? 0;
      final commission = int.tryParse(_commissionController.text) ?? 0;
      
      if (_editingItem == null) {
        // Add
        final newItem = InventoryItemModel(
          id: 0,
          branchId: 1, // Default branch
          name: name,
          currentStock: qty,
          currentPrice: price,
          currentCommission: commission,
          startMonth: _selectedMonth,
          startYear: _selectedYear,
        );
        ref.read(inventoryNotifierProvider.notifier).addItem(newItem);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('تمت إضافة الصنف بنجاح')),
        );
      } else {
        // Edit
        final updatedItem = _editingItem!.copyWith(
          name: name,
          currentStock: qty,
          currentPrice: price,
          currentCommission: commission,
          startMonth: _selectedMonth,
          startYear: _selectedYear,
        );
        ref.read(inventoryNotifierProvider.notifier).updateItem(updatedItem);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('تم تعديل الصنف بنجاح')),
        );
      }
      
      _resetForm();
    }
  }

  void _resetForm() {
    _editingItem = null;
    _nameController.clear();
    _qtyController.clear();
    _priceController.clear();
    _commissionController.clear();
    setState(() {
      _selectedMonth = DateTime.now().month;
      _selectedYear = DateTime.now().year;
    });
  }

  void _editItem(InventoryItemModel item) {
    setState(() {
      _editingItem = item;
      _nameController.text = item.name;
      _qtyController.text = item.currentStock.toString();
      _priceController.text = item.currentPrice.toString();
      _commissionController.text = item.currentCommission.toString();
      _selectedMonth = item.startMonth;
      _selectedYear = item.startYear;
    });
  }

  void _deleteItem(int id) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('تأكيد الحذف'),
        content: const Text('هل أنت متأكد من حذف هذا الصنف؟'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('إلغاء'),
          ),
          ElevatedButton(
            onPressed: () {
              ref.read(inventoryNotifierProvider.notifier).deleteItem(id);
              Navigator.pop(ctx);
            },
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            child: const Text('حذف'),
          ),
        ],
      ),
    );
  }

  void _showCommissionTimeMachine(InventoryItemModel item) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (ctx) => CommissionTimeMachineSheet(item: item),
    );
  }

  @override
  Widget build(BuildContext context) {
    final inventoryState = ref.watch(inventoryNotifierProvider);

    return Column(
      children: [
        // Form Card
        Card(
          margin: const EdgeInsets.all(8.0),
          child: Padding(
            padding: const EdgeInsets.all(12.0),
            child: Form(
              key: _formKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    _editingItem == null ? 'إضافة صنف جديد' : 'تعديل صنف',
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      Expanded(
                        flex: 2,
                        child: TextFormField(
                          controller: _nameController,
                          decoration: const InputDecoration(labelText: 'اسم الصنف'),
                          validator: (val) => val == null || val.isEmpty ? 'مطلوب' : null,
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: TextFormField(
                          controller: _qtyController,
                          decoration: const InputDecoration(labelText: 'الرصيد الافتتاحي'),
                          keyboardType: TextInputType.number,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      Expanded(
                        child: TextFormField(
                          controller: _priceController,
                          decoration: const InputDecoration(labelText: 'سعر الشراء الافتتاحي'),
                          keyboardType: TextInputType.number,
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: TextFormField(
                          controller: _commissionController,
                          decoration: const InputDecoration(labelText: 'قيمة العمولة الافتتاحية'),
                          keyboardType: TextInputType.number,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      Expanded(
                        child: DropdownButtonFormField<int>(
                          value: _selectedMonth,
                          decoration: const InputDecoration(labelText: 'شهر البداية'),
                          items: List.generate(12, (index) {
                            return DropdownMenuItem(
                              value: index + 1,
                              child: Text('${index + 1}'),
                            );
                          }),
                          onChanged: (val) {
                            if (val != null) setState(() => _selectedMonth = val);
                          },
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: TextFormField(
                          initialValue: _selectedYear.toString(),
                          decoration: const InputDecoration(labelText: 'سنة البداية'),
                          keyboardType: TextInputType.number,
                          onChanged: (val) {
                            final y = int.tryParse(val);
                            if (y != null) _selectedYear = y;
                          },
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.end,
                    children: [
                      if (_editingItem != null)
                        TextButton(
                          onPressed: _resetForm,
                          child: const Text('إلغاء التعديل'),
                        ),
                      ElevatedButton(
                        onPressed: _submitForm,
                        child: Text(_editingItem == null ? 'إضافة' : 'حفظ'),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ),

        // Search Bar
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8.0),
          child: TextField(
            decoration: const InputDecoration(
              hintText: 'بحث باسم الصنف...',
              prefixIcon: Icon(Icons.search),
              border: OutlineInputBorder(),
            ),
            onChanged: (val) => setState(() => _searchQuery = val.toLowerCase()),
          ),
        ),

        // List
        Expanded(
          child: inventoryState.when(
            data: (items) {
              final filtered = items.where((item) => item.name.toLowerCase().contains(_searchQuery)).toList();
              
              int totalItems = filtered.length;
              int totalValue = filtered.fold(0, (sum, item) => sum + (item.currentStock * item.currentPrice));

              return Column(
                children: [
                  Padding(
                    padding: const EdgeInsets.all(8.0),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text('إجمالي الأصناف: $totalItems', style: const TextStyle(fontWeight: FontWeight.bold)),
                        Text('إجمالي القيمة: $totalValue', style: const TextStyle(fontWeight: FontWeight.bold)),
                      ],
                    ),
                  ),
                  Expanded(
                    child: ListView.builder(
                      itemCount: filtered.length,
                      itemBuilder: (context, index) {
                        final item = filtered[index];
                        final isLowStock = item.currentStock <= 5;
                        
                        return ListTile(
                          title: Row(
                            children: [
                              Text(item.name),
                              if (isLowStock) ...[
                                const SizedBox(width: 8),
                                const Icon(Icons.warning_amber_rounded, color: Colors.red, size: 16),
                              ]
                            ],
                          ),
                          subtitle: Text('الرصيد: ${item.currentStock} | السعر: ${item.currentPrice} | العمولة: ${item.currentCommission}'),
                          trailing: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              IconButton(
                                icon: const Icon(Icons.history, color: Colors.blue),
                                onPressed: () => _showCommissionTimeMachine(item),
                                tooltip: 'سجل العمولات',
                              ),
                              IconButton(
                                icon: const Icon(Icons.edit, color: Colors.orange),
                                onPressed: () => _editItem(item),
                              ),
                              IconButton(
                                icon: const Icon(Icons.delete, color: Colors.red),
                                onPressed: () => _deleteItem(item.id),
                              ),
                            ],
                          ),
                        );
                      },
                    ),
                  ),
                ],
              );
            },
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (err, stack) => Center(child: Text('خطأ: $err')),
          ),
        ),
      ],
    );
  }
}

class CommissionTimeMachineSheet extends ConsumerStatefulWidget {
  final InventoryItemModel item;
  const CommissionTimeMachineSheet({super.key, required this.item});

  @override
  ConsumerState<CommissionTimeMachineSheet> createState() => _CommissionTimeMachineSheetState();
}

class _CommissionTimeMachineSheetState extends ConsumerState<CommissionTimeMachineSheet> {
  final _amountCtrl = TextEditingController();
  int _selectedMonth = DateTime.now().month;
  int _selectedYear = DateTime.now().year;

  @override
  void dispose() {
    _amountCtrl.dispose();
    super.dispose();
  }

  Future<void> _addCommission() async {
    final amount = int.tryParse(_amountCtrl.text);
    if (amount != null) {
      final newCommission = CommissionHistoryModel(
        inventoryItemId: widget.item.id,
        commissionAmount: amount,
        startMonth: _selectedMonth,
        startYear: _selectedYear,
        createdAtLocal: DateTime.now().toIso8601String(),
      );
      await SetupRepository().addCommissionHistory(newCommission);
      ref.refresh(commissionHistoryNotifierProvider(widget.item.id));
      _amountCtrl.clear();
    }
  }

  @override
  Widget build(BuildContext context) {
    final historyState = ref.watch(commissionHistoryNotifierProvider(widget.item.id));
    
    return Padding(
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(context).viewInsets.bottom,
        left: 16, right: 16, top: 16,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('سجل عمولات: ${widget.item.name}', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _amountCtrl,
                  decoration: const InputDecoration(labelText: 'قيمة العمولة'),
                  keyboardType: TextInputType.number,
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: DropdownButtonFormField<int>(
                  value: _selectedMonth,
                  decoration: const InputDecoration(labelText: 'الشهر'),
                  items: List.generate(12, (index) => DropdownMenuItem(value: index + 1, child: Text('${index + 1}'))),
                  onChanged: (val) { if (val != null) setState(() => _selectedMonth = val); },
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: TextFormField(
                  initialValue: _selectedYear.toString(),
                  decoration: const InputDecoration(labelText: 'السنة'),
                  keyboardType: TextInputType.number,
                  onChanged: (val) {
                    final y = int.tryParse(val);
                    if (y != null) _selectedYear = y;
                  },
                ),
              ),
              IconButton(
                icon: const Icon(Icons.add_circle, color: Colors.green, size: 36),
                onPressed: _addCommission,
              )
            ],
          ),
          const SizedBox(height: 16),
          SizedBox(
            height: 200,
            child: historyState.when(
              data: (history) => ListView.builder(
                itemCount: history.length,
                itemBuilder: (ctx, i) {
                  final h = history[i];
                  return ListTile(
                    title: Text('العمولة: ${h.commissionAmount}'),
                    subtitle: Text('بداية من: ${h.startMonth}/${h.startYear}'),
                  );
                },
              ),
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (err, stack) => Text('خطأ: $err'),
            ),
          ),
        ],
      ),
    );
  }
}
