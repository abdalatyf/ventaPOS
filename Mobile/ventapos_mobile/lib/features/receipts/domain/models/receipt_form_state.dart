class CustomerData {
  final String name;
  final String phone;
  final String area;
  final String address;
  final int? salespersonId;

  CustomerData({
    this.name = '',
    this.phone = '',
    this.area = '',
    this.address = '',
    this.salespersonId,
  });

  CustomerData copyWith({
    String? name,
    String? phone,
    String? area,
    String? address,
    int? salespersonId,
    bool clearSalesperson = false,
  }) {
    return CustomerData(
      name: name ?? this.name,
      phone: phone ?? this.phone,
      area: area ?? this.area,
      address: address ?? this.address,
      salespersonId: clearSalesperson ? null : (salespersonId ?? this.salespersonId),
    );
  }
}

class CartItem {
  final int inventoryItemId;
  final String name;
  final int quantity;
  final double price;

  CartItem({
    required this.inventoryItemId,
    required this.name,
    required this.quantity,
    required this.price,
  });

  double get total => quantity * price;

  CartItem copyWith({
    int? inventoryItemId,
    String? name,
    int? quantity,
    double? price,
  }) {
    return CartItem(
      inventoryItemId: inventoryItemId ?? this.inventoryItemId,
      name: name ?? this.name,
      quantity: quantity ?? this.quantity,
      price: price ?? this.price,
    );
  }
}

class InstallmentGroup {
  final double? amount;
  final int? count;

  InstallmentGroup({this.amount, this.count});

  InstallmentGroup copyWith({
    double? amount,
    int? count,
  }) {
    return InstallmentGroup(
      amount: amount ?? this.amount,
      count: count ?? this.count,
    );
  }
}

class InstallmentScheduleItem {
  final int month;
  final int year;
  final double amount;

  InstallmentScheduleItem({
    required this.month,
    required this.year,
    required this.amount,
  });
}

class ReceiptFormState {
  final bool isCashSale;
  final CustomerData customer;
  final int saleMonth;
  final int saleYear;
  final List<CartItem> cart;
  final double downPayment;
  final List<InstallmentGroup> groups;
  final List<InstallmentScheduleItem> schedule;

  ReceiptFormState({
    this.isCashSale = false,
    required this.customer,
    required this.saleMonth,
    required this.saleYear,
    this.cart = const [],
    this.downPayment = 0.0,
    required this.groups,
    this.schedule = const [],
  });

  factory ReceiptFormState.initial() {
    final now = DateTime.now();
    return ReceiptFormState(
      customer: CustomerData(),
      saleMonth: now.month,
      saleYear: now.year,
      groups: [
        InstallmentGroup(),
        InstallmentGroup(),
        InstallmentGroup(),
      ],
    );
  }

  double get totalCartValue {
    return cart.fold(0.0, (sum, item) => sum + item.total);
  }

  double get totalInstallments {
    return schedule.fold(0.0, (sum, item) => sum + item.amount);
  }

  double get totalPaidAndInstallments {
    return downPayment + totalInstallments;
  }

  bool get isValidTotal {
    if (isCashSale) return true; // Handled implicitly
    // Allow minor floating point diff
    return (totalCartValue - totalPaidAndInstallments).abs() < 0.01;
  }

  ReceiptFormState copyWith({
    bool? isCashSale,
    CustomerData? customer,
    int? saleMonth,
    int? saleYear,
    List<CartItem>? cart,
    double? downPayment,
    List<InstallmentGroup>? groups,
    List<InstallmentScheduleItem>? schedule,
  }) {
    return ReceiptFormState(
      isCashSale: isCashSale ?? this.isCashSale,
      customer: customer ?? this.customer,
      saleMonth: saleMonth ?? this.saleMonth,
      saleYear: saleYear ?? this.saleYear,
      cart: cart ?? this.cart,
      downPayment: downPayment ?? this.downPayment,
      groups: groups ?? this.groups,
      schedule: schedule ?? this.schedule,
    );
  }
}
