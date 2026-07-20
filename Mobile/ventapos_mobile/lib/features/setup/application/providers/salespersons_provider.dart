import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../domain/models/salesperson_model.dart';
import '../../infrastructure/repositories/setup_repository.dart';

class SalespersonsNotifier extends AsyncNotifier<List<SalespersonModel>> {
  late final SetupRepository _repository;

  @override
  FutureOr<List<SalespersonModel>> build() async {
    _repository = SetupRepository();
    return await _repository.getSalespersons();
  }

  Future<void> addSalesperson(SalespersonModel salesperson) async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() async {
      await _repository.addSalesperson(salesperson);
      return await _repository.getSalespersons();
    });
  }

  Future<void> updateSalesperson(SalespersonModel salesperson) async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() async {
      await _repository.updateSalesperson(salesperson);
      return await _repository.getSalespersons();
    });
  }

  Future<void> deleteSalesperson(int id) async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() async {
      await _repository.deleteSalesperson(id);
      return await _repository.getSalespersons();
    });
  }
}

final salespersonsNotifierProvider = AsyncNotifierProvider<SalespersonsNotifier, List<SalespersonModel>>(() => SalespersonsNotifier());
