"""OpenAI API client for product categorization."""

import asyncio
import json
from collections.abc import Callable

from loguru import logger
from openai import APIError, AsyncOpenAI, RateLimitError
from prompts.v1 import PROMPT_V1
from pydantic import BaseModel
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random,
)

from src.config import (
    API_CONCURRENT_BATCH_SIZE,
    RETRY_MAX_ATTEMPTS,
    RETRY_MAX_WAIT,
    RETRY_MIN_WAIT,
)


class ProductInput(BaseModel):
    """Input data for product categorization."""

    program_name: str
    program_description: str
    about_place: str


class CategoryOutput(BaseModel):
    """Output data for product categorization."""

    category: str
    comment: str


def build_categorization_prompt(product: ProductInput) -> str:
    """Build categorization prompt from template.

    Args:
        product: Product data to categorize

    Returns:
        Formatted prompt string
    """
    return (
        PROMPT_V1.replace("{{PRODUCT_NAME}}", product.program_name)
        .replace("{{PRODUCT_DESCRIPTION}}", product.program_description)
        .replace("{{PRODUCT_LOCATION}}", product.about_place)
    )


async def _categorize_product_internal(
    client: AsyncOpenAI, product: ProductInput, model: str
) -> CategoryOutput:
    prompt = build_categorization_prompt(product)

    response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )

    # Extract and parse the response
    content = response.choices[0].message.content
    if not content:
        msg = "Empty response from API"
        raise ValueError(msg)

    result = json.loads(content)
    category: str = str(result.get("category", "unknown"))
    comment: str = str(result.get("comment", "No comment was returned"))

    return CategoryOutput(category=category, comment=comment)


async def categorize_product_async(
    client: AsyncOpenAI,
    product: ProductInput,
    model: str,
    rate_limit_callback: Callable[[bool], None] | None = None,
) -> CategoryOutput:
    """Categorize a single product using OpenAI API.

    Args:
        client: AsyncOpenAI client
        product: Product data to categorize
        model: Model name
        rate_limit_callback: Optional callback(is_waiting) for rate limit status

    Returns:
        CategoryOutput (returns 'unknown' on failure)
    """

    def on_retry(_retry_state: object) -> None:
        """Called before sleeping due to rate limit."""
        if rate_limit_callback:
            rate_limit_callback(True)

    # Apply retry decorator to the internal function
    categorize_product_internal_with_retry = retry(
        stop=stop_after_attempt(RETRY_MAX_ATTEMPTS),
        wait=wait_random(min=RETRY_MIN_WAIT, max=RETRY_MAX_WAIT),
        retry=retry_if_exception_type(RateLimitError),
        before_sleep=on_retry,
        reraise=True,
    )(_categorize_product_internal)

    try:
        # Call the retrying function
        result = await categorize_product_internal_with_retry(client, product, model)
    except RateLimitError as e:
        if rate_limit_callback:
            rate_limit_callback(False)
        msg = f"Rate limit exceeded after {RETRY_MAX_ATTEMPTS} retries: {e}"
        logger.error(msg)
        return CategoryOutput(category="unknown", comment=msg)
    except APIError as e:
        msg = f"OpenAI API error: {e}"
        logger.error(msg)
        return CategoryOutput(category="unknown", comment=msg)
    except Exception as e:
        msg = f"Unexpected error during categorization: {e}"
        logger.error(msg)
        return CategoryOutput(category="unknown", comment=msg)
    else:
        # Signal end of waiting if callback exists
        if rate_limit_callback:
            rate_limit_callback(False)

        return result


async def categorize_batch_async(
    client: AsyncOpenAI,
    products: list[ProductInput],
    model: str,
    rate_limit_callback: Callable[[bool], None] | None = None,
) -> list[CategoryOutput]:
    """Categorize a batch of products with concurrent API calls.

    Args:
        client: AsyncOpenAI client
        products: Products to categorize
        model: Model name
        rate_limit_callback: Optional callback(is_waiting) for rate limit status

    Returns:
        List of CategoryOutput in same order as input
    """
    semaphore = asyncio.Semaphore(API_CONCURRENT_BATCH_SIZE)

    async def categorize_with_limit(product: ProductInput) -> CategoryOutput:
        async with semaphore:
            return await categorize_product_async(client, product, model, rate_limit_callback)

    # Create tasks for all products
    tasks = [categorize_with_limit(product) for product in products]

    # Execute all tasks concurrently (with semaphore limiting concurrency)
    results = await asyncio.gather(*tasks)
    return list(results)
