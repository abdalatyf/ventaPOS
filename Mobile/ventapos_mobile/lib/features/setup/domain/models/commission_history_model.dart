class CommissionHistoryModel {
  final int? id;
  final int inventoryItemId;
  final int commissionAmount;
  final int startMonth;
  final int startYear;
  final String createdAtLocal;

  const CommissionHistoryModel({
    this.id,
    required this.inventoryItemId,
    required this.commissionAmount,
    required this.startMonth,
    required this.startYear,
    required this.createdAtLocal,
  });

  factory CommissionHistoryModel.fromJson(Map<String, dynamic> json) => CommissionHistoryModel(
        id: json['id'] as int?,
        inventoryItemId: json['inventory_item_id'] as int? ?? 0,
        commissionAmount: json['commission_amount'] as int? ?? 0,
        startMonth: json['start_month'] as int? ?? 0,
        startYear: json['start_year'] as int? ?? 0,
        createdAtLocal: json['created_at_local'] as String? ?? '',
      );

  Map<String, dynamic> toJson() => {
        if (id != null) 'id': id,
        'inventory_item_id': inventoryItemId,
        'commission_amount': commissionAmount,
        'start_month': startMonth,
        'start_year': startYear,
        'created_at_local': createdAtLocal,
      };
}
