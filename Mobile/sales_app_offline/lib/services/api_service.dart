import 'dart:convert';
import 'package:http/http.dart' as http;
import '../db/database_helper.dart';

class ApiService {
  static Future<bool> pushToCloud(Map<String, dynamic> payload) async {
    try {
      final dbHelper = DatabaseHelper();
      String? baseUrl = await dbHelper.getBaseUrl();
      if (baseUrl == null || baseUrl.isEmpty) {
        print('Error: baseUrl is not set.');
        return false;
      }

      // Determine correct endpoint based on URL (Ngrok vs Local IP)
      String endpoint = baseUrl.contains('ngrok') || baseUrl.contains('http') 
          ? '$baseUrl/api/v1/sync/mobile-push/'
          : 'http://$baseUrl/api/v1/sync/mobile-push/';

      // If baseUrl already ends with / or has the full path, we can refine this later
      // But let's construct it safely:
      Uri uri;
      if (baseUrl.contains('api/v1/sync')) {
         uri = Uri.parse(baseUrl);
      } else {
         String cleanBase = baseUrl.endsWith('/') ? baseUrl.substring(0, baseUrl.length - 1) : baseUrl;
         if (!cleanBase.startsWith('http')) {
            cleanBase = 'http://$cleanBase';
         }
         uri = Uri.parse('$cleanBase/api/v1/sync/mobile-push/');
      }

        Map<String, dynamic> machineInfo = await dbHelper.getMachineInfo() ?? {};
        
        Map<String, dynamic> wrappedPayload = {
          'company_code': machineInfo['company_code'],
          'machine_id': machineInfo['master_machine_id'],
          'payload': payload,
        };

        final response = await http.post(
          uri,
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode(wrappedPayload),
        );
      
      if (response.statusCode == 200 || response.statusCode == 201) {
        return true;
      } else {
        print('Error: ${response.statusCode} - ${response.body}');
        return false;
      }
    } catch (e) {
      print('Exception during pushToCloud: $e');
      return false;
    }
  }

  static Future<bool> pullUpdates() async {
    try {
      final dbHelper = DatabaseHelper();
      String? baseUrl = await dbHelper.getBaseUrl();
      if (baseUrl == null || baseUrl.isEmpty) return false;

      String? role = await dbHelper.getRole();
      String? lastSync = await dbHelper.getLastSync();
      Map<String, dynamic> machineInfo = await dbHelper.getMachineInfo() ?? {};

      String cleanBase = baseUrl.endsWith('/') ? baseUrl.substring(0, baseUrl.length - 1) : baseUrl;
      if (!cleanBase.startsWith('http')) {
        cleanBase = 'http://$cleanBase';
      }
      Uri uri = Uri.parse('$cleanBase/api/v1/sync/pull/');

      final response = await http.post(
        uri,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'company_code': machineInfo['company_code'],
          'machine_id': machineInfo['master_machine_id'],
          'role': role ?? 'SALESPERSON',
          'last_sync': lastSync ?? '1970-01-01',
        }),
      );

      if (response.statusCode == 200) {
        print("====== DATA TRANSFERRED SUCCESSFULLY ======");
        print("Raw Pull Response: ${response.body}");
        print("===========================================");
        Map<String, dynamic> data = jsonDecode(response.body);
        if (data.containsKey('receipts')) {
          for (var r in data['receipts']) {
            await dbHelper.upsertReceipt(r);
          }
        }
        if (data.containsKey('products')) {
          for (var p in data['products']) {
            await dbHelper.upsertProduct(p);
          }
        }
        await dbHelper.setLastSync(DateTime.now().toIso8601String());
        return true;
      }
      return false;
    } catch (e) {
      print('Exception during pullUpdates: $e');
      return false;
    }
  }
}
