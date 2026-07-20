import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../application/providers/salespersons_provider.dart';
import '../../domain/models/salesperson_model.dart';

class SalespersonsTab extends ConsumerStatefulWidget {
  const SalespersonsTab({super.key});

  @override
  ConsumerState<SalespersonsTab> createState() => _SalespersonsTabState();
}

class _SalespersonsTabState extends ConsumerState<SalespersonsTab> {
  final _nameController = TextEditingController();

  @override
  void dispose() {
    _nameController.dispose();
    super.dispose();
  }

  void _addSalesperson() {
    final name = _nameController.text.trim();
    if (name.isNotEmpty) {
      final newPerson = SalespersonModel(id: 0, branchId: 1, name: name);
      ref.read(salespersonsNotifierProvider.notifier).addSalesperson(newPerson);
      _nameController.clear();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('تم إضافة المندوب بنجاح')),
      );
    }
  }

  void _editSalesperson(SalespersonModel person) {
    final editController = TextEditingController(text: person.name);
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('تعديل اسم المندوب'),
        content: TextField(
          controller: editController,
          decoration: const InputDecoration(labelText: 'الاسم الجديد'),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('إلغاء')),
          ElevatedButton(
            onPressed: () {
              final newName = editController.text.trim();
              if (newName.isNotEmpty) {
                ref.read(salespersonsNotifierProvider.notifier)
                   .updateSalesperson(person.copyWith(name: newName));
              }
              Navigator.pop(ctx);
            },
            child: const Text('حفظ'),
          ),
        ],
      ),
    );
  }

  void _deleteSalesperson(int id) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('تأكيد الحذف'),
        content: const Text('هل أنت متأكد من حذف هذا المندوب؟'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('إلغاء')),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            onPressed: () {
              ref.read(salespersonsNotifierProvider.notifier).deleteSalesperson(id);
              Navigator.pop(ctx);
            },
            child: const Text('حذف'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(salespersonsNotifierProvider);

    return Column(
      children: [
        Card(
          margin: const EdgeInsets.all(8.0),
          child: Padding(
            padding: const EdgeInsets.all(12.0),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _nameController,
                    decoration: const InputDecoration(labelText: 'اسم المندوب'),
                  ),
                ),
                const SizedBox(width: 8),
                ElevatedButton(
                  onPressed: _addSalesperson,
                  child: const Text('إضافة'),
                ),
              ],
            ),
          ),
        ),
        Expanded(
          child: state.when(
            data: (list) => ListView.builder(
              itemCount: list.length,
              itemBuilder: (context, index) {
                final person = list[index];
                return ListTile(
                  title: Text(person.name),
                  trailing: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      IconButton(
                        icon: const Icon(Icons.edit, color: Colors.orange),
                        onPressed: () => _editSalesperson(person),
                      ),
                      IconButton(
                        icon: const Icon(Icons.delete, color: Colors.red),
                        onPressed: () => _deleteSalesperson(person.id),
                      ),
                    ],
                  ),
                );
              },
            ),
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (err, stack) => Center(child: Text('خطأ: $err')),
          ),
        ),
      ],
    );
  }
}
