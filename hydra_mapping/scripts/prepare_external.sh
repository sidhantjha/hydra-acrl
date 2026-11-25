#!/usr/bin/env bash
set -euo pipefail
mapping=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
usage='Usage: prepare_external.sh aws|rpgo [local Git checkout]'
[[ $# -ge 1 && $# -le 2 ]] || { echo "$usage" >&2; exit 2; }

case "$1" in
  aws)
    url=https://github.com/aws-robotics/aws-robomaker-small-house-world.git
    revision=ff9631ca6d1db9c1ba656498151464b5ab74aafe
    destination="$mapping/small_house"
    ;;
  rpgo)
    url=https://github.com/MIT-SPARK/Kimera-RPGO.git
    revision=f1fee0900ef6825bf76304685668235cf5dd008d
    destination="$mapping/hydra_ws/src/kimera_rpgo"
    ;;
  *) echo "$usage" >&2; exit 2 ;;
esac

prepared=false
if [[ -f "$destination/.source-revision" && $(<"$destination/.source-revision") == "$revision" ]]; then
  if [[ $1 != aws || -f "$destination/.portrait-textures" ]]; then
    printf '%s already prepared at %s\n' "$revision" "$destination"
    exit 0
  fi
  prepared=true
elif [[ -e "$destination" ]]; then
  echo "Existing directory needs review: $destination" >&2
  exit 1
fi
mkdir -p "$mapping/external" "$(dirname -- "$destination")"
temporary=$(mktemp -d "$mapping/external/.prepare.XXXXXXXX")
trap 'rm -rf -- "$temporary"' EXIT
source_repo=${2:-"$temporary/source"}
if [[ $# == 1 ]]; then
  git init -q "$source_repo"
  printf '[Hydra-ACRL] Fetching %s at %s\n' "$1" "$revision"
  git -C "$source_repo" fetch --depth=1 --progress "$url" "$revision"
  [[ $(git -C "$source_repo" rev-parse FETCH_HEAD) == "$revision" ]]
fi

mkdir "$temporary/content"
if [[ $1 == aws && "$prepared" == false ]]; then
  world="$mapping/tb3_ws/src/tb3_hydra_bringup/worlds/small_house_hydra.world"
  [[ -s "$world" ]] || { echo "Missing packaged Small House world: $world" >&2; exit 1; }
  python3 - "$world" > "$temporary/models" <<'PY'
import sys
import xml.etree.ElementTree as ET

prefix = "model://aws_robomaker_residential_"
uris = {entry.text for entry in ET.parse(sys.argv[1]).iter("uri")}
for uri in sorted(uris):
    if uri.startswith(prefix):
        print("models/" + uri.removeprefix("model://").split("/")[0])
PY
  mapfile -t models < "$temporary/models"
  git -C "$source_repo" archive "$revision" LICENSE "${models[@]}" |
    tar -xf - -C "$temporary/content"
  GIT_CEILING_DIRECTORIES="$temporary" git -C "$temporary/content" apply --no-index \
    "$mapping/patches/aws-shoerack.patch"
  GIT_CEILING_DIRECTORIES="$temporary" git -C "$temporary/content" apply --no-index --reverse --check \
    "$mapping/patches/aws-shoerack.patch"
elif [[ $1 == rpgo ]]; then
  git -C "$source_repo" archive "$revision" | tar -xf - -C "$temporary/content"
fi

if [[ $1 == aws ]]; then
  # The original JPEGs are present upstream. Keep their bytes and resolve the
  # Collada references relative to our package-local meshes.
  git -C "$source_repo" archive "$revision" photos | tar -xf - -C "$temporary"
  asset_dir="$temporary/content"
  if [[ "$prepared" == true ]]; then asset_dir="$destination"; fi
  python3 - "$asset_dir" "$temporary/photos" <<'PYTHON'
from pathlib import Path
import re
import shutil
import sys

assets, photos = map(Path, sys.argv[1:])
prefix = b"../../../../photos/"
pattern = re.compile(rb"<init_from>" + re.escape(prefix) + rb"([\w.-]+\.jpg)</init_from>")
updates = []
for mesh in sorted((assets / "models").glob("*/meshes/*")):
    if mesh.suffix.lower() != ".dae":
        continue
    data = mesh.read_bytes()
    names = pattern.findall(data)
    if not names:
        continue
    textures = mesh.parent.parent / "materials/textures"
    for filename in names:
        name = filename.decode("ascii")
        source, destination = photos / name, textures / name
        if not source.is_file():
            raise SystemExit(f"Missing pinned portrait texture: {source}")
        if destination.exists() and source.read_bytes() != destination.read_bytes():
            raise SystemExit(f"Existing texture needs review: {destination}")
    updates.append((mesh, data.replace(prefix, b"../materials/textures/"), textures, names))

for mesh, data, textures, names in updates:
    textures.mkdir(parents=True, exist_ok=True)
    for filename in names:
        name = filename.decode("ascii")
        shutil.copyfile(photos / name, textures / name)
    temporary = mesh.with_suffix(mesh.suffix + ".tmp")
    temporary.write_bytes(data)
    temporary.replace(mesh)
print(f"Resolved portrait texture paths in {len(updates)} AWS meshes.")
PYTHON
  : > "$asset_dir/.portrait-textures"
  if [[ "$prepared" == true ]]; then exit 0; fi
fi
printf '%s\n' "$revision" > "$temporary/content/.source-revision"
mv -T --no-clobber "$temporary/content" "$destination"
[[ ! -e "$temporary/content" ]] || { echo "Destination appeared during preparation" >&2; exit 1; }
printf 'Prepared %s at %s\n' "$revision" "$destination"
