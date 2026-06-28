import 'package:flutter/material.dart';
import '../db/database_helper.dart';
import 'package:flareline_uikit/components/card/common_card.dart';
import 'package:flareline_uikit/core/theme/flareline_colors.dart';


class ProductLedgerScreen extends StatefulWidget {
  const ProductLedgerScreen({super.key});

  @override
  State<ProductLedgerScreen> createState() => _ProductLedgerScreenState();
}

class _ProductLedgerScreenState extends State<ProductLedgerScreen> with SingleTickerProviderStateMixin {
  int? _selectedProductId;
  int? _fromMonth;
  int? _fromYear;
  int? _toMonth;
  int? _toYear;

  List<Map<String, dynamic>> _products = [];
  List<Map<String, dynamic>> _monthlySummary = [];
  List<Map<String, dynamic>> _movements = [];
  
  Map<String, dynamic> _grandTotals = {
    'cash_profit': 0.0,
    'inst_profit': 0.0,
    'adj_profit': 0.0,
    'net_profit': 0.0,
    'cash_qty': 0,
    'inst_qty': 0
  };

  bool _isLoading = false;
  TabController? _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _loadProducts();
  }

  @override
  void dispose() {
    _tabController?.dispose();
    super.dispose();
  }

  Future<void> _loadProducts() async {
    setState(() => _isLoading = true);
    try {
      final db = await DatabaseHelper.instance.database;
      final data = await db.query('inventory', orderBy: 'name ASC');
      setState(() {
        _products = data;
        if (_products.isNotEmpty) {
          _selectedProductId = _products.first['id'] as int;
          // Trigger initial load with defaults from selected product
          final p = _products.first;
          _fromMonth = p['initial_month'] as int? ?? 1;
          _fromYear = p['initial_year'] as int? ?? 2026;
          _toMonth = DateTime.now().month;
          _toYear = DateTime.now().year;
        }
      });
      if (_selectedProductId != null) {
        await _filterLedger();
      }
    } catch (e) {
      debugPrint('Error loading products: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _filterLedger() async {
    if (_selectedProductId == null) return;
    setState(() => _isLoading = true);

    try {
      final db = await DatabaseHelper.instance.database;

      // 1. Fetch product info
      final prodQuery = await db.query('inventory', where: 'id = ?', whereArgs: [_selectedProductId]);
      if (prodQuery.isEmpty) {
        setState(() => _isLoading = false);
        return;
      }
      final product = prodQuery.first;
      final int initialQty = product['initial_quantity'] as int? ?? 0;
      final int initialPrice = product['initial_purchase_price'] as int? ?? 0;
      final int initialComm = product['initial_commission_amount'] as int? ?? 0;
      final int initialMonth = product['initial_month'] as int? ?? 1;
      final int initialYear = product['initial_year'] as int? ?? 2026;

      // 2. Align filter ranges
      int startY = _fromYear ?? initialYear;
      int startM = _fromMonth ?? initialMonth;
      int endY = _toYear ?? DateTime.now().year;
      int endM = _toMonth ?? DateTime.now().month;

      _fromYear ??= startY;
      _fromMonth ??= startM;
      _toYear ??= endY;
      _toMonth ??= endM;

      // --- Helper 1: get_stock_at_date(month, year) ---
      Future<int> getStockAtDate(int m, int y) async {
        if (y < initialYear || (y == initialYear && m < initialMonth)) {
          return 0;
        }

        // total_purchased
        final purchasedQuery = await db.rawQuery('''
          SELECT SUM(pi.quantity) as total
          FROM purchase_invoice_items pi
          JOIN purchase_invoices p ON pi.invoice_id = p.id
          WHERE pi.inventory_item_id = ?
            AND p.invoice_type = 'PURCHASE'
            AND (p.invoice_year < ? OR (p.invoice_year = ? AND p.invoice_month <= ?))
        ''', [_selectedProductId, y, y, m]);
        int totalPurchased = (purchasedQuery.first['total'] as num?)?.toInt() ?? 0;

        // total_returned
        final returnedQuery = await db.rawQuery('''
          SELECT SUM(pi.quantity) as total
          FROM purchase_invoice_items pi
          JOIN purchase_invoices p ON pi.invoice_id = p.id
          WHERE pi.inventory_item_id = ?
            AND p.invoice_type = 'RETURN'
            AND (p.invoice_year < ? OR (p.invoice_year = ? AND p.invoice_month <= ?))
        ''', [_selectedProductId, y, y, m]);
        int totalReturned = (returnedQuery.first['total'] as num?)?.toInt() ?? 0;

        // total_sold
        final soldQuery = await db.rawQuery('''
          SELECT SUM(ri.quantity) as total
          FROM receipt_items ri
          JOIN receipts r ON ri.receipt_id = r.id
          WHERE ri.inventory_item_id = ?
            AND (r.sale_year < ? OR (r.sale_year = ? AND r.sale_month <= ?))
        ''', [_selectedProductId, y, y, m]);
        int totalSold = (soldQuery.first['total'] as num?)?.toInt() ?? 0;

        int finalStock = (initialQty + totalPurchased) - (totalSold + totalReturned);
        return finalStock < 0 ? 0 : finalStock;
      }

      // --- Helper 2: get_price_at_date(month, year) ---
      Future<double> getPriceAtDate(int m, int y) async {
        final latestPurchase = await db.rawQuery('''
          SELECT pi.purchase_price
          FROM purchase_invoice_items pi
          JOIN purchase_invoices p ON pi.invoice_id = p.id
          WHERE pi.inventory_item_id = ?
            AND p.invoice_type = 'PURCHASE'
            AND p.invoice_year <= ?
            AND (p.invoice_year < ? OR p.invoice_month <= ?)
          ORDER BY p.invoice_year DESC, p.invoice_month DESC, p.id DESC
          LIMIT 1
        ''', [_selectedProductId, y, y, m]);

        if (latestPurchase.isNotEmpty) {
          return (latestPurchase.first['purchase_price'] as num).toDouble();
        }
        return initialPrice.toDouble();
      }

      // --- Helper 3: get_commission_at_date(month, year) ---
      Future<double> getCommissionAtDate(int m, int y) async {
        final latestComm = await db.rawQuery('''
          SELECT commission_amount
          FROM commission_history
          WHERE item_id = ?
            AND activation_year <= ?
            AND (activation_year < ? OR activation_month <= ?)
          ORDER BY activation_year DESC, activation_month DESC, id DESC
          LIMIT 1
        ''', [_selectedProductId, y, y, m]);

        if (latestComm.isNotEmpty) {
          return (latestComm.first['commission_amount'] as num).toDouble();
        }
        return initialComm.toDouble();
      }

      // --- Calculate Monthly Summaries ---
      List<Map<String, dynamic>> summaryList = [];
      double grandCashProfit = 0.0;
      double grandInstProfit = 0.0;
      double grandAdjProfit = 0.0;
      double grandNetProfit = 0.0;
      int grandCashQty = 0;
      int grandInstQty = 0;

      int tempY = startY;
      int tempM = startM;

      while (tempY < endY || (tempY == endY && tempM <= endM)) {
        int prevM = tempM == 1 ? 12 : tempM - 1;
        int prevY = tempM == 1 ? tempY - 1 : tempY;

        int opening = await getStockAtDate(prevM, prevY);
        if (tempY == initialYear && tempM == initialMonth) {
          opening += initialQty;
        }

        int closing = await getStockAtDate(tempM, tempY);
        double costUnit = await getPriceAtDate(tempM, tempY);
        double commUnit = await getCommissionAtDate(tempM, tempY);

        // Purchases in this month
        final pQuery = await db.rawQuery('''
          SELECT SUM(pi.quantity) as s
          FROM purchase_invoice_items pi
          JOIN purchase_invoices p ON pi.invoice_id = p.id
          WHERE pi.inventory_item_id = ?
            AND p.invoice_month = ?
            AND p.invoice_year = ?
            AND p.invoice_type = 'PURCHASE'
        ''', [_selectedProductId, tempM, tempY]);
        int purchases = (pQuery.first['s'] as num?)?.toInt() ?? 0;

        // Returns in this month
        final rQuery = await db.rawQuery('''
          SELECT SUM(pi.quantity) as s
          FROM purchase_invoice_items pi
          JOIN purchase_invoices p ON pi.invoice_id = p.id
          WHERE pi.inventory_item_id = ?
            AND p.invoice_month = ?
            AND p.invoice_year = ?
            AND p.invoice_type = 'RETURN'
        ''', [_selectedProductId, tempM, tempY]);
        int returns = (rQuery.first['s'] as num?)?.toInt() ?? 0;

        int netPurchases = purchases - returns;

        // Adjustments are 0
        int surplus = 0;
        int deficit = 0;

        // Cash sales in this month
        final cashQuery = await db.rawQuery('''
          SELECT SUM(ri.quantity) as qty, SUM(ri.quantity * ri.unit_price) as rev
          FROM receipt_items ri
          JOIN receipts r ON ri.receipt_id = r.id
          WHERE ri.inventory_item_id = ?
            AND r.sale_year = ?
            AND r.sale_month = ?
            AND r.is_cash_sale = 1
        ''', [_selectedProductId, tempY, tempM]);
        int cQty = (cashQuery.first['qty'] as num?)?.toInt() ?? 0;
        double cRev = (cashQuery.first['rev'] as num?)?.toDouble() ?? 0.0;
        double cCost = cQty * costUnit;
        double cProfit = cRev - cCost;

        // Installment sales in this month
        final instQuery = await db.rawQuery('''
          SELECT ri.quantity, ri.unit_price, r.total_amount, r.down_payment
          FROM receipt_items ri
          JOIN receipts r ON ri.receipt_id = r.id
          WHERE ri.inventory_item_id = ?
            AND r.sale_year = ?
            AND r.sale_month = ?
            AND r.is_cash_sale = 0
        ''', [_selectedProductId, tempY, tempM]);

        int iQty = 0;
        double iRev = 0.0;
        double iCollComm = 0.0;

        for (var row in instQuery) {
          int qty = (row['quantity'] as num?)?.toInt() ?? 0;
          double price = (row['unit_price'] as num?)?.toDouble() ?? 0.0;
          double totalAmt = (row['total_amount'] as num?)?.toDouble() ?? 0.0;
          double downP = (row['down_payment'] as num?)?.toDouble() ?? 0.0;

          iQty += qty;
          double lineRev = qty * price;
          iRev += lineRev;

          if (totalAmt > 0) {
            iCollComm += (lineRev * (totalAmt - downP) * 0.10) / totalAmt;
          }
        }

        double iProfit = iRev - (iQty * costUnit) - (iQty * commUnit) - iCollComm;
        double adjProfit = 0.0;
        double monthNetProfit = cProfit + iProfit + adjProfit;

        if (opening > 0 || netPurchases > 0 || (cQty + iQty) > 0 || surplus > 0 || deficit > 0 || closing > 0) {
          summaryList.add({
            'year': tempY,
            'month': tempM,
            'opening': opening,
            'purchases': netPurchases,
            'sales': cQty + iQty,
            'surplus': surplus,
            'deficit': deficit,
            'closing': closing,
            'cost_unit': costUnit,
            'total_val': closing * costUnit,
            'cash': {
              'qty': cQty,
              'avg_sell': cQty > 0 ? cRev / cQty : 0.0,
              'rev': cRev,
              'cost': cCost,
              'profit': cProfit,
              'profit_unit': cQty > 0 ? cProfit / cQty : 0.0,
            },
            'inst': {
              'qty': iQty,
              'avg_sell': iQty > 0 ? iRev / iQty : 0.0,
              'rev': iRev,
              'cost': iQty * costUnit,
              'sales_comm_unit': commUnit,
              'sales_comm': iQty * commUnit,
              'coll_comm': iCollComm,
              'profit': iProfit,
              'coll_comm_unit': iQty > 0 ? iCollComm / iQty : 0.0,
              'profit_unit': iQty > 0 ? iProfit / iQty : 0.0,
            },
            'adj_profit': adjProfit,
            'month_net_profit': monthNetProfit
          });

          grandCashProfit += cProfit;
          grandInstProfit += iProfit;
          grandAdjProfit += adjProfit;
          grandNetProfit += monthNetProfit;
          grandCashQty += cQty;
          grandInstQty += iQty;
        }

        tempM++;
        if (tempM > 12) {
          tempM = 1;
          tempY++;
        }
      }

      summaryList = summaryList.reversed.toList();

      // --- Calculate Movements Log ---
      int prevStartM = startM == 1 ? 12 : startM - 1;
      int prevStartY = startM == 1 ? startY - 1 : startY;
      int broughtForwardQty = await getStockAtDate(prevStartM, prevStartY);
      if (startY == initialYear && startM == initialMonth) {
        broughtForwardQty += initialQty;
      }

      List<Map<String, dynamic>> movementsList = [];
      movementsList.add({
        'year': startY,
        'month': startM,
        'id': 0,
        'label': 'رصيد مرحل (بداية الفترة)',
        'type': 'INITIAL',
        'in_qty': broughtForwardQty,
        'out_qty': 0,
        'ref': '-',
        'person': 'النظام'
      });

      // Sales
      final salesItemsQuery = await db.rawQuery('''
        SELECT ri.id, r.sale_year, r.sale_month, ri.quantity, r.receipt_number, r.customer_name
        FROM receipt_items ri
        JOIN receipts r ON ri.receipt_id = r.id
        WHERE ri.inventory_item_id = ?
      ''', [_selectedProductId]);

      for (var s in salesItemsQuery) {
        int y = (s['sale_year'] as num).toInt();
        int m = (s['sale_month'] as num).toInt();
        if ((y > startY || (y == startY && m >= startM)) && (y < endY || (y == endY && m <= endM))) {
          movementsList.add({
            'year': y,
            'month': m,
            'id': s['id'] as int,
            'label': 'فاتورة بيع',
            'type': 'SALE/OUT',
            'in_qty': 0,
            'out_qty': (s['quantity'] as num).toInt(),
            'ref': s['receipt_number']?.toString() ?? '-',
            'person': s['customer_name']?.toString() ?? '-'
          });
        }
      }

      // Purchases/Returns
      final purchaseItemsQuery = await db.rawQuery('''
        SELECT pi.id, p.invoice_year, p.invoice_month, pi.quantity, p.invoice_type, p.invoice_number, s.name as supplier_name
        FROM purchase_invoice_items pi
        JOIN purchase_invoices p ON pi.invoice_id = p.id
        LEFT JOIN suppliers s ON p.supplier_id = s.id
        WHERE pi.inventory_item_id = ?
      ''', [_selectedProductId]);

      for (var p in purchaseItemsQuery) {
        int y = (p['invoice_year'] as num).toInt();
        int m = (p['invoice_month'] as num).toInt();
        if ((y > startY || (y == startY && m >= startM)) && (y < endY || (y == endY && m <= endM))) {
          bool isIn = p['invoice_type'] == 'PURCHASE';
          movementsList.add({
            'year': y,
            'month': m,
            'id': p['id'] as int,
            'label': isIn ? 'شراء' : 'مرتجع مصنع',
            'type': isIn ? 'PURCHASE/IN' : 'RETURN/OUT',
            'in_qty': isIn ? (p['quantity'] as num).toInt() : 0,
            'out_qty': isIn ? 0 : (p['quantity'] as num).toInt(),
            'ref': p['invoice_number']?.toString() ?? '-',
            'person': p['supplier_name']?.toString() ?? 'غير محدد'
          });
        }
      }

      // Sort movements by year, month, id ASC
      movementsList.sort((a, b) {
        int cmpYear = (a['year'] as int).compareTo(b['year'] as int);
        if (cmpYear != 0) return cmpYear;
        int cmpMonth = (a['month'] as int).compareTo(b['month'] as int);
        if (cmpMonth != 0) return cmpMonth;
        return (a['id'] as int).compareTo(b['id'] as int);
      });

      // running balance
      int runningBalance = 0;
      for (var mov in movementsList) {
        runningBalance += ((mov['in_qty'] as int) - (mov['out_qty'] as int));
        mov['balance'] = runningBalance;
      }

      movementsList = movementsList.reversed.toList();

      setState(() {
        _monthlySummary = summaryList;
        _movements = movementsList;
        _grandTotals = {
          'cash_profit': grandCashProfit,
          'inst_profit': grandInstProfit,
          'adj_profit': grandAdjProfit,
          'net_profit': grandNetProfit,
          'cash_qty': grandCashQty,
          'inst_qty': grandInstQty
        };
      });
    } catch (e) {
      debugPrint('Error calculating ledger: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Widget _buildKpiCard(String title, String value, Color color, IconData icon) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: color.withOpacity(0.1),
          border: Border.all(color: color.withOpacity(0.3), width: 1),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: TextStyle(fontSize: 12, color: color, fontWeight: FontWeight.bold)),
                const SizedBox(height: 4),
                Text(value, style: TextStyle(fontSize: 16, color: FlarelineColors.darkBlackText, fontWeight: FontWeight.bold)),
              ],
            ),
            Icon(icon, color: color, size: 28),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    List<int> months = List.generate(12, (index) => index + 1);
    List<int> years = List.generate(10, (index) => 2020 + index);

    return Scaffold(
      backgroundColor: const Color(0xFFF4F6F8),
      appBar: AppBar(
        title: const Text('كارت الصنف / Product Ledger', style: TextStyle(color: FlarelineColors.darkBlackText)),
        backgroundColor: Colors.white,
        iconTheme: const IconThemeData(color: FlarelineColors.darkBlackText),
        elevation: 0,
      ),
      body: _isLoading && _products.isEmpty
          ? const Center(child: CircularProgressIndicator())
          : Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                children: [
                  // 1. Filter Section
                  CommonCard(
                    title: 'تصفية البيانات / Filters',
                    margin: const EdgeInsets.only(bottom: 16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        // Product Select Dropdown
                        const Text('اختر الصنف / Select Product', style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold)),
                        const SizedBox(height: 8),
                        DropdownButtonFormField<int>(
                          decoration: const InputDecoration(
                            border: OutlineInputBorder(
                              borderSide: BorderSide(color: FlarelineColors.border, width: 1),
                            ),
                            enabledBorder: OutlineInputBorder(
                              borderSide: BorderSide(color: FlarelineColors.border, width: 1),
                            ),
                            contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                          ),
                          value: _selectedProductId,
                          items: _products.map((p) {
                            return DropdownMenuItem<int>(
                              value: p['id'] as int,
                              child: Text(p['name']?.toString() ?? 'بدون اسم'),
                            );
                          }).toList(),
                          onChanged: (val) {
                            if (val != null) {
                              setState(() {
                                _selectedProductId = val;
                                // Reset other filters to let _filterLedger reload product default initial date
                                _fromMonth = null;
                                _fromYear = null;
                              });
                              _filterLedger();
                            }
                          },
                        ),
                        const SizedBox(height: 16),

                        // Date Ranges
                        Row(
                          children: [
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Text('من شهر', style: TextStyle(fontSize: 12)),
                                  const SizedBox(height: 4),
                                  DropdownButtonFormField<int>(
                                    decoration: const InputDecoration(
                                      border: OutlineInputBorder(
                                        borderSide: BorderSide(color: FlarelineColors.border, width: 1),
                                      ),
                                      contentPadding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                    ),
                                    value: _fromMonth,
                                    items: months.map((m) => DropdownMenuItem(value: m, child: Text(m.toString()))).toList(),
                                    onChanged: (val) => setState(() => _fromMonth = val),
                                  ),
                                ],
                              ),
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Text('من سنة', style: TextStyle(fontSize: 12)),
                                  const SizedBox(height: 4),
                                  DropdownButtonFormField<int>(
                                    decoration: const InputDecoration(
                                      border: OutlineInputBorder(
                                        borderSide: BorderSide(color: FlarelineColors.border, width: 1),
                                      ),
                                      contentPadding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                    ),
                                    value: _fromYear,
                                    items: years.map((y) => DropdownMenuItem(value: y, child: Text(y.toString()))).toList(),
                                    onChanged: (val) => setState(() => _fromYear = val),
                                  ),
                                ],
                              ),
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Text('إلى شهر', style: TextStyle(fontSize: 12)),
                                  const SizedBox(height: 4),
                                  DropdownButtonFormField<int>(
                                    decoration: const InputDecoration(
                                      border: OutlineInputBorder(
                                        borderSide: BorderSide(color: FlarelineColors.border, width: 1),
                                      ),
                                      contentPadding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                    ),
                                    value: _toMonth,
                                    items: months.map((m) => DropdownMenuItem(value: m, child: Text(m.toString()))).toList(),
                                    onChanged: (val) => setState(() => _toMonth = val),
                                  ),
                                ],
                              ),
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Text('إلى سنة', style: TextStyle(fontSize: 12)),
                                  const SizedBox(height: 4),
                                  DropdownButtonFormField<int>(
                                    decoration: const InputDecoration(
                                      border: OutlineInputBorder(
                                        borderSide: BorderSide(color: FlarelineColors.border, width: 1),
                                      ),
                                      contentPadding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                    ),
                                    value: _toYear,
                                    items: years.map((y) => DropdownMenuItem(value: y, child: Text(y.toString()))).toList(),
                                    onChanged: (val) => setState(() => _toYear = val),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 16),

                        ElevatedButton(
                          style: ElevatedButton.styleFrom(
                            backgroundColor: FlarelineColors.primary,
                            padding: const EdgeInsets.symmetric(vertical: 12),
                          ),
                          onPressed: _filterLedger,
                          child: const Text('تحديث / Filter Ledger', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                        )
                      ],
                    ),
                  ),

                  // 2. Grand Totals KPIs
                  Row(
                    children: [
                      _buildKpiCard('صافي الأرباح', '${_grandTotals['net_profit']} ج.م', ButtonColors.success, Icons.trending_up),
                      const SizedBox(width: 8),
                      _buildKpiCard('أرباح كاش', '${_grandTotals['cash_profit']} ج.م', ButtonColors.primary, Icons.monetization_on),
                      const SizedBox(width: 8),
                      _buildKpiCard('أرباح تقسيط', '${_grandTotals['inst_profit']} ج.م', ButtonColors.warn, Icons.payment),
                    ],
                  ),
                  const SizedBox(height: 16),

                  // 3. Tab Bar for Switch
                  Container(
                    color: Colors.white,
                    child: TabBar(
                      controller: _tabController,
                      labelColor: FlarelineColors.primary,
                      unselectedLabelColor: FlarelineColors.darkTextBody,
                      indicatorColor: FlarelineColors.primary,
                      tabs: const [
                        Tab(text: 'ملخص شهري / Monthly Summary'),
                        Tab(text: 'حركة كارت الصنف / Movements Log'),
                      ],
                    ),
                  ),

                  // 4. Tab Views
                  Expanded(
                    child: _isLoading
                        ? const Center(child: CircularProgressIndicator())
                        : TabBarView(
                            controller: _tabController,
                            children: [
                              // Tab 1: Monthly Summary
                              CommonCard(
                                margin: const EdgeInsets.symmetric(vertical: 8),
                                child: _monthlySummary.isEmpty
                                    ? const Center(child: Text('لا توجد بيانات للفترة المحددة'))
                                    : SingleChildScrollView(
                                        scrollDirection: Axis.horizontal,
                                        child: SingleChildScrollView(
                                          child: DataTable(
                                            headingRowColor: WidgetStateProperty.resolveWith<Color?>((states) => FlarelineColors.gray),
                                            columns: const [
                                              DataColumn(label: Text('التاريخ', style: TextStyle(fontWeight: FontWeight.bold, color: FlarelineColors.darkBlackText))),
                                              DataColumn(label: Text('رصيد أول', style: TextStyle(fontWeight: FontWeight.bold, color: FlarelineColors.darkBlackText))),
                                              DataColumn(label: Text('صافي مشتريات', style: TextStyle(fontWeight: FontWeight.bold, color: FlarelineColors.darkBlackText))),
                                              DataColumn(label: Text('مبيعات كاش', style: TextStyle(fontWeight: FontWeight.bold, color: FlarelineColors.darkBlackText))),
                                              DataColumn(label: Text('أرباح كاش', style: TextStyle(fontWeight: FontWeight.bold, color: FlarelineColors.darkBlackText))),
                                              DataColumn(label: Text('مبيعات تقسيط', style: TextStyle(fontWeight: FontWeight.bold, color: FlarelineColors.darkBlackText))),
                                              DataColumn(label: Text('أرباح تقسيط', style: TextStyle(fontWeight: FontWeight.bold, color: FlarelineColors.darkBlackText))),
                                              DataColumn(label: Text('رصيد آخر', style: TextStyle(fontWeight: FontWeight.bold, color: FlarelineColors.darkBlackText))),
                                              DataColumn(label: Text('تكلفة الوحدة', style: TextStyle(fontWeight: FontWeight.bold, color: FlarelineColors.darkBlackText))),
                                              DataColumn(label: Text('صافي الربح', style: TextStyle(fontWeight: FontWeight.bold, color: FlarelineColors.darkBlackText))),
                                            ],
                                            rows: _monthlySummary.map((m) {
                                              return DataRow(cells: [
                                                DataCell(Text('${m['month']}/${m['year']}')),
                                                DataCell(Text(m['opening'].toString())),
                                                DataCell(Text(m['purchases'].toString())),
                                                DataCell(Text(m['cash']['qty'].toString())),
                                                DataCell(Text('${m['cash']['profit'].toStringAsFixed(1)} ج.م')),
                                                DataCell(Text(m['inst']['qty'].toString())),
                                                DataCell(Text('${m['inst']['profit'].toStringAsFixed(1)} ج.م')),
                                                DataCell(Text(m['closing'].toString())),
                                                DataCell(Text('${m['cost_unit'].toStringAsFixed(1)} ج.م')),
                                                DataCell(Text('${m['month_net_profit'].toStringAsFixed(1)} ج.م', style: const TextStyle(fontWeight: FontWeight.bold, color: FlarelineColors.primary))),
                                              ]);
                                            }).toList(),
                                          ),
                                        ),
                                      ),
                              ),

                              // Tab 2: Movements Log
                              CommonCard(
                                margin: const EdgeInsets.symmetric(vertical: 8),
                                child: _movements.isEmpty
                                    ? const Center(child: Text('لا توجد حركات للصنف'))
                                    : SingleChildScrollView(
                                        scrollDirection: Axis.horizontal,
                                        child: SingleChildScrollView(
                                          child: DataTable(
                                            headingRowColor: WidgetStateProperty.resolveWith<Color?>((states) => FlarelineColors.gray),
                                            columns: const [
                                              DataColumn(label: Text('التاريخ', style: TextStyle(fontWeight: FontWeight.bold, color: FlarelineColors.darkBlackText))),
                                              DataColumn(label: Text('نوع الحركة', style: TextStyle(fontWeight: FontWeight.bold, color: FlarelineColors.darkBlackText))),
                                              DataColumn(label: Text('المرجع', style: TextStyle(fontWeight: FontWeight.bold, color: FlarelineColors.darkBlackText))),
                                              DataColumn(label: Text('العميل/المورد', style: TextStyle(fontWeight: FontWeight.bold, color: FlarelineColors.darkBlackText))),
                                              DataColumn(label: Text('وارد', style: TextStyle(fontWeight: FontWeight.bold, color: FlarelineColors.darkBlackText))),
                                              DataColumn(label: Text('منصرف', style: TextStyle(fontWeight: FontWeight.bold, color: FlarelineColors.darkBlackText))),
                                              DataColumn(label: Text('الرصيد', style: TextStyle(fontWeight: FontWeight.bold, color: FlarelineColors.darkBlackText))),
                                            ],
                                            rows: _movements.map((mov) {
                                              Color typeColor = FlarelineColors.darkBlackText;
                                              if (mov['type'] == 'INITIAL') typeColor = ButtonColors.info;
                                              if (mov['type'] == 'PURCHASE/IN') typeColor = ButtonColors.success;
                                              if (mov['type'] == 'RETURN/OUT' || mov['type'] == 'SALE/OUT') typeColor = ButtonColors.danger;

                                              return DataRow(cells: [
                                                DataCell(Text('${mov['month']}/${mov['year']}')),
                                                DataCell(Text(mov['type'].toString(), style: TextStyle(color: typeColor, fontWeight: FontWeight.bold))),
                                                DataCell(Text(mov['ref'].toString())),
                                                DataCell(Text(mov['person'].toString())),
                                                DataCell(Text(mov['in_qty'].toString())),
                                                DataCell(Text(mov['out_qty'].toString())),
                                                DataCell(Text(mov['balance'].toString(), style: const TextStyle(fontWeight: FontWeight.bold))),
                                              ]);
                                            }).toList(),
                                          ),
                                        ),
                                      ),
                              ),
                            ],
                          ),
                  ),
                ],
              ),
            ),
    );
  }
}
