"""Configuration management for Gift Voucher Categorizer."""

import json
from pathlib import Path

from loguru import logger
from openai import AsyncOpenAI, AuthenticationError
from pydantic import BaseModel, ValidationError

# Hardcoded batch size constants
# Tier 1 GPT-5 models allow 500 RPM (Requests Per Minute)
# Rate is limited by tokens also
# for GPT-5 nano 200,000 tokens per minute (TPM), for GPT-5 mini 500,000 TPM
# CSV batch size is selected to 50 rows, to read/write data in chunks while processing in progress
# And rate limits are limiting smooth execution
# More information on rate limits generally: https://platform.openai.com/docs/guides/rate-limits#page-top
# More information on limits personalized: https://platform.openai.com/settings/organization/limits
CSV_BATCH_SIZE = 50  # Rows to read per chunk
API_CONCURRENT_BATCH_SIZE = 50  # Number of concurrent API requests

# CSV configuration
ENCODINGS = ["utf-8", "cp1252", "latin1"]  # Encoding fallback order
REQUIRED_COLUMNS = ["ProgramName", "ProgramDescription", "About_Place"]  # Required CSV columns
LANGUAGE_SAMPLE_LINES = 10  # Number of lines to sample for language detection

LOG_LEVEL = "DEBUG"  # Default log level
RETRY_MIN_WAIT = 10  # RateLimit error minimum wait time in seconds
RETRY_MAX_WAIT = 30  # RateLimit error maximum wait time in seconds
RETRY_MAX_ATTEMPTS = 20  # Maximum number of retry attempts for RateLimitError

# User config
CONFIG_FILE_PATH = Path.home() / ".product_categorizer_config.json"

# Hardcoded available models list
AVAILABLE_MODELS = [
    "gpt-5-nano-2025-08-07",
    "gpt-5-mini-2025-08-07",
]


class Config(BaseModel):
    """Configuration structure for Gift Voucher Categorizer."""

    openai_api_key: str
    model_name: str


def load_config() -> Config | None:
    """Load configuration from file.

    Returns:
        Config if successful, None otherwise
    """
    if not CONFIG_FILE_PATH.exists():
        logger.debug(f"Config file not found at {CONFIG_FILE_PATH}")
        return None

    try:
        with CONFIG_FILE_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)

        # Parse and validate with Pydantic
        return Config(**data)
    except (json.JSONDecodeError, OSError, ValidationError) as e:
        logger.error(f"Failed to load config: {e}")
        return None


# Global active configuration instance
ACTIVE_CONFIG: Config = load_config() or Config(
    openai_api_key="", model_name="gpt-5-nano-2025-08-07"
)


async def save_config(config: Config) -> None:
    """Save and verify configuration.

    Args:
        config: Configuration to save

    Raises:
        OSError: If unable to write file
        ValueError: If API key is invalid
    """
    logger.debug(f"Saving config with model: '{config.model_name}'")

    # Verify API key before saving
    client = AsyncOpenAI(api_key=config.openai_api_key)
    try:
        # Perform a minimal call to list models, limit to 1 for efficiency
        await client.models.list()
    except AuthenticationError as e:
        msg = "Invalid API key provided. Please enter a correct OpenAI API key."
        logger.error(msg)
        raise ValueError(msg) from e

    try:
        config_dict = config.model_dump()
        with CONFIG_FILE_PATH.open("w", encoding="utf-8") as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)
        logger.info(f"Config saved to {CONFIG_FILE_PATH} with model '{config.model_name}'")

        # Mutate the global instance so all modules see the update
        ACTIVE_CONFIG.openai_api_key = config.openai_api_key
        ACTIVE_CONFIG.model_name = config.model_name
        logger.debug(f"Updated ACTIVE_CONFIG: model_name = '{ACTIVE_CONFIG.model_name}'")
    except OSError as e:
        logger.error(f"Failed to save config: {e}")
        raise
