import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../features/home/presentation/screens/main_screen.dart';
import '../../features/receipts/presentation/screens/receipts_screen.dart';
import '../../features/receipts/presentation/screens/add_receipt_screen.dart';
import '../../features/inventory/presentation/screens/inventory_screen.dart';
import '../../features/sync/presentation/screens/sync_screen.dart';
import '../../features/setup/presentation/screens/setup_screen.dart';

final GlobalKey<NavigatorState> _rootNavigatorKey = GlobalKey<NavigatorState>(debugLabel: 'root');
final GlobalKey<NavigatorState> _receiptsNavigatorKey = GlobalKey<NavigatorState>(debugLabel: 'receiptsTab');
final GlobalKey<NavigatorState> _inventoryNavigatorKey = GlobalKey<NavigatorState>(debugLabel: 'inventoryTab');
final GlobalKey<NavigatorState> _syncNavigatorKey = GlobalKey<NavigatorState>(debugLabel: 'syncTab');
final GlobalKey<NavigatorState> _setupNavigatorKey = GlobalKey<NavigatorState>(debugLabel: 'setupTab');

final appRouterProvider = Provider<GoRouter>((ref) {
  return GoRouter(
    navigatorKey: _rootNavigatorKey,
    initialLocation: '/receipts',
    routes: [
      StatefulShellRoute.indexedStack(
        builder: (context, state, navigationShell) {
          return MainScreen(navigationShell: navigationShell);
        },
        branches: [
          StatefulShellBranch(
            navigatorKey: _receiptsNavigatorKey,
            routes: [
              GoRoute(
                path: '/receipts',
                builder: (context, state) => const ReceiptsScreen(),
                routes: [
                  GoRoute(
                    path: 'add',
                    builder: (context, state) => const AddReceiptScreen(),
                  ),
                ],
              ),
            ],
          ),
          StatefulShellBranch(
            navigatorKey: _inventoryNavigatorKey,
            routes: [
              GoRoute(
                path: '/inventory',
                builder: (context, state) => const InventoryScreen(),
              ),
            ],
          ),
          StatefulShellBranch(
            navigatorKey: _syncNavigatorKey,
            routes: [
              GoRoute(
                path: '/sync',
                builder: (context, state) => const SyncScreen(),
              ),
            ],
          ),
          StatefulShellBranch(
            navigatorKey: _setupNavigatorKey,
            routes: [
              GoRoute(
                path: '/setup',
                builder: (context, state) => const SetupScreen(),
              ),
            ],
          ),
        ],
      ),
    ],
  );
});
