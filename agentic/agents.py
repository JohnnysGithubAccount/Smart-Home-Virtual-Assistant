def lighting_agent(dim=None, color=None, off=False):
    print(f"[ACTION] Lighting agent called: dim={dim}, color={color}, off={off}")

def climate_agent(set_temp=None):
    print(f"[ACTION] Climate agent called: set_temp={set_temp}")

def security_agent(lock_doors=False):
    print(f"[ACTION] Security agent called: lock_doors={lock_doors}")

def media_agent(play=None):
    print(f"[ACTION] Media agent called: play={play}")
