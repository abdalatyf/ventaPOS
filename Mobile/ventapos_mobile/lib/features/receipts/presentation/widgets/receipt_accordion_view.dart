import 'package:flutter/material.dart';
import '../../domain/models/receipt_model.dart';

class ReceiptAccordionView extends StatefulWidget {
  final List<ReceiptModel> receipts;

  const ReceiptAccordionView({Key? key, required this.receipts}) : super(key: key);

  @override
  State<ReceiptAccordionView> createState() => _ReceiptAccordionViewState();
}

class _ReceiptAccordionViewState extends State<ReceiptAccordionView> {
  // Store expanded state
  late List<bool> _isExpanded;

  @override
  void initState() {
    super.initState();
    _isExpanded = List.generate(widget.receipts.length, (index) => false);
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      child: Padding(
        padding: const EdgeInsets.all(8.0),
        child: ExpansionPanelList(
          elevation: 1,
          expandedHeaderPadding: const EdgeInsets.all(0),
          expansionCallback: (int index, bool isExpanded) {
            setState(() {
              // Flutter 3.10+ passes the new state (isExpanded is whether it is currently expanded)
              // We need to toggle it. Wait, the callback passes the current state before the click.
              // Let's just invert it.
              _isExpanded[index] = !_isExpanded[index];
            });
          },
          children: widget.receipts.asMap().entries.map((entry) {
            final index = entry.key;
            final receipt = entry.value;

            return ExpansionPanel(
              isExpanded: _isExpanded[index],
              canTapOnHeader: true,
              headerBuilder: (BuildContext context, bool isExpanded) {
                return ListTile(
                  title: Text(receipt.customerName, style: const TextStyle(fontWeight: FontWeight.bold)),
                  subtitle: Text('#${receipt.receiptNumber} • ${receipt.isExported ? 'مرحلة' : 'مسودة'}', style: const TextStyle(fontSize: 12)),
                  trailing: Text(
                    '${receipt.totalAmount} ج.م',
                    style: TextStyle(
                      color: receipt.isExported ? Colors.green : Colors.red,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                );
              },
              body: Container(
                color: Colors.grey.shade50,
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildRow('المنتجات:', receipt.productsText, isBold: true),
                    const SizedBox(height: 8),
                    _buildRow('نظام الدفع:', receipt.isCashSale ? 'كاش' : 'قسط (${receipt.installmentSystem})'),
                    const SizedBox(height: 8),
                    _buildRow('المقدم:', '${receipt.downPayment} ج.م'),
                    const SizedBox(height: 8),
                    _buildRow('المنطقة:', '${receipt.area} - ${receipt.address}'),
                    const SizedBox(height: 8),
                    _buildRow('الهاتف:', receipt.phoneNumber),
                    const SizedBox(height: 8),
                    _buildRow('التاريخ:', receipt.createdAtLocal),
                  ],
                ),
              ),
            );
          }).toList(),
        ),
      ),
    );
  }

  Widget _buildRow(String label, String value, {bool isBold = false}) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: 80,
          child: Text(label, style: const TextStyle(fontSize: 13, color: Colors.black54)),
        ),
        Expanded(
          child: Text(
            value,
            style: TextStyle(
              fontSize: 13,
              fontWeight: isBold ? FontWeight.bold : FontWeight.normal,
              color: Colors.black87,
            ),
          ),
        ),
      ],
    );
  }
}
