import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class MainScreen extends StatelessWidget {
  final StatefulNavigationShell navigationShell;

  const MainScreen({Key? key, required this.navigationShell}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    // We removed the BottomNavigationBar. 
    // The navigationShell is returned directly so each branch (screen)
    // can define its own Scaffold with an AppBar and an AppDrawer.
    return navigationShell;
  }
}
