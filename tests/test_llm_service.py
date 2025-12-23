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
)


@pytest.mark.asyncio
async def test_categorize_product_async_success() -> None:
    """Test successful product categorization."""
    mock_client = AsyncMock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps({"category": "spa_wellness"})

    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    product = ProductInput(
        ProgramName="SPA poilsis",
        ProgramDescription="Masažai ir procedūros",
        About_Place="Vilnius",
    )

    result = await categorize_product_async(mock_client, product, "gpt-5-nano")

    assert isinstance(result, CategoryOutput)
    assert result.category == "spa_wellness"
    assert result.comment == ""
    mock_client.chat.completions.create.assert_called_once()


@pytest.mark.asyncio
async def test_categorize_product_async_invalid_category() -> None:
    """Test that invalid categories are converted to unknown."""
    mock_client = AsyncMock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps({"category": "invalid_category"})

    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    product = ProductInput(
        ProgramName="Test",
        ProgramDescription="Test",
        About_Place="Test",
    )

    result = await categorize_product_async(mock_client, product, "gpt-5-nano")

    assert isinstance(result, CategoryOutput)
    assert result.category == "unknown"
    assert result.comment == "Invalid category returned by model"
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
        ProgramName="Test",
        ProgramDescription="Test",
        About_Place="Test",
    )

    result = await categorize_product_async(mock_client, product, "gpt-5-nano")

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
        ProgramName="Test",
        ProgramDescription="Test",
        About_Place="Test",
    )

    result = await categorize_product_async(mock_client, product, "gpt-5-nano")

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
    mock_response.choices[0].message.content = json.dumps({"category": "spa_wellness"})

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
        ProgramName="Test",
        ProgramDescription="Test",
        About_Place="Test",
    )

    result = await categorize_product_async(mock_client, product, "gpt-5-nano")

    assert result.category == "spa_wellness"
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
        ProgramName="Test",
        ProgramDescription="Test",
        About_Place="Test",
    )

    # RateLimitError should be caught after exhausted retries and return CategoryOutput with unknown
    result = await categorize_product_async(mock_client, product, "gpt-5-nano")

    assert isinstance(result, CategoryOutput)
    assert result.category == "unknown"
    assert "Rate limit exceeded" in result.comment

    # Should have called 5 times as per stop_after_attempt(5)
    assert mock_client.chat.completions.create.call_count == 5


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
        ProgramName="Test",
        ProgramDescription="Test",
        About_Place="Test",
    )

    # APIError should be caught and return CategoryOutput with unknown
    result = await categorize_product_async(mock_client, product, "gpt-5-nano")

    assert isinstance(result, CategoryOutput)
    assert result.category == "unknown"
    assert "OpenAI API error" in result.comment


@pytest.mark.asyncio
async def test_categorize_product_async_unexpected_error() -> None:
    """Test handling of unexpected errors."""
    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(side_effect=ValueError("Unexpected error"))

    product = ProductInput(
        ProgramName="Test",
        ProgramDescription="Test",
        About_Place="Test",
    )

    result = await categorize_product_async(mock_client, product, "gpt-5-nano")

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
        mock_response.choices[0].message.content = json.dumps({"category": category})
        return mock_response

    mock_client.chat.completions.create = AsyncMock(
        side_effect=[
            create_mock_response("spa_wellness"),
            create_mock_response("restaurants_food"),
            create_mock_response("accommodation"),
        ]
    )

    products: list[ProductInput] = [
        ProductInput(
            ProgramName="SPA",
            ProgramDescription="Masažai",
            About_Place="Vilnius",
        ),
        ProductInput(
            ProgramName="Restoranas",
            ProgramDescription="Pietūs",
            About_Place="Kaunas",
        ),
        ProductInput(
            ProgramName="Viešbutis",
            ProgramDescription="Nakvynė",
            About_Place="Klaipėda",
        ),
    ]

    results = await categorize_batch_async(mock_client, products, "gpt-5-nano")

    # Wrap in gather check since gather return values might be wrapped
    assert len(results) == 3
    assert isinstance(results[0], CategoryOutput)
    assert results[0].category == "spa_wellness"
    assert isinstance(results[1], CategoryOutput)
    assert results[1].category == "restaurants_food"
    assert isinstance(results[2], CategoryOutput)
    assert results[2].category == "accommodation"


@pytest.mark.asyncio
async def test_categorize_batch_async_with_exceptions() -> None:
    """Test batch categorization handles exceptions gracefully."""
    mock_client = AsyncMock()

    def create_mock_response(category: str) -> Mock:
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({"category": category})
        return mock_response

    # First succeeds, second fails, third succeeds
    mock_client.chat.completions.create = AsyncMock(
        side_effect=[
            create_mock_response("spa_wellness"),
            ValueError("Test error"),
            create_mock_response("accommodation"),
        ]
    )

    products: list[ProductInput] = [
        ProductInput(ProgramName="SPA", ProgramDescription="Test", About_Place="Test"),
        ProductInput(
            ProgramName="Error",
            ProgramDescription="Test",
            About_Place="Test",
        ),
        ProductInput(
            ProgramName="Hotel",
            ProgramDescription="Test",
            About_Place="Test",
        ),
    ]

    results = await categorize_batch_async(mock_client, products, "gpt-5-nano")

    assert len(results) == 3
    assert isinstance(results[0], CategoryOutput)
    assert results[0].category == "spa_wellness"
    assert isinstance(results[1], CategoryOutput)
    assert results[1].category == "unknown"
    assert "Unexpected error" in results[1].comment
    assert isinstance(results[2], CategoryOutput)
    assert results[2].category == "accommodation"


@pytest.mark.asyncio
async def test_categorize_batch_async_empty_list() -> None:
    """Test batch categorization with empty product list."""
    mock_client = AsyncMock()

    results = await categorize_batch_async(mock_client, [], "gpt-5-nano")

    assert len(results) == 0
    mock_client.chat.completions.create.assert_not_called()
