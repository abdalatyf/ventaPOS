import json
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from sync_api.models import ServerBranch, ServerSalesperson

@method_decorator(csrf_exempt, name='dispatch')
class BranchViewSet(View):
    def get(self, request, pk=None):
        if pk:
            try:
                branch = ServerBranch.objects.get(pk=pk)
                data = {
                    'id': branch.id,
                    'source_machine_id': branch.source_machine_id,
                    'local_id': branch.local_id,
                    'name': branch.name,
                    'synced_at': branch.synced_at.isoformat() if branch.synced_at else None
                }
                return JsonResponse(data)
            except ServerBranch.DoesNotExist:
                return JsonResponse({'error': 'Not found'}, status=404)
        else:
            branches = ServerBranch.objects.all()
            data = [{
                'id': b.id,
                'source_machine_id': b.source_machine_id,
                'local_id': b.local_id,
                'name': b.name,
                'synced_at': b.synced_at.isoformat() if b.synced_at else None
            } for b in branches]
            return JsonResponse({'results': data})

    def post(self, request):
        try:
            data = json.loads(request.body)
            branch = ServerBranch.objects.create(
                source_machine_id=data.get('source_machine_id', 'API'),
                local_id=data.get('local_id'),
                name=data.get('name')
            )
            return JsonResponse({'id': branch.id, 'message': 'Created successfully'}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    def put(self, request, pk):
        try:
            branch = ServerBranch.objects.get(pk=pk)
            data = json.loads(request.body)
            branch.name = data.get('name', branch.name)
            if 'local_id' in data:
                branch.local_id = data.get('local_id')
            if 'source_machine_id' in data:
                branch.source_machine_id = data.get('source_machine_id')
            branch.save()
            return JsonResponse({'id': branch.id, 'message': 'Updated successfully'})
        except ServerBranch.DoesNotExist:
            return JsonResponse({'error': 'Not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    def delete(self, request, pk):
        try:
            branch = ServerBranch.objects.get(pk=pk)
            branch.delete()
            return JsonResponse({'message': 'Deleted successfully'}, status=204)
        except ServerBranch.DoesNotExist:
            return JsonResponse({'error': 'Not found'}, status=404)


@method_decorator(csrf_exempt, name='dispatch')
class SalespersonViewSet(View):
    def get(self, request, pk=None):
        if pk:
            try:
                sp = ServerSalesperson.objects.get(pk=pk)
                data = {
                    'id': sp.id,
                    'source_machine_id': sp.source_machine_id,
                    'local_id': sp.local_id,
                    'local_branch_id': sp.local_branch_id,
                    'name': sp.name,
                    'cloud_username': sp.cloud_username,
                    'cloud_password': sp.cloud_password,
                    'synced_at': sp.synced_at.isoformat() if sp.synced_at else None
                }
                return JsonResponse(data)
            except ServerSalesperson.DoesNotExist:
                return JsonResponse({'error': 'Not found'}, status=404)
        else:
            salespeople = ServerSalesperson.objects.all()
            data = [{
                'id': sp.id,
                'source_machine_id': sp.source_machine_id,
                'local_id': sp.local_id,
                'local_branch_id': sp.local_branch_id,
                'name': sp.name,
                'cloud_username': sp.cloud_username,
                'cloud_password': sp.cloud_password,
                'synced_at': sp.synced_at.isoformat() if sp.synced_at else None
            } for sp in salespeople]
            return JsonResponse({'results': data})

    def post(self, request):
        try:
            data = json.loads(request.body)
            sp = ServerSalesperson.objects.create(
                source_machine_id=data.get('source_machine_id', 'API'),
                local_id=data.get('local_id'),
                local_branch_id=data.get('local_branch_id'),
                name=data.get('name'),
                cloud_username=data.get('cloud_username'),
                cloud_password=data.get('cloud_password')
            )
            return JsonResponse({'id': sp.id, 'message': 'Created successfully'}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    def put(self, request, pk):
        try:
            sp = ServerSalesperson.objects.get(pk=pk)
            data = json.loads(request.body)
            sp.name = data.get('name', sp.name)
            if 'local_id' in data:
                sp.local_id = data.get('local_id')
            if 'local_branch_id' in data:
                sp.local_branch_id = data.get('local_branch_id')
            if 'source_machine_id' in data:
                sp.source_machine_id = data.get('source_machine_id')
            if 'cloud_username' in data:
                sp.cloud_username = data.get('cloud_username')
            if 'cloud_password' in data:
                sp.cloud_password = data.get('cloud_password')
            sp.save()
            return JsonResponse({'id': sp.id, 'message': 'Updated successfully'})
        except ServerSalesperson.DoesNotExist:
            return JsonResponse({'error': 'Not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    def delete(self, request, pk):
        try:
            sp = ServerSalesperson.objects.get(pk=pk)
            sp.delete()
            return JsonResponse({'message': 'Deleted successfully'}, status=204)
        except ServerSalesperson.DoesNotExist:
            return JsonResponse({'error': 'Not found'}, status=404)
