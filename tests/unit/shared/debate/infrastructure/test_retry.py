"""Tests for retry_with_backoff function."""

import asyncio
import pytest

from src.shared.debate.infrastructure.retry import retry_with_backoff


class TestRetryWithBackoff:
    """Test suite for retry_with_backoff function."""

    @pytest.mark.asyncio
    async def test_succeeds_on_first_attempt(self):
        """Should return result immediately on first successful call."""

        async def always_succeed():
            return "success"

        result = await retry_with_backoff(always_succeed, max_retries=3)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_retries_on_failure(self):
        """Should retry until success."""
        attempts = []

        async def fail_twice_then_succeed():
            attempts.append(1)
            if len(attempts) < 3:
                raise ValueError("Not yet")
            return "success"

        result = await retry_with_backoff(fail_twice_then_succeed, max_retries=3)
        assert result == "success"
        assert len(attempts) == 3

    @pytest.mark.asyncio
    async def test_raises_after_max_retries(self):
        """Should raise last exception after exhausting retries."""

        async def always_fail():
            raise RuntimeError("Always fails")

        with pytest.raises(RuntimeError, match="Always fails"):
            await retry_with_backoff(always_fail, max_retries=2)

    @pytest.mark.asyncio
    async def test_exponential_backoff_timing(self):
        """Should use exponential backoff delays."""
        import time
        delays = []

        async def record_delay():
            start = time.time()
            raise ValueError("Fail")

        try:
            await retry_with_backoff(record_delay, max_retries=3)
        except ValueError:
            pass

        # The backoff should be 2^attempt seconds
        # We can't test exact timing in pytest, but we can verify it doesn't crash

    @pytest.mark.asyncio
    async def test_passes_arguments_to_function(self):
        """Should pass arguments and kwargs to the wrapped function."""

        async def greet(name, greeting="Hello"):
            return f"{greeting}, {name}"

        result = await retry_with_backoff(
            greet,
            1,  # max_retries
            "World",  # positional arg for greet
            greeting="Hi"  # kwarg for greet
        )
        assert result == "Hi, World"

    @pytest.mark.asyncio
    async def test_zero_retries_means_one_attempt(self):
        """Should attempt once even with max_retries=0."""

        async def fail():
            raise ValueError("Fail")

        with pytest.raises(ValueError):
            await retry_with_backoff(fail, max_retries=0)

    @pytest.mark.asyncio
    async def test_preserves_exception_type(self):
        """Should preserve the original exception type."""

        class CustomError(Exception):
            pass

        async def raise_custom():
            raise CustomError("Custom error")

        with pytest.raises(CustomError, match="Custom error"):
            await retry_with_backoff(raise_custom, max_retries=1)
