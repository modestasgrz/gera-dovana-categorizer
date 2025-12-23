"""OpenAI API client for product categorization."""

import asyncio
import json

from loguru import logger
from openai import APIError, AsyncOpenAI, RateLimitError
from pydantic import BaseModel
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_random

from src.config import (
    API_CONCURRENT_BATCH_SIZE,
    PRODUCT_CATEGORIES,
    RETRY_MAX_ATTEMPTS,
    RETRY_MAX_WAIT,
    RETRY_MIN_WAIT,
)


class ProductInput(BaseModel):
    """Input data for product categorization."""

    ProgramName: str
    ProgramDescription: str
    About_Place: str


class CategoryOutput(BaseModel):
    """Output data for product categorization."""

    category: str
    comment: str


# TODO: Build this later with Prompt Engineering task - NO NEED TO IMPLEMENT THIS TODO
def build_categorization_prompt(product: ProductInput) -> str:
    """Build tree-of-thought categorization prompt with Lithuanian examples.

    Args:
        product: Product data to categorize

    Returns:
        Formatted prompt string
    """
    categories_description = "\n".join(
        [
            "- spa_wellness: SPA, sveikatingumo centrai, masažai, wellness procedūros",
            "- accommodation: Viešbučiai, apgyvendinimas, nakvynė, poilsio namai",
            "- travel_tourism: Kelionės, ekskursijos, turizmas, kelionių agentūros",
            "- sports_fitness: Sporto klubai, fitnesas, treniruoklių salės, aktyvus poilsis",
            "- beauty_cosmetics: Grožio klinikos, kosmetika, kirpyklos, grožio procedūros",
            "- restaurants_food: Restoranai, kavinės, maistas, pietūs, vakarienės, kulinarija",
            "- entertainment: Pramogos, renginiai, šou, spektakliai, koncertai, teatro pasirodymai",
            "- adventure_activities: Rally taksi, balionu, ekstremalios pramogos",
            "- shopping_retail: Parduotuvių čekiai, apsipirkimas, dovanų kuponai",
            "- medical_health: Medicinos centrai, sveikata, sveikatos patikrinimai",
            "- education_workshops: Kursai, seminarai, dirbtuvės, mokymai, edukacija, pamokos",
            "- unknown: Nežinoma kategorija arba nepakanka informacijos klasifikavimui",
        ]
    )

    return f"""Tu esi ekspertas Lietuviškų dovanų kuponų ir paslaugų kategorizavime.

Kategorijos:
{categories_description}

Analizuok šią paslaugą ir pasirink VIENĄ tinkamiausią kategoriją:

Pavadinimas: {product.ProgramName}
Aprašymas: {product.ProgramDescription}
Vieta: {product.About_Place}

Pagalvok žingsnis po žingsnio:
1. Kokio tipo paslauga ar produktas tai yra?
2. Kuri kategorija geriausiai atitinka?
3. Jei neaišku arba nepakanka informacijos, grąžink "unknown"

Grąžink TIK kategorijos pavadinimą JSON formatu: {{"category": "kategorijos_pavadinimas"}}"""


@retry(
    stop=stop_after_attempt(RETRY_MAX_ATTEMPTS),
    wait=wait_random(min=RETRY_MIN_WAIT, max=RETRY_MAX_WAIT),
    retry=retry_if_exception_type(RateLimitError),
    reraise=True,
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
    category: str = result.get("category", "unknown")

    # Comment on unknown return
    if "unknown" in category.lower().strip():
        return CategoryOutput(category="unknown", comment="Model failed to assign a category")

    # Validate category is in our predefined list
    if category not in PRODUCT_CATEGORIES:
        return CategoryOutput(category="unknown", comment="Invalid category returned by model")
    return CategoryOutput(category=category, comment="")


async def categorize_product_async(
    client: AsyncOpenAI, product: ProductInput, model: str
) -> CategoryOutput:
    """Categorize a single product using OpenAI API asynchronously.

    Returns CategoryOutput with 'unknown' category on failure.

    Args:
        client: AsyncOpenAI client instance
        product: Product data to categorize
        model: OpenAI model name to use

    Returns:
        CategoryOutput with category and optional comment
    """
    try:
        return await _categorize_product_internal(client, product, model)
    except RateLimitError as e:
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


async def categorize_batch_async(
    client: AsyncOpenAI, products: list[ProductInput], model: str
) -> list[CategoryOutput]:
    """Categorize a batch of products with concurrent API calls.

    Uses a semaphore to limit concurrent API requests to API_CONCURRENT_BATCH_SIZE.

    Args:
        client: AsyncOpenAI client instance
        products: List of ProductInput objects to categorize
        model: OpenAI model name

    Returns:
        List of CategoryOutput objects in the same order as input products
    """
    semaphore = asyncio.Semaphore(API_CONCURRENT_BATCH_SIZE)

    async def categorize_with_limit(product: ProductInput) -> CategoryOutput:
        async with semaphore:
            return await categorize_product_async(client, product, model)

    # Create tasks for all products
    tasks = [categorize_with_limit(product) for product in products]

    # Execute all tasks concurrently (with semaphore limiting concurrency)
    results = await asyncio.gather(*tasks)
    return list(results)
