#!/usr/bin/env bash
# update-videos.sh — Update video references across the codebase
# Updated: 2026-03-29
#
# Usage:
#   1. Place exactly 3 .mp4 files in pages/hosting/videos/
#   2. Run: bash update-videos.sh
#
# The script will:
#   - Detect the 3 video files
#   - Let you assign each to video 1, 2, or 3 (controls presentation order)
#   - Prompt you for a short display label for each
#   - Update CONFIG.VIDEOS in utils/common.js
#   - Regenerate the task array in scripts/tasks-controller.js

set -euo pipefail

VIDEOS_DIR="pages/hosting/videos"
COMMON_JS="utils/common.js"
TASKS_JS="scripts/tasks-controller.js"

# --- Find videos ---

if [[ ! -d "$VIDEOS_DIR" ]]; then
  echo "Error: $VIDEOS_DIR directory not found."
  exit 1
fi

ALL_FILES=()
while IFS= read -r f; do
  ALL_FILES+=("$f")
done < <(find "$VIDEOS_DIR" -maxdepth 1 -name "*.mp4" -exec basename {} \; | sort)

if [[ ${#ALL_FILES[@]} -ne 3 ]]; then
  echo "Error: Expected exactly 3 .mp4 files in $VIDEOS_DIR, found ${#ALL_FILES[@]}:"
  for f in "${ALL_FILES[@]}"; do
    echo "  $f"
  done
  exit 1
fi

echo "=== Found videos ==="
for i in 0 1 2; do
  echo "  [$(( i + 1 ))] ${ALL_FILES[$i]}"
done
echo ""

# --- Assign order ---

echo "Assign each video to a position (1, 2, 3)."
echo "Video 1 is shown first, video 2 second, video 3 third."
echo ""

ORDERED_FILES=("" "" "")
USED=()

for slot in 1 2 3; do
  while true; do
    echo "Available:"
    for i in 0 1 2; do
      # Check if already used
      skip=false
      for u in "${USED[@]+"${USED[@]}"}"; do
        if [[ "$u" == "$i" ]]; then skip=true; break; fi
      done
      if [[ "$skip" == "false" ]]; then
        echo "  [$(( i + 1 ))] ${ALL_FILES[$i]}"
      fi
    done

    read -rp "Which file for video ${slot}? Enter number [1-3]: " choice
    idx=$(( choice - 1 ))

    # Validate
    if [[ $idx -lt 0 || $idx -gt 2 ]]; then
      echo "  Invalid choice. Enter 1, 2, or 3."
      continue
    fi

    already_used=false
    for u in "${USED[@]+"${USED[@]}"}"; do
      if [[ "$u" == "$idx" ]]; then already_used=true; break; fi
    done
    if [[ "$already_used" == "true" ]]; then
      echo "  That file is already assigned. Pick another."
      continue
    fi

    ORDERED_FILES[$((slot - 1))]="${ALL_FILES[$idx]}"
    USED+=("$idx")
    echo "  Video ${slot} = ${ALL_FILES[$idx]}"
    echo ""
    break
  done
done

# --- Get labels ---

LABELS=()
for i in 0 1 2; do
  # Generate a default label from filename
  default_label="${ORDERED_FILES[$i]%.mp4}"
  default_label="${default_label//_/ }"
  default_label="${default_label//-/ }"

  read -rp "Short label for video $((i+1)) [${default_label}]: " user_label
  if [[ -z "$user_label" ]]; then
    LABELS+=("$default_label")
  else
    LABELS+=("$user_label")
  fi
done

echo ""
echo "=== Final Configuration ==="
for i in 0 1 2; do
  echo "  Video $((i+1)): ${ORDERED_FILES[$i]}"
  echo "    Label: ${LABELS[$i]}"
done
echo ""
read -rp "Proceed with these updates? [Y/n] " confirm
if [[ "$confirm" =~ ^[Nn] ]]; then
  echo "Aborted."
  exit 0
fi

# --- Update CONFIG.VIDEOS in common.js ---

echo ""
echo "Updating $COMMON_JS ..."

TMPFILE=$(mktemp)
cat > "$TMPFILE" <<VIDEOF
  VIDEOS: {
    VIDEO_1: 'videos/${ORDERED_FILES[0]}',
    VIDEO_2: 'videos/${ORDERED_FILES[1]}',
    VIDEO_3: 'videos/${ORDERED_FILES[2]}'
  },
VIDEOF

perl -0777 -i -pe '
  BEGIN {
    open(my $fh, "<", "'"$TMPFILE"'") or die;
    local $/; $replacement = <$fh>; close $fh;
    chomp $replacement;
  }
  s/  VIDEOS: \{[^}]+\},/$replacement/s;
' "$COMMON_JS"

rm "$TMPFILE"
echo "  Updated CONFIG.VIDEOS"

# --- Regenerate tasks-controller.js task array ---

echo "Updating $TASKS_JS ..."

PLATFORMS=("Facebook" "Instagram" "Twitter")
PLATFORM_CLASSES=("facebook" "instagram" "twitter")
PLATFORM_CONFIGS=("FACEBOOK" "INSTAGRAM" "TWITTER")

TMPFILE=$(mktemp)
{
  echo "  tasks: ["
  echo "     // First cycle"

  for round in 1 2; do
    if [[ $round -eq 2 ]]; then
      echo "    // Second cycle - same videos, round 2"
    fi
    for v in 0 1 2; do
      for p in 0 1 2; do
        video_path="videos/${ORDERED_FILES[$v]}"
        label="${LABELS[$v]}"
        platform="${PLATFORMS[$p]}"
        platform_class="${PLATFORM_CLASSES[$p]}"
        platform_config="${PLATFORM_CONFIGS[$p]}"
        video_num=$((v + 1))

        if [[ $round -eq 2 && $v -eq 2 && $p -eq 2 ]]; then
          trailing=""
        else
          trailing=","
        fi

        echo "    {"
        echo "      platform: \"${platform}\","
        echo "      platformClass: \"${platform_class}\","
        echo "      task: \"${label}\","
        echo "      video: \"${video_path}\","
        echo "      link: CONFIG.PLATFORMS.${platform_config}.url,"
        echo "      platformId: CONFIG.PLATFORMS.${platform_config}.id,"
        echo "      videoNumber: ${video_num},"
        echo "      round: ${round}"
        echo "    }${trailing}"
      done
    done
  done

  echo "  ],"
} > "$TMPFILE"

perl -0777 -i -pe '
  BEGIN {
    open(my $fh, "<", "'"$TMPFILE"'") or die;
    local $/; $replacement = <$fh>; close $fh;
    chomp $replacement;
  }
  s/  tasks: \[.*?\],/$replacement/s;
' "$TASKS_JS"

rm "$TMPFILE"
echo "  Regenerated 18 task definitions (3 videos x 3 platforms x 2 rounds)"

echo ""
echo "=== Done ==="
echo "Videos updated. Review the changes:"
echo "  git diff $COMMON_JS $TASKS_JS"
