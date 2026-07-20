import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../domain/models/receipt_form_state.dart';
import '../domain/repositories/receipt_repository.dart';

final receiptRepositoryProvider = Provider<ReceiptRepository>((ref) {
  return ReceiptRepository();
});

class ReceiptFormNotifier extends Notifier<ReceiptFormState> {
  @override
  ReceiptFormState build() {
    return ReceiptFormState.initial();
  }

  void toggleCashSale(bool isCash) {
    state = state.copyWith(
      isCashSale: isCash,
    );
  }

  void updateCustomerField({
    String? name,
    String? phone,
    String? area,
    String? address,
    int? salespersonId,
    bool clearSalesperson = false,
  }) {
    state = state.copyWith(
      customer: state.customer.copyWith(
        name: name,
        phone: phone,
        area: area,
        address: address,
        salespersonId: salespersonId,
        clearSalesperson: clearSalesperson,
      ),
    );
  }

  void setSaleDate(int month, int year) {
    state = state.copyWith(
      saleMonth: month,
      saleYear: year,
    );
    _recalculateSchedule();
  }

  String? addToCart({
    required int inventoryItemId,
    required String name,
    required int quantity,
    required double price,
    required int maxStock,
  }) {
    final currentCart = List<CartItem>.from(state.cart);
    final existingIndex = currentCart.indexWhere((item) => item.inventoryItemId == inventoryItemId);

    final existingQty = existingIndex >= 0 ? currentCart[existingIndex].quantity : 0;
    final newTotalQty = existingQty + quantity;

    if (newTotalQty > maxStock) {
      return 'الكمية المطلوبة أكبر من المتاح. المتاح: $maxStock';
    }

    if (existingIndex >= 0) {
      currentCart[existingIndex] = currentCart[existingIndex].copyWith(
        quantity: newTotalQty,
        price: price,
      );
    } else {
      currentCart.add(CartItem(
        inventoryItemId: inventoryItemId,
        name: name,
        quantity: quantity,
        price: price,
      ));
    }

    state = state.copyWith(cart: currentCart);
    return null; // Success
  }

  void removeFromCart(int index) {
    final currentCart = List<CartItem>.from(state.cart);
    if (index >= 0 && index < currentCart.length) {
      currentCart.removeAt(index);
      state = state.copyWith(cart: currentCart);
    }
  }

  void updateDownPayment(double amount) {
    state = state.copyWith(downPayment: amount);
  }

  void updateInstallmentGroup(int index, {double? amount, int? count}) {
    final currentGroups = List<InstallmentGroup>.from(state.groups);
    if (index >= 0 && index < currentGroups.length) {
      currentGroups[index] = currentGroups[index].copyWith(
        amount: amount,
        count: count,
      );
      state = state.copyWith(groups: currentGroups);
      _recalculateSchedule();
    }
  }

  void _recalculateSchedule() {
    final newSchedule = <InstallmentScheduleItem>[];
    int currentMonth = state.saleMonth + 1;
    int currentYear = state.saleYear;

    if (currentMonth > 12) {
      currentMonth = 1;
      currentYear++;
    }

    for (var group in state.groups) {
      final count = group.count ?? 0;
      final amount = group.amount ?? 0.0;

      if (count > 0 && amount > 0) {
        for (int i = 0; i < count; i++) {
          newSchedule.add(InstallmentScheduleItem(
            month: currentMonth,
            year: currentYear,
            amount: amount,
          ));

          currentMonth++;
          if (currentMonth > 12) {
            currentMonth = 1;
            currentYear++;
          }
        }
      }
    }

    state = state.copyWith(schedule: newSchedule);
  }

  Future<String?> submitForm() async {
    if (state.cart.isEmpty) {
      return 'لا توجد بضاعة في الفاتورة!';
    }

    if (!state.isValidTotal) {
      return 'إجمالي الفاتورة لا يتطابق مع المقدم + الأقساط.';
    }

    try {
      final repo = ref.read(receiptRepositoryProvider);
      await repo.saveReceipt(state);
      return null; // Success
    } catch (e) {
      return 'حدث خطأ أثناء الحفظ: $e';
    }
  }
}

final receiptFormProvider = NotifierProvider<ReceiptFormNotifier, ReceiptFormState>(() {
  return ReceiptFormNotifier();
});
