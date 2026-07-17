#!/usr/bin/env bash
set -e

# 1. Check that Docker Desktop is running.
#    If it's not, everything else fails, so we warn clearly.
if ! docker info > /dev/null 2>&1; then
  echo "Docker Desktop doesn't seem to be running. Open it and try again."
  exit 1
fi

# 2. Save the folder this script was called from.
#    This is the folder that will be visible inside the container.
REPO_DIR="$(pwd)"

# 3. Read the REAL configuration the container will use, straight
#    from devcontainer.json, instead of keeping the numbers copied by hand here.
#    "read-configuration" is a command from the devcontainers tool itself
#    that knows how to parse the file (including the "//" comments in it),
#    something Bash can't do on its own.
echo "Reading .devcontainer/devcontainer.json..."
CONFIG_JSON=$(npx --yes @devcontainers/cli read-configuration \
  --workspace-folder "$REPO_DIR" \
  --include-merged-configuration 2>/dev/null) || true

# 4. Extract the "runArgs" section from that configuration using Node
#    (you already have it installed, so no need to install anything extra just to read JSON).
RUNARGS_LINE=""
if [ -n "$CONFIG_JSON" ]; then
  RUNARGS_LINE=$(echo "$CONFIG_JSON" | node -e '
    let data = "";
    process.stdin.on("data", d => data += d);
    process.stdin.on("end", () => {
      try {
        const parsed = JSON.parse(data);
        const args = (parsed.mergedConfiguration && parsed.mergedConfiguration.runArgs) || [];
        console.log(args.join(" "));
      } catch (e) {
        // If the format changes or something fails, do not break the script, just show nothing.
      }
    });
  ' 2>/dev/null) || true
fi

# 5. Pull out the actual memory and CPU numbers from that runArgs line.
if [ -n "$RUNARGS_LINE" ]; then
  CONTAINER_MEMORY=$(echo "$RUNARGS_LINE" | grep -oE -- '--memory=[^ ]+' | cut -d= -f2)
  CONTAINER_CPUS=$(echo "$RUNARGS_LINE" | grep -oE -- '--cpus=[^ ]+' | cut -d= -f2)
fi
CONTAINER_MEMORY="${CONTAINER_MEMORY:-undefined}"
CONTAINER_CPUS="${CONTAINER_CPUS:-undefined}"

# 6. Ask Docker how much RAM/CPU its OWN internal VM has assigned
#    (what you configured in Docker Desktop > Settings > Resources).
VM_CPUS=$(docker info --format '{{.NCPU}}')
VM_MEM_BYTES=$(docker info --format '{{.MemTotal}}')
VM_MEM_GB=$(( VM_MEM_BYTES / 1073741824 ))

echo "-----------------------------------------------------"
echo " Resources assigned to the Docker Desktop VM:"
echo "   Total RAM:  ${VM_MEM_GB} GB"
echo "   Total CPUs: ${VM_CPUS}"
echo ""
echo " Resources this container will request (read from devcontainer.json):"
echo "   RAM:  ${CONTAINER_MEMORY}"
echo "   CPUs: ${CONTAINER_CPUS}"
echo "-----------------------------------------------------"

# 7. Warn if the container is requesting more than the VM has available.
if [ "$CONTAINER_MEMORY" != "undefined" ] && [ "$CONTAINER_CPUS" != "undefined" ]; then
  CONTAINER_MEM_NUM="${CONTAINER_MEMORY//g/}"
  if [ "$CONTAINER_MEM_NUM" -gt "$VM_MEM_GB" ] || [ "$CONTAINER_CPUS" -gt "$VM_CPUS" ]; then
    echo "WARNING: the container is requesting more resources than the Docker VM has."
    echo "The real limit will be the VM's. Check Docker Desktop > Settings > Resources."
    echo ""
  fi
else
  echo "WARNING: could not read resource limits from devcontainer.json."
  echo "Check the file by hand before continuing."
  echo ""
fi

# 8. Ask for explicit confirmation before starting anything.
read -p "Continue and launch the environment with these resources? (y/n) " ANSWER
if [[ "$ANSWER" != "y" && "$ANSWER" != "Y" ]]; then
  echo "Cancelled. Nothing was launched."
  exit 0
fi

echo "Repository: $REPO_DIR"
echo "Preparing isolated environment (first run takes longer, downloads the image)..."

# 9. "npx" downloads and runs a tool without installing it permanently.
#    "@devcontainers/cli" is the official tool that reads your devcontainer.json
#    and builds/starts the container.
npx --yes @devcontainers/cli up --workspace-folder "$REPO_DIR"

echo "Environment ready. Entering Claude Code..."

# 10. Run "claude" INSIDE the container, not on your Mac.
#     --dangerously-skip-permissions is safe here because the container itself
#     already prevents Claude from touching anything outside /workspace.
npx --yes @devcontainers/cli exec --workspace-folder "$REPO_DIR" \
  bash -lc "claude --dangerously-skip-permissions"