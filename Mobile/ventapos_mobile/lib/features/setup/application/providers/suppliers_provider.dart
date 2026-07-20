import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../domain/models/supplier_model.dart';
import '../../infrastructure/repositories/setup_repository.dart';

class SuppliersNotifier extends AsyncNotifier<List<SupplierModel>> {
  late final SetupRepository _repository;

  @override
  FutureOr<List<SupplierModel>> build() async {
    _repository = SetupRepository();
    return await _repository.getSuppliers();
  }

  Future<void> addSupplier(SupplierModel supplier) async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() async {
      await _repository.addSupplier(supplier);
      return await _repository.getSuppliers();
    });
  }

  Future<void> deleteSupplier(int id) async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() async {
      await _repository.deleteSupplier(id);
      return await _repository.getSuppliers();
    });
  }
}

final suppliersNotifierProvider = AsyncNotifierProvider<SuppliersNotifier, List<SupplierModel>>(() => SuppliersNotifier());
