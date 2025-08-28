#!/usr/bin/env bash
set -euo pipefail

# This script ensures the IAM directory exists (it is gitignored)
# and bootstraps iam/wort_s3.env from the example file if missing.
# Safe to run multiple times; it will not overwrite existing files.

ROOT_DIR="$(cd "$(dirname "$0")"/.. && pwd)"
IAM_DIR="$ROOT_DIR/iam"
EXAMPLE_ENV="$IAM_DIR/wort_s3.env.example"
TARGET_ENV="$IAM_DIR/wort_s3.env"

# Ensure the IAM directory exists
if [[ ! -d "$IAM_DIR" ]]; then
  echo "Creating $IAM_DIR ..."
  mkdir -p "$IAM_DIR"
else
  echo "$IAM_DIR already exists."
fi

# Ensure example file exists (tracked in repo)
if [[ ! -f "$EXAMPLE_ENV" ]]; then
  echo "WARNING: $EXAMPLE_ENV not found."
  echo "If you don't have it, create one with the following contents:"
  cat <<'EOF'
# Example environment variables for the Celery worker (S3/SQS access)
# Copy this file to iam/wort_s3.env and set your real values.
AWS_ACCESS_KEY_ID=REPLACE_WITH_YOUR_KEY_ID
AWS_SECRET_ACCESS_KEY=REPLACE_WITH_YOUR_SECRET
AWS_DEFAULT_REGION=us-east-1
# AWS_PROFILE=default
EOF
else
  echo "Found example file: $EXAMPLE_ENV"
fi

# Create the real env file if missing
if [[ ! -f "$TARGET_ENV" ]]; then
  if [[ -f "$EXAMPLE_ENV" ]]; then
    cp "$EXAMPLE_ENV" "$TARGET_ENV"
    echo "Created $TARGET_ENV from example. Please edit it with your AWS credentials."
  else
    # Fall back: create a stub file
    cat > "$TARGET_ENV" <<'EOF'
# Environment variables for the Celery worker (S3/SQS access)
AWS_ACCESS_KEY_ID=REPLACE_WITH_YOUR_KEY_ID
AWS_SECRET_ACCESS_KEY=REPLACE_WITH_YOUR_SECRET
AWS_DEFAULT_REGION=us-east-1
# AWS_PROFILE=default
EOF
    echo "Created $TARGET_ENV with placeholder values. Please edit it with your AWS credentials."
  fi
else
  echo "$TARGET_ENV already exists; not modifying."
fi

echo "Done."
