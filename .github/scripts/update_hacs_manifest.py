"""Update the manifest file."""
import json
import os
import sys


def update_manifest():
    """Update the manifest file."""
    version = "0.0.0"
    manifest_path = False
    for index, value in enumerate(sys.argv):
        if value in ["--version", "-V"]:
            version = sys.argv[index + 1]
        if value in ["--path", "-P"]:
            manifest_path = sys.argv[index + 1]

    if not manifest_path:
        sys.exit("Missing path to manifest file")

    with open(
        f"{os.getcwd()}/{manifest_path.removesuffix('/').removesuffix('/')}/manifest.json",
        encoding="UTF-8",
    ) as manifestfile:
        manifest = json.load(manifestfile)

    manifest["version"] = version.removeprefix("v")

    requirements = []
    with open(
        f"{os.getcwd()}/requirements.txt",
        encoding="UTF-8",
    ) as file:
        for line in file:
            requirements.append(line.rstrip())

    new_requirements = []
    for requirement in requirements:
        req = requirement.split("==")[0].lower()
        new_requirements = [
            requirement for x in manifest["requirements"] if x.lower().startswith(req)
        ]
        new_requirements += [
            x for x in manifest["requirements"] if not x.lower().startswith(req)
        ]
        manifest["requirements"] = new_requirements

    with open(
        f"{os.getcwd()}/{manifest_path.removesuffix('/').removesuffix('/')}/manifest.json",
        "w",
        encoding="UTF-8",
    ) as manifestfile:
        manifestfile.write(json.dumps(manifest, indent=4, sort_keys=True))


update_manifest()
