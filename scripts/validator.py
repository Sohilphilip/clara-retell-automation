import json
from pathlib import Path
from jsonschema import validate, ValidationError
from utils import log


def load_schema(schema_path):
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_json(data, schema_path, object_name="Object"):
    """
    Validate JSON against schema.
    Raises error if invalid.
    """
    schema = load_schema(schema_path)

    try:
        validate(instance=data, schema=schema)
        log(f"{object_name} passed schema validation.")
        return True
    except ValidationError as e:
        log(f"Validation failed for {object_name}: {e.message}")
        raise