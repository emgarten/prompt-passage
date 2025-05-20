import pytest
from pathlib import Path

from local_llm_proxy.config import load_config


def test_load_config_file_not_found(tmp_path: Path) -> None:
    """Test FileNotFoundError when config file does not exist."""
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path / "non_existent.yaml")
