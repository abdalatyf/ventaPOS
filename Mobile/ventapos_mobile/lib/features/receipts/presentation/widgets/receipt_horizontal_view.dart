import 'package:flutter/material.dart';
import '../../domain/models/receipt_model.dart';

class ReceiptHorizontalView extends StatelessWidget {
  final List<ReceiptModel> receipts;

  const ReceiptHorizontalView({Key? key, required this.receipts}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(8.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: Colors.blue.shade50,
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Text(
              'اسحب الجدول يميناً ويساراً لرؤية باقي الأعمدة',
              style: TextStyle(fontSize: 12, color: Colors.blue),
              textAlign: TextAlign.center,
            ),
          ),
          const SizedBox(height: 8),
          Expanded(
            child: Card(
              elevation: 2,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              child: SingleChildScrollView(
                scrollDirection: Axis.vertical,
                child: SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: DataTable(
                    headingRowColor: MaterialStateProperty.all(Colors.grey.shade100),
                    columns: const [
                      DataColumn(label: Text('رقم الفاتورة')),
                      DataColumn(label: Text('العميل')),
                      DataColumn(label: Text('الإجمالي')),
                      DataColumn(label: Text('المقدم')),
                      DataColumn(label: Text('طريقة الدفع')),
                      DataColumn(label: Text('المنتجات')),
                      DataColumn(label: Text('الهاتف')),
                      DataColumn(label: Text('المنطقة')),
                      DataColumn(label: Text('التاريخ')),
                      DataColumn(label: Text('المزامنة')),
                    ],
                    rows: receipts.map((receipt) {
                      return DataRow(
                        cells: [
                          DataCell(Text('#${receipt.receiptNumber}', style: const TextStyle(fontWeight: FontWeight.bold))),
                          DataCell(Text(receipt.customerName, style: const TextStyle(color: Colors.blue))),
                          DataCell(Text('${receipt.totalAmount} ج.م', style: const TextStyle(color: Colors.red, fontWeight: FontWeight.bold))),
                          DataCell(Text('${receipt.downPayment} ج.م')),
                          DataCell(Text(receipt.isCashSale ? 'كاش' : 'قسط')),
                          DataCell(Text(receipt.productsText)),
                          DataCell(Text(receipt.phoneNumber)),
                          DataCell(Text(receipt.area)),
                          DataCell(Text(receipt.createdAtLocal)),
                          DataCell(
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                              decoration: BoxDecoration(
                                color: receipt.isExported ? Colors.green.shade100 : Colors.orange.shade100,
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: Text(
                                receipt.isExported ? 'مرحلة' : 'مسودة',
                                style: TextStyle(fontSize: 11, color: receipt.isExported ? Colors.green.shade800 : Colors.orange.shade800),
                              ),
                            ),
                          ),
                        ],
                      );
                    }).toList(),
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
