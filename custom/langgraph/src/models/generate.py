"""Generate Pydantic models from JSON Schema files.

Usage: uv run python -m src.models.generate

Reads schemas/*.json and generates corresponding Pydantic v2 models.
The manually-written models in pipeline.py and profile.py take precedence;
this script generates models for skill, agent, and tool-result schemas.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

SCHEMAS_DIR = Path(__file__).parent.parent.parent / "schemas"
OUTPUT_DIR = Path(__file__).parent


def generate_from_schema(schema_path: Path, output_name: str) -> None:
    """Generate a Pydantic model file from a JSON schema."""
    output_path = OUTPUT_DIR / f"{output_name}.py"

    cmd = [
        "datamodel-codegen",
        "--input",
        str(schema_path),
        "--output",
        str(output_path),
        "--input-file-type",
        "jsonschema",
        "--output-model-type",
        "pydantic_v2.BaseModel",
        "--target-python-version",
        "3.12",
        "--use-annotated",
        "--field-constraints",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"  ✓ Generated {output_path.name}")
    else:
        print(f"  ✗ Failed {output_path.name}: {result.stderr}")


def main():
    """Generate models from all schemas (except those with manual implementations)."""
    print("Generating Pydantic models from JSON schemas...")

    # These schemas have manual implementations already:
    # - pipeline-io.schema.json → src/models/pipeline.py
    # - model-profile.schema.json → src/models/profile.py
    #
    # Generate for the rest:
    schema_map = {
        "skill.schema.json": "skill",
        "agent.schema.json": "agent",
        "tool-result.schema.json": "tool_result",
    }

    for schema_file, output_name in schema_map.items():
        schema_path = SCHEMAS_DIR / schema_file
        if schema_path.exists():
            generate_from_schema(schema_path, output_name)
        else:
            print(f"  ⚠ Schema not found: {schema_file}")

    print("\nDone. Manual models (pipeline.py, profile.py) are unchanged.")


if __name__ == "__main__":
    main()
