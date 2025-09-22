
import os
from pathlib import Path

def replace_env_vars(config: dict):
    def _replace(obj):
        if isinstance(obj, dict):
            return {k: _replace(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_replace(x) for x in obj]
        if isinstance(obj, str):
            if obj.startswith("${") and obj.endswith("}"):
                key = obj[2:-1]
                return os.environ.get(key, "")
        return obj
    for key in list(config.keys()):
        config[key] = _replace(config[key])

def resolve_paths(config: dict):
    base = Path(".").resolve()
    def _resolve(path):
        p = Path(path)
        return str((base / p).resolve())
    # only essential paths
    pconf = config.get("paths", {})
    for k in ["download_folder","work_folder","storage_folder","output_folder","log_folder","checkpoint_folder"]:
        if k in pconf:
            pconf[k] = _resolve(pconf[k])

def ensure_dirs(config: dict):
    from pathlib import Path
    for p in [
        config["paths"]["download_folder"],
        config["paths"]["work_folder"],
        config["paths"]["storage_folder"],
        config["paths"]["output_folder"],
        config["paths"]["log_folder"],
        config["paths"]["checkpoint_folder"],
    ]:
        Path(p).mkdir(parents=True, exist_ok=True)
