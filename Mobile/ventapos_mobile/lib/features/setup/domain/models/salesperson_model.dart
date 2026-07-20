class SalespersonModel {
  final int id;
  final int branchId;
  final String name;

  const SalespersonModel({
    required this.id,
    required this.branchId,
    required this.name,
  });

  factory SalespersonModel.fromJson(Map<String, dynamic> json) => SalespersonModel(
        id: json['id'] as int? ?? 0,
        branchId: json['branch_id'] as int? ?? 0,
        name: json['name'] as String? ?? '',
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'branch_id': branchId,
        'name': name,
      };

  SalespersonModel copyWith({
    int? id,
    int? branchId,
    String? name,
  }) {
    return SalespersonModel(
      id: id ?? this.id,
      branchId: branchId ?? this.branchId,
      name: name ?? this.name,
    );
  }
}
