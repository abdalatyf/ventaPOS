import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../widgets/inventory_tab.dart';
import '../widgets/salespersons_tab.dart';
import '../widgets/suppliers_tab.dart';
import '../../../../core/widgets/app_drawer.dart';

class SetupScreen extends ConsumerWidget {
  const SetupScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return DefaultTabController(
      length: 3,
      child: Scaffold(
        drawer: const AppDrawer(),
        appBar: AppBar(
          title: const Text('التأسيس'),
          bottom: const TabBar(
            tabs: [
              Tab(
                icon: Icon(Icons.inventory_2_outlined),
                text: 'تأسيس الأصناف',
              ),
              Tab(
                icon: Icon(Icons.people_outline),
                text: 'تأسيس المناديب',
              ),
              Tab(
                icon: Icon(Icons.local_shipping_outlined),
                text: 'تأسيس الموردين',
              ),
            ],
          ),
        ),
        body: const TabBarView(
          children: [
            InventoryTab(),
            SalespersonsTab(),
            SuppliersTab(),
          ],
        ),
      ),
    );
  }
}
