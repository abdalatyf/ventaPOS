import re
import os

filepath = 'backend/api/tools_views.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# We just replace any ActionLog.objects.create( ... ) with a standardized version
# We can find all ActionLog.objects.create by finding the balanced parentheses
# But a regex works well enough if we match until the next closing parenthesis that is the end of the statement

pattern = r'ActionLog\.objects\.create\s*\(\s*tenant=request\.tenant,\s*branch=request\.branch,\s*action_type=([^,]+),\s*details=([^,]+),\s*user=request\.user\s*\)'

def replacer(match):
    action_type = match.group(1).strip()
    details = match.group(2).strip()
    return f'ActionLog.objects.create(actor=getattr(request.user, "username", "System"), action_type={action_type}, model_name="Tools", details={details})'

new_content = re.sub(pattern, replacer, content)

# There are a few that don't match the exact spacing or have newlines.
# Let's just use a simpler regex that matches up to the closing parenthesis
pattern2 = r'ActionLog\.objects\.create\((.*?)\)'
def replacer2(match):
    inner = match.group(1)
    
    # extract action_type
    at_match = re.search(r'action_type=\s*([^,]+)', inner)
    det_match = re.search(r'details=\s*([^,\n]+(?:,\s*[^,\n]+)*?)(\n|$|, user)', inner) # this is tricky because details can contain commas if f-string
    
    # better: just parse by hand
    at = '"Unknown"'
    if at_match: at = at_match.group(1).strip()
    
    det = '""'
    m = re.search(r'details=(f?"[^"]+"|f?\'[^\']+\')', inner)
    if m:
        det = m.group(1)
        
    return f'ActionLog.objects.create(actor=getattr(request.user, "username", "System"), action_type={at}, model_name="Tools", details={det})'

new_content2 = re.sub(pattern2, replacer2, content, flags=re.DOTALL)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(new_content2)

print("done")
