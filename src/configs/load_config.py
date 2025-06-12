from functools import lru_cache
from pathlib import Path
from typing import Any
import yaml


@lru_cache
def load_config(config_path: Path, _format: str = "dict") -> dict[str, Any] | str:
    """
    Load configuration from a YAML file into a dictionary.

    Parameters
    ----------
    config_path : Path
        Path to the YAML configuration file.
    _format : str, optional
        The format in which to return the configuration, by default "dict".

    Returns
    -------
    dict[str, Any] | str
        A dictionary containing the configuration parameters if _format="dict",
        otherwise the raw YAML content as a string.
    """
    with open(config_path, "r") as file:
        content = file.read()

    if _format == "dict":
        return yaml.safe_load(content)
    else:
        return content


PROMPT_LIBRARY = load_config(Path(__file__).parent / "prompt_library.yml")
