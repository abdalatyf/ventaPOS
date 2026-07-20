import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../domain/models/receipt_model.dart';

enum ReceiptViewMode {
  masterDetail,
  card,
  horizontal,
  accordion,
}

class ReceiptViewModeNotifier extends Notifier<ReceiptViewMode> {
  @override
  ReceiptViewMode build() {
    return ReceiptViewMode.masterDetail;
  }

  void setMode(ReceiptViewMode mode) {
    state = mode;
  }
}

final receiptViewModeProvider = NotifierProvider<ReceiptViewModeNotifier, ReceiptViewMode>(() {
  return ReceiptViewModeNotifier();
});

// Provides dummy data for the UI
final dummyReceiptsProvider = Provider<List<ReceiptModel>>((ref) {
  return [
    ReceiptModel(
      id: 1,
      receiptNumber: 1042,
      customerName: "محمود عبد الله",
      phoneNumber: "01023456789",
      address: "شارع فيصل الرئيسي، برج الصفا",
      area: "فيصل",
      totalAmount: 15400.0,
      downPayment: 5000.0,
      installmentSystem: "12 شهر",
      isCashSale: false,
      productsText: "ثلاجة توشيبا 14 قدم (1) - غسالة زانوسي 7 كيلو (1)",
      isExported: false, // Draft
      createdAtLocal: "14/07/2026",
    ),
    ReceiptModel(
      id: 2,
      receiptNumber: 1043,
      customerName: "سوبر ماركت الهدى",
      phoneNumber: "01198765432",
      address: "متفرع من شارع العشرين",
      area: "بولاق الدكرور",
      totalAmount: 4200.0,
      downPayment: 4200.0,
      installmentSystem: null,
      isCashSale: true,
      productsText: "كرتونة شيبسي عائلي (5) - كرتونة بيبسي جيب (10)",
      isExported: true, // Synced
      createdAtLocal: "13/07/2026",
    ),
  ];
});
