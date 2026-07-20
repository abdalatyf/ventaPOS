from sync_api.models import ServerBranch
for b in ServerBranch.objects.all():
    print(f"ID: {b.id}, Local ID: {b.local_id}, Source: {b.source_machine_id}")
