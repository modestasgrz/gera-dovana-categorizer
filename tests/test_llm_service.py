"""Tests for AI client layer."""

import json
from unittest.mock import AsyncMock, Mock

import pytest
from openai import APIError, RateLimitError
from src.llm_service import (
    CategoryOutput,
    ProductInput,
    categorize_batch_async,
    categorize_product_async,
    detect_language_async,
)


@pytest.mark.asyncio
async def test_categorize_product_async_success() -> None:
    """Test successful product categorization."""
    mock_client = AsyncMock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    comment = (
        "Chosen SPA ir masažai (spa-ir-masazai) (0.80); considered Unknown (0.10) but clear SPA."
    )
    mock_response.choices[0].message.content = json.dumps(
        {"category": "SPA ir masažai (spa-ir-masazai)", "comment": comment}
    )

    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    product = ProductInput(
        program_name="SPA poilsis",
        program_description="Masažai ir procedūros",
        about_place="Vilnius",
    )

    result = await categorize_product_async(mock_client, product, "gpt-5-nano", "lt")

    assert isinstance(result, CategoryOutput)
    assert result.category == "SPA ir masažai (spa-ir-masazai)"
    assert result.comment.startswith("Chosen SPA ir masažai (spa-ir-masazai)")
    mock_client.chat.completions.create.assert_called_once()


@pytest.mark.asyncio
async def test_categorize_product_async_empty_response() -> None:
    """Test handling of empty API response."""
    mock_client = AsyncMock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = None

    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    product = ProductInput(
        program_name="Test",
        program_description="Test",
        about_place="Test",
    )

    result = await categorize_product_async(mock_client, product, "gpt-5-nano", "lt")

    assert isinstance(result, CategoryOutput)
    assert result.category == "unknown"
    assert result.comment == "Unexpected error during categorization: Empty response from API"
    mock_client.chat.completions.create.assert_called_once()


@pytest.mark.asyncio
async def test_categorize_product_async_malformed_json() -> None:
    """Test handling of malformed JSON response."""
    mock_client = AsyncMock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "{invalid json}"

    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    product = ProductInput(
        program_name="Test",
        program_description="Test",
        about_place="Test",
    )

    result = await categorize_product_async(mock_client, product, "gpt-5-nano", "lt")

    assert isinstance(result, CategoryOutput)
    assert result.category == "unknown"
    assert "Unexpected error during categorization" in result.comment
    mock_client.chat.completions.create.assert_called_once()


@pytest.mark.asyncio
async def test_categorize_product_async_rate_limit_retry() -> None:
    """Test that RateLimitError triggers a retry and eventually succeeds."""
    mock_client = AsyncMock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(
        {
            "category": "Vandens pramogos (vandens-pramogos)",
            "comment": "Chosen Vandens pramogos (vandens-pramogos) (0.62); considered Unknown (0.18) but water activity.",  # noqa: E501
        }
    )

    # First call raises RateLimitError, second call succeeds
    mock_client.chat.completions.create = AsyncMock(
        side_effect=[
            RateLimitError(
                "Rate limit exceeded",
                response=Mock(status_code=429),
                body=None,
            ),
            mock_response,
        ]
    )

    product = ProductInput(
        program_name="Test",
        program_description="Test",
        about_place="Test",
    )

    result = await categorize_product_async(mock_client, product, "gpt-5-nano", "lt")

    assert result.category == "Vandens pramogos (vandens-pramogos)"
    assert mock_client.chat.completions.create.call_count == 2


@pytest.mark.asyncio
async def test_categorize_product_async_rate_limit_error() -> None:
    """Test handling of rate limit errors after exhausting retries."""
    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(
        side_effect=RateLimitError(
            "Rate limit exceeded",
            response=Mock(status_code=429),
            body=None,
        )
    )

    product = ProductInput(
        program_name="Test",
        program_description="Test",
        about_place="Test",
    )

    # RateLimitError should be caught after exhausted retries and return CategoryOutput with unknown
    result = await categorize_product_async(mock_client, product, "gpt-5-nano", "lt")

    assert isinstance(result, CategoryOutput)
    assert result.category == "unknown"
    assert "Rate limit exceeded" in result.comment

    # Should have called 6 times as per RETRY_MAX_ATTEMPTS (set in conftest.py)
    assert mock_client.chat.completions.create.call_count == 6


@pytest.mark.asyncio
async def test_categorize_product_async_api_error() -> None:
    """Test handling of general API errors."""
    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(
        side_effect=APIError(
            "API error",
            request=Mock(),
            body=None,
        )
    )

    product = ProductInput(
        program_name="Test",
        program_description="Test",
        about_place="Test",
    )

    # APIError should be caught and return CategoryOutput with unknown
    result = await categorize_product_async(mock_client, product, "gpt-5-nano", "lt")

    assert isinstance(result, CategoryOutput)
    assert result.category == "unknown"
    assert "OpenAI API error" in result.comment


@pytest.mark.asyncio
async def test_categorize_product_async_unexpected_error() -> None:
    """Test handling of unexpected errors."""
    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(side_effect=ValueError("Unexpected error"))

    product = ProductInput(
        program_name="Test",
        program_description="Test",
        about_place="Test",
    )

    result = await categorize_product_async(mock_client, product, "gpt-5-nano", "lt")

    assert isinstance(result, CategoryOutput)
    assert result.category == "unknown"
    assert "Unexpected error during categorization" in result.comment


