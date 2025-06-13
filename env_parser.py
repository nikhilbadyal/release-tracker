import os
import re
from typing import Any

# Pattern to find ${VAR_NAME} anywhere in a string
# We remove the ^ and $ anchors to allow matching within strings.
# [\w\d_-]+ matches one or more word characters (a-z, A-Z, 0-9, _, -)
# Note: Hyphens are valid in environment variable names in some systems
ENV_VAR_PLACEHOLDER_PATTERN = re.compile(r"\${(?P<env>[\w\d_-]+)}")


class EnvironmentVariableNotFoundError(KeyError):
    """Custom exception raised when a required environment variable is not found."""


def _resolve_value_recursive(value: Any, strict: bool) -> Any:
    """
    Helper function to recursively resolve environment variable placeholders
    in a single value (string, dict, list).
    """
    if isinstance(value, str):
        # Check if the string contains the placeholder pattern
        if ENV_VAR_PLACEHOLDER_PATTERN.search(value):
            # Use re.sub with a function to replace all occurrences dynamically
            def replace_match(match: Any) -> str:
                env_key = match.group("env")
                env_value = os.getenv(env_key)

                if env_value is None:
                    if strict:
                        msg = f"Environment variable '{env_key}' not found while resolving '{value}'"
                        raise EnvironmentVariableNotFoundError(
                            msg,
                        )
                    # In non-strict mode, replace missing variables with an empty string
                    # when substituting within a string. If the whole string was ${VAR},
                    # this results in "". If a config *requires* a value (even empty),
                    # strict mode is better.
                    return ""
                # Strip leading/trailing whitespace from environment values
                return env_value.strip()

            # Apply the replacement function to all matches in the string
            # We use the compiled pattern for efficiency
            return ENV_VAR_PLACEHOLDER_PATTERN.sub(replace_match, value)
        # String doesn't contain the pattern, return as is
        return value

    if isinstance(value, dict):
        # Recursively process nested dictionaries
        # Call the main function to maintain the strictness logic at each dictionary level
        return resolve_env_placeholders_recursive(value, strict=strict)

    if isinstance(value, list):
        # Recursively process items in a list
        # Use a list comprehension to build a new list with resolved items
        return [_resolve_value_recursive(item, strict=strict) for item in value]

    # Not a string, dict, or list, return value as is
    return value


def resolve_env_placeholders_recursive(
    config: dict[str, Any],
    strict: bool = False,
) -> dict[str, Any]:
    """
    Recursively resolves environment variable placeholders in a dictionary.

    Placeholders are of the form ${ENV_VAR_NAME} and can appear anywhere
    within a string value, including within nested dictionaries and lists.

    Args:
        config: The dictionary to process. This function creates a new
                dictionary and does not modify the original.
        strict: If True, raises EnvironmentVariableNotFoundError if a referenced
                environment variable is not found. If False, replaces missing
                variables with an empty string when substituting within strings.
                Defaults to False.

    Returns
    -------
        A new dictionary with placeholders resolved.

    Raises
    ------
        EnvironmentVariableNotFoundError: If strict is True and a referenced
                                          environment variable is not found.
    """
    # Ensure the top level is a dictionary as expected by the type hint and logic
    if not isinstance(config, dict):
        # Depending on requirements, you might raise a TypeError here
        # or attempt to resolve if it's a single string/list, but
        # the function is designed for a dict root. Let's raise an error
        # for clarity if the input is not a dictionary.
        msg = "Input config must be a dictionary."
        raise TypeError(msg)

    resolved_config = {}
    for key, value in config.items():
        # Recursively resolve the value and assign to the new dictionary
        resolved_config[key] = _resolve_value_recursive(value, strict=strict)

    return resolved_config


# Example Usage (This part only runs when the script is executed directly)
if __name__ == "__main__":
    # Set some environment variables for testing
    os.environ["USER_NAME"] = "Alice"
    os.environ["DATA_PATH"] = "/opt/data"
    # os.environ["MISSING_VAR"] # Intentionally not set
    os.environ["TIMEOUT_SEC"] = "60"  # Example of a defined variable

    # Example configuration with nested structures and inline placeholders
    test_config = {
        "user": "${USER_NAME}",
        "paths": {
            "data": "${DATA_PATH}",
            "logs": "/var/log/${USER_NAME}",
            "temp": "/something",
            "missing": "${MISSING_VAR}",  # Missing variable placeholder
            "combined": "${DATA_PATH}/users/${USER_NAME}/config",
        },
        "settings": [
            {"timeout_ms": 5000},
            "ConnectTimeout=${TIMEOUT_SEC}",  # Variable is set
            "Protocol=tcp",
            {"host": "localhost", "port": "${PORT}"},  # Missing variable
        ],
        "database": {
            "url": "jdbc:postgresql://${DB_HOST}:${DB_PORT}/${DB_NAME}",  # All missing
        },
        "some_number": 123,
        "a_list": [1, 2, 3, "${ANOTHER_MISSING}"],  # Missing in a list
    }

    print("Original Config:")
    import json

    print(json.dumps(test_config, indent=2))
    print("-" * 30)

    print("Resolved Config (non-strict):")
    resolved_config_non_strict = resolve_env_placeholders_recursive(test_config, strict=False)
    print(json.dumps(resolved_config_non_strict, indent=2))
    print("-" * 30)

    print("Resolved Config (strict - expecting error for MISSING_VAR or others):")
    # Note: Depending on which missing variable is encountered first during recursion,
    # the error message might show different variable names.
    try:
        # Let's remove TIMEOUT_SEC to ensure a strict error is caught
        del os.environ["TIMEOUT_SEC"]
        resolved_config_strict = resolve_env_placeholders_recursive(test_config, strict=True)
        print(json.dumps(resolved_config_strict, indent=2))
    except EnvironmentVariableNotFoundError as e:
        print(f"Caught expected error: {e}")
    finally:
        # Clean up environment variables (optional, but good for testing)
        if "USER_NAME" in os.environ:
            del os.environ["USER_NAME"]
        if "DATA_PATH" in os.environ:
            del os.environ["DATA_PATH"]
        if "MISSING_VAR" in os.environ:
            del os.environ["MISSING_VAR"]
        if "TIMEOUT_SEC" in os.environ:
            os.environ["TIMEOUT_SEC"] = "60"  # Restore if needed by other tests
        if "PORT" in os.environ:
            del os.environ["PORT"]
        if "DB_HOST" in os.environ:
            del os.environ["DB_HOST"]
        if "DB_PORT" in os.environ:
            del os.environ["DB_PORT"]
        if "DB_NAME" in os.environ:
            del os.environ["DB_NAME"]
        if "ANOTHER_MISSING" in os.environ:
            del os.environ["ANOTHER_MISSING"]
