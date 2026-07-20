class ReceiptModel {
  final int id;
  final int receiptNumber;
  final String customerName;
  final String phoneNumber;
  final String address;
  final String area;
  final double totalAmount;
  final double downPayment;
  final String? installmentSystem;
  final bool isCashSale;
  final String productsText; // e.g. "ثلاجة (1), غسالة (1)"
  final bool isExported;
  final String createdAtLocal;

  ReceiptModel({
    required this.id,
    required this.receiptNumber,
    required this.customerName,
    required this.phoneNumber,
    required this.address,
    required this.area,
    required this.totalAmount,
    required this.downPayment,
    this.installmentSystem,
    required this.isCashSale,
    required this.productsText,
    required this.isExported,
    required this.createdAtLocal,
  });
}