@pytest.mark.asyncio
async def test_categorize_batch_async_success() -> None:
    """Test batch categorization with multiple products."""
    mock_client = AsyncMock()

    # Mock responses for different products
    def create_mock_response(category: str) -> Mock:
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(
            {
                "category": category,
                "comment": f"Chosen {category} (0.70); considered Unknown (0.10) but matches.",
            }
        )
        return mock_response

    mock_client.chat.completions.create = AsyncMock(
        side_effect=[
            create_mock_response("SPA ir masažai (spa-ir-masazai)"),
            create_mock_response("Vakarienės (vakarienes)"),
            create_mock_response("Poilsis Lietuvoje (poilsis-su-nakvyne)"),
        ]
    )

    products: list[ProductInput] = [
        ProductInput(
            program_name="SPA",
            program_description="Masažai",
            about_place="Vilnius",
        ),
        ProductInput(
            program_name="Restoranas",
            program_description="Pietūs",
            about_place="Kaunas",
        ),
        ProductInput(
            program_name="Viešbutis",
            program_description="Nakvynė",
            about_place="Klaipėda",
        ),
    ]

    results = await categorize_batch_async(mock_client, products, "gpt-5-nano", "lt")

    # Wrap in gather check since gather return values might be wrapped
    assert len(results) == 3
    assert isinstance(results[0], CategoryOutput)
    assert results[0].category == "SPA ir masažai (spa-ir-masazai)"
    assert isinstance(results[1], CategoryOutput)
    assert results[1].category == "Vakarienės (vakarienes)"
    assert isinstance(results[2], CategoryOutput)
    assert results[2].category == "Poilsis Lietuvoje (poilsis-su-nakvyne)"


@pytest.mark.asyncio
async def test_categorize_batch_async_with_exceptions() -> None:
    """Test batch categorization handles exceptions gracefully."""
    mock_client = AsyncMock()

    def create_mock_response(category: str) -> Mock:
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(
            {
                "category": category,
                "comment": f"Chosen {category} (0.70); considered Unknown (0.10) but matches.",
            }
        )
        return mock_response

    # First succeeds, second fails, third succeeds
    mock_client.chat.completions.create = AsyncMock(
        side_effect=[
            create_mock_response("SPA ir masažai (spa-ir-masazai)"),
            ValueError("Test error"),
            create_mock_response("Poilsis Lietuvoje (poilsis-su-nakvyne)"),
        ]
    )

    products: list[ProductInput] = [
        ProductInput(program_name="SPA", program_description="Test", about_place="Test"),
        ProductInput(
            program_name="Error",
            program_description="Test",
            about_place="Test",
        ),
        ProductInput(
            program_name="Hotel",
            program_description="Test",
            about_place="Test",
        ),
    ]

    results = await categorize_batch_async(mock_client, products, "gpt-5-nano", "lt")

    assert len(results) == 3
    assert isinstance(results[0], CategoryOutput)
    assert results[0].category == "SPA ir masažai (spa-ir-masazai)"
    assert isinstance(results[1], CategoryOutput)
    assert results[1].category == "unknown"
    assert "Unexpected error" in results[1].comment
    assert isinstance(results[2], CategoryOutput)
    assert results[2].category == "Poilsis Lietuvoje (poilsis-su-nakvyne)"


@pytest.mark.asyncio
async def test_categorize_batch_async_empty_list() -> None:
    """Test batch categorization with empty product list."""
    mock_client = AsyncMock()

    results = await categorize_batch_async(mock_client, [], "gpt-5-nano", "lt")

    assert len(results) == 0
    mock_client.chat.completions.create.assert_not_called()


@pytest.mark.asyncio
async def test_detect_language_async_lithuanian() -> None:
    """Test language detection returns Lithuanian."""
    mock_client = AsyncMock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps({"language": "lt"})

    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    result = await detect_language_async(mock_client, "SPA dovana Vilniuje", "gpt-5-nano")

    assert result == "lt"
    mock_client.chat.completions.create.assert_called_once()


@pytest.mark.asyncio
async def test_detect_language_async_latvian() -> None:
    """Test language detection returns Latvian."""
    mock_client = AsyncMock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps({"language": "lv"})

    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    result = await detect_language_async(mock_client, "SPA dāvana Rīgā", "gpt-5-nano")

    assert result == "lv"


@pytest.mark.asyncio
async def test_detect_language_async_polish() -> None:
    """Test language detection returns Polish."""
    mock_client = AsyncMock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps({"language": "pl"})

    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    result = await detect_language_async(mock_client, "Prezent SPA w Warszawie", "gpt-5-nano")

    assert result == "pl"


@pytest.mark.asyncio
async def test_detect_language_async_unknown() -> None:
    """Test language detection returns unknown for unrecognized language."""
    mock_client = AsyncMock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps({"language": "unknown"})

    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    result = await detect_language_async(mock_client, "???", "gpt-5-nano")

    assert result == "unknown"


@pytest.mark.asyncio
async def test_detect_language_async_invalid_code() -> None:
    """Test language detection handles invalid language codes."""
    mock_client = AsyncMock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps({"language": "invalid"})

    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    result = await detect_language_async(mock_client, "test", "gpt-5-nano")

    assert result == "unknown"


@pytest.mark.asyncio
async def test_detect_language_async_error() -> None:
    """Test language detection handles errors gracefully."""
    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(side_effect=ValueError("API error"))

    result = await detect_language_async(mock_client, "test", "gpt-5-nano")

    assert result == "unknown"
