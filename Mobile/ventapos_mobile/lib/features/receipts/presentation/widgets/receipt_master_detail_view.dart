import 'package:flutter/material.dart';
import '../../domain/models/receipt_model.dart';

class ReceiptMasterDetailView extends StatelessWidget {
  final List<ReceiptModel> receipts;

  const ReceiptMasterDetailView({Key? key, required this.receipts}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      padding: const EdgeInsets.all(12),
      itemCount: receipts.length,
      itemBuilder: (context, index) {
        final receipt = receipts[index];
        return InkWell(
          onTap: () => _showDetailModal(context, receipt),
          child: Container(
            margin: const EdgeInsets.only(bottom: 10),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(10),
              boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.04), blurRadius: 5, offset: const Offset(0, 2))],
              border: Border(right: BorderSide(color: receipt.isExported ? Colors.green : Colors.orange, width: 4)),
            ),
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(receipt.customerName, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                    const SizedBox(height: 4),
                    Text('#${receipt.receiptNumber} • ${receipt.createdAtLocal} • ${receipt.isExported ? '✅' : '⏳'}',
                        style: const TextStyle(fontSize: 11, color: Colors.grey)),
                  ],
                ),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text('${receipt.totalAmount} ج.م',
                        style: TextStyle(fontWeight: FontWeight.bold, color: Colors.blue.shade700)),
                    const SizedBox(height: 4),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(border: Border.all(color: Colors.grey.shade300), borderRadius: BorderRadius.circular(4)),
                      child: Text(receipt.isCashSale ? 'كاش' : 'قسط ${receipt.installmentSystem}',
                          style: const TextStyle(fontSize: 9, color: Colors.black54)),
                    )
                  ],
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  void _showDetailModal(BuildContext context, ReceiptModel receipt) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) {
        return Container(
          height: MediaQuery.of(context).size.height * 0.85,
          decoration: const BoxDecoration(
            color: Color(0xFFF4F6F9),
            borderRadius: BorderRadius.only(topLeft: Radius.circular(20), topRight: Radius.circular(20)),
          ),
          child: Column(
            children: [
              // Header
              Container(
                padding: const EdgeInsets.all(16),
                decoration: const BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.only(topLeft: Radius.circular(20), topRight: Radius.circular(20)),
                  border: Border(bottom: BorderSide(color: Colors.black12)),
                ),
                child: Row(
                  children: [
                    IconButton(icon: const Icon(Icons.arrow_back), onPressed: () => Navigator.pop(context)),
                    Text('تفاصيل الفاتورة #${receipt.receiptNumber}', style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                  ],
                ),
              ),
              
              // Body
              Expanded(
                child: SingleChildScrollView(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    children: [
                      // Customer Info
                      Text(receipt.customerName, style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Colors.blue)),
                      const SizedBox(height: 4),
                      Text('${receipt.area}، ${receipt.address}', style: const TextStyle(fontSize: 13, color: Colors.grey)),
                      Text(receipt.phoneNumber, style: const TextStyle(fontSize: 13, color: Colors.grey), textDirection: TextDirection.ltr),
                      const SizedBox(height: 24),

                      // Totals
                      Row(
                        children: [
                          Expanded(
                            child: _buildBoxInfo('الإجمالي', '${receipt.totalAmount}', Colors.red),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: _buildBoxInfo('المدفوع (المقدم)', '${receipt.downPayment}', Colors.green),
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),

                      // Metadata
                      Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: Colors.black12)),
                        child: Column(
                          children: [
                            _buildMetaRow('طريقة البيع', receipt.isCashSale ? 'كاش' : 'بيع قسط'),
                            _buildMetaRow('نظام التقسيط', receipt.installmentSystem ?? '-'),
                            _buildMetaRow('تاريخ البيع', receipt.createdAtLocal),
                            _buildMetaRow('المزامنة', receipt.isExported ? 'تم الترحيل ✅' : 'مسودة محلية ⏳', isLast: true),
                          ],
                        ),
                      ),
                      const SizedBox(height: 16),

                      // Products
                      const Align(
                        alignment: Alignment.centerRight,
                        child: Text('المنتجات المباعة', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                      ),
                      const SizedBox(height: 8),
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: Colors.black12)),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: receipt.productsText.split('-').map((p) {
                            return Padding(
                              padding: const EdgeInsets.only(bottom: 8.0),
                              child: Text('• ${p.trim()}', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
                            );
                          }).toList(),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildBoxInfo(String title, String value, Color color) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: Colors.black12)),
      child: Column(
        children: [
          Text(title, style: const TextStyle(fontSize: 11, color: Colors.grey)),
          const SizedBox(height: 4),
          Text(value, style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: color)),
        ],
      ),
    );
  }

  Widget _buildMetaRow(String label, String value, {bool isLast = false}) {
    return Padding(
      padding: EdgeInsets.only(bottom: isLast ? 0 : 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: Colors.grey, fontSize: 13)),
          Text(value, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
        ],
      ),
    );
  }
}
