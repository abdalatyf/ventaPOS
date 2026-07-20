class InventoryItemModel {
  final int id;
  final int branchId;
  final String name;
  final int currentStock;
  final int currentPrice;
  final int currentCommission;
  final int startMonth;
  final int startYear;
  final int isDeleted;

  const InventoryItemModel({
    required this.id,
    required this.branchId,
    required this.name,
    this.currentStock = 0,
    this.currentPrice = 0,
    this.currentCommission = 0,
    required this.startMonth,
    required this.startYear,
    this.isDeleted = 0,
  });

  factory InventoryItemModel.fromJson(Map<String, dynamic> json) => InventoryItemModel(
        id: json['id'] as int? ?? 0,
        branchId: json['branch_id'] as int? ?? 0,
        name: json['name'] as String? ?? '',
        currentStock: json['current_stock'] as int? ?? 0,
        currentPrice: json['current_price'] as int? ?? 0,
        currentCommission: json['current_commission'] as int? ?? 0,
        startMonth: json['start_month'] as int? ?? 0,
        startYear: json['start_year'] as int? ?? 0,
        isDeleted: json['is_deleted'] as int? ?? 0,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'branch_id': branchId,
        'name': name,
        'current_stock': currentStock,
        'current_price': currentPrice,
        'current_commission': currentCommission,
        'start_month': startMonth,
        'start_year': startYear,
        'is_deleted': isDeleted,
      };

  InventoryItemModel copyWith({
    int? id,
    int? branchId,
    String? name,
    int? currentStock,
    int? currentPrice,
    int? currentCommission,
    int? startMonth,
    int? startYear,
    int? isDeleted,
  }) {
    return InventoryItemModel(
      id: id ?? this.id,
      branchId: branchId ?? this.branchId,
      name: name ?? this.name,
      currentStock: currentStock ?? this.currentStock,
      currentPrice: currentPrice ?? this.currentPrice,
      currentCommission: currentCommission ?? this.currentCommission,
      startMonth: startMonth ?? this.startMonth,
      startYear: startYear ?? this.startYear,
      isDeleted: isDeleted ?? this.isDeleted,
    );
  }
}
