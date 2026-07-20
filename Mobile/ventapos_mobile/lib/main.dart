import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_fonts/google_fonts.dart';
import 'features/receipts/presentation/screens/receipts_screen.dart';

import 'core/routing/app_router.dart';

void main() {
  runApp(
    // Added ProviderScope for Riverpod
    const ProviderScope(
      child: VentaPosApp(),
    ),
  );
}

class VentaPosApp extends ConsumerWidget {
  const VentaPosApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(appRouterProvider);

    return MaterialApp.router(
      title: 'VentaPOS Mobile',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
        useMaterial3: true,
        textTheme: GoogleFonts.cairoTextTheme(), // Arabic Font Support
      ),
      // Enforce RTL globally for Arabic UX
      builder: (context, child) {
        return Directionality(
          textDirection: TextDirection.rtl,
          child: child!,
        );
      },
      routerConfig: router,
    );
  }
}
