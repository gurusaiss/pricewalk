import pytest

from core.settings import Settings


def test_cors_origin_list_splits_comma_separated_values() -> None:
    settings = Settings(cors_origins="https://a.example.com, https://b.example.com")
    assert settings.cors_origin_list == ["https://a.example.com", "https://b.example.com"]


def test_cors_origin_list_default_is_localhost() -> None:
    settings = Settings()
    assert settings.cors_origin_list == ["http://localhost:3000"]


@pytest.mark.parametrize("value", ["", "  "])
def test_cors_origin_list_empty_is_empty_list(value: str) -> None:
    settings = Settings(cors_origins=value)
    assert settings.cors_origin_list == []
