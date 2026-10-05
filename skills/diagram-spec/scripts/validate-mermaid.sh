#!/bin/bash
# Usage: ./validate-mermaid.sh <markdown_file>

FILE=$1
TMP_SVG="/tmp/mermaid-test-$(date +%s).svg"

# -y auto-installs the package without prompting the agent
# -p points to the sandbox bypass config
npx -y @mermaid-js/mermaid-cli@latest -i "$FILE" -o "$TMP_SVG" -p ./assets/puppeteer-config.json

# Capture the exit code
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
  echo "Mermaid validation failed. Check syntax."
  exit $EXIT_CODE
else
  echo "Mermaid validation passed!"
  rm -f "$TMP_SVG"
  exit 0
fi