from functools import lru_cache
from pathlib import Path
from typing import Any
import yaml

from configs.config_models import StepModelsConfigs


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


def load_module_config(config_path, config_model=None):
    """
    Load a YAML configuration file and validate against a Pydantic model.
    """
    config_data = load_config(config_path)

    if config_model:
        return config_model(**config_data)

    return config_data


PROMPT_LIBRARY = load_config(Path(__file__).parent / "prompt_library.yaml")
APP_STEPS_CONFIGS = load_module_config(
    Path(__file__).parent / "config.yaml", StepModelsConfigs
)
