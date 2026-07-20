import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../domain/models/inventory_item_model.dart';
import '../../domain/models/commission_history_model.dart';
import '../../infrastructure/repositories/setup_repository.dart';

class InventoryNotifier extends AsyncNotifier<List<InventoryItemModel>> {
  late final SetupRepository _repository;

  @override
  FutureOr<List<InventoryItemModel>> build() async {
    _repository = SetupRepository();
    return await _repository.getInventoryItems();
  }

  Future<void> addItem(InventoryItemModel item) async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() async {
      await _repository.addInventoryItem(item);
      return await _repository.getInventoryItems();
    });
  }

  Future<void> updateItem(InventoryItemModel item) async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() async {
      await _repository.updateInventoryItem(item);
      return await _repository.getInventoryItems();
    });
  }

  Future<void> deleteItem(int id) async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() async {
      await _repository.deleteInventoryItem(id);
      return await _repository.getInventoryItems();
    });
  }
}

final inventoryNotifierProvider = AsyncNotifierProvider<InventoryNotifier, List<InventoryItemModel>>(() => InventoryNotifier());

final commissionHistoryNotifierProvider = FutureProvider.family<List<CommissionHistoryModel>, int>((ref, int arg) async {
  final repository = SetupRepository();
  return await repository.getCommissionHistory(arg);
});
