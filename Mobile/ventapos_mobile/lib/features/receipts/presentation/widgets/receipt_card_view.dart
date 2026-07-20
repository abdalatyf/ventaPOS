import 'package:flutter/material.dart';
import '../../domain/models/receipt_model.dart';

class ReceiptCardView extends StatelessWidget {
  final List<ReceiptModel> receipts;

  const ReceiptCardView({Key? key, required this.receipts}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      padding: const EdgeInsets.all(12),
      itemCount: receipts.length,
      itemBuilder: (context, index) {
        final receipt = receipts[index];
        return Card(
          elevation: 2,
          margin: const EdgeInsets.only(bottom: 12),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Header
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Expanded(
                      child: Text(
                        receipt.customerName,
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Colors.blue),
                      ),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: receipt.isExported ? Colors.green.shade100 : Colors.orange.shade100,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        receipt.isExported ? 'مرحلة ✅' : 'مسودة ⏳',
                        style: TextStyle(
                          fontSize: 10,
                          color: receipt.isExported ? Colors.green.shade800 : Colors.orange.shade800,
                        ),
                      ),
                    ),
                  ],
                ),
                Text(
                  'فاتورة #${receipt.receiptNumber} • ${receipt.createdAtLocal}',
                  style: const TextStyle(fontSize: 12, color: Colors.grey),
                ),
                const SizedBox(height: 12),
                
                // Money Info
                _buildDataRow('الإجمالي:', '${receipt.totalAmount} ج.م', isBold: true, valueColor: Colors.red),
                _buildDataRow('المقدم / الدفعة:', '${receipt.downPayment} ج.م'),
                _buildDataRow('نظام الدفع:', receipt.isCashSale ? 'كاش' : 'قسط (${receipt.installmentSystem})'),
                
                const Divider(),
                
                // Address Info
                _buildDataRow('الهاتف:', receipt.phoneNumber),
                _buildDataRow('المنطقة:', '${receipt.area} - ${receipt.address}'),
                
                const Divider(),
                
                // Products
                const Text('المنتجات:', style: TextStyle(fontSize: 12, color: Colors.grey)),
                const SizedBox(height: 4),
                Wrap(
                  spacing: 6,
                  runSpacing: 6,
                  children: receipt.productsText.split('-').map((product) {
                    return Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: Colors.grey.shade200,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        product.trim(),
                        style: const TextStyle(fontSize: 11),
                      ),
                    );
                  }).toList(),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildDataRow(String label, String value, {bool isBold = false, Color? valueColor}) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(fontSize: 13, color: Colors.black87)),
          Expanded(
            child: Text(
              value,
              textAlign: TextAlign.left,
              style: TextStyle(
                fontSize: 13,
                fontWeight: isBold ? FontWeight.bold : FontWeight.normal,
                color: valueColor ?? Colors.black87,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
