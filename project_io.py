import json
import os
import zipfile
from pathlib import Path
from typing import List, Dict, Optional


def save_project(steps: List[Dict], output_path: str) -> None:
    """Save a list of step dictionaries to a zip file."""
    manifest = {"version": "1.0", "steps": []}
    for step in steps:
        step_data = {
            "filename": os.path.basename(step["filename"]),
            "title": step.get("title", ""),
            "alerts_above": step.get("alerts_above", []),
            "alerts_below": step.get("alerts_below", []),
        }
        manifest["steps"].append(step_data)

    with zipfile.ZipFile(output_path, "w") as zf:
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))
        for step in steps:
            if os.path.exists(step["filename"]):
                zf.write(step["filename"], os.path.basename(step["filename"]))


def load_project(zip_path: str, extract_to: Optional[str] = None) -> List[Dict]:
    """Load a project from a zip archive and return the steps list."""
    steps = []
    with zipfile.ZipFile(zip_path, "r") as zf:
        with zf.open("manifest.json") as mf:
            manifest = json.load(mf)
        for step in manifest.get("steps", []):
            filename = step["filename"]
            if extract_to:
                Path(extract_to).mkdir(parents=True, exist_ok=True)
                zf.extract(filename, path=extract_to)
                file_path = os.path.join(extract_to, filename)
            else:
                dest_dir = os.path.dirname(zip_path)
                zf.extract(filename, path=dest_dir)
                file_path = os.path.join(dest_dir, filename)
            steps.append({
                "filename": file_path,
                "title": step.get("title", ""),
                "alerts_above": step.get("alerts_above", []),
                "alerts_below": step.get("alerts_below", []),
            })
    return steps
