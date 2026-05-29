import pytest

from utils.event_bus import AsyncEventBus
from interface.event_type import EventType


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

async def _noop_handler(data: object) -> None:  # noqa: ARG001
    """async handler that does nothing."""


async def _raising_handler(data: object) -> None:  # noqa: ARG001
    """async handler that always raises."""
    raise ValueError("boom")


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def bus() -> AsyncEventBus:
    """provide a fresh, non-singleton AsyncEventBus for each test."""
    original = AsyncEventBus._instance

    AsyncEventBus._instance = None
    fresh = AsyncEventBus()

    yield fresh

    # restore the application-level singleton so other tests are unaffected
    AsyncEventBus._instance = original


# ---------------------------------------------------------------------------
# singleton
# ---------------------------------------------------------------------------

class TestAsyncEventBusSingleton:
    def test_async_event_bus_is_singleton_returns_same_instance(self) -> None:
        # arrange / act
        first = AsyncEventBus()
        second = AsyncEventBus()

        # assert
        assert first is second


# ---------------------------------------------------------------------------
# subscribe
# ---------------------------------------------------------------------------

class TestAsyncEventBusSubscribe:
    def test_subscribe_adds_handler_to_subscribers(self, bus: AsyncEventBus) -> None:
        # arrange / act
        bus.subscribe(EventType.INCOMING_TELEGRAM_MESSAGE, _noop_handler)

        # assert
        assert _noop_handler in bus._subscribers[EventType.INCOMING_TELEGRAM_MESSAGE]

    def test_subscribe_same_handler_twice_stores_it_once(self, bus: AsyncEventBus) -> None:
        # arrange
        bus.subscribe(EventType.INCOMING_TELEGRAM_MESSAGE, _noop_handler)

        # act
        bus.subscribe(EventType.INCOMING_TELEGRAM_MESSAGE, _noop_handler)

        # assert - set deduplication must keep only one entry
        assert len(bus._subscribers[EventType.INCOMING_TELEGRAM_MESSAGE]) == 1

    def test_subscribe_multiple_handlers_stores_all(self, bus: AsyncEventBus) -> None:
        # arrange
        async def handler_b(data: object) -> None: ...

        # act
        bus.subscribe(EventType.INCOMING_TELEGRAM_MESSAGE, _noop_handler)
        bus.subscribe(EventType.INCOMING_TELEGRAM_MESSAGE, handler_b)

        # assert
        assert len(bus._subscribers[EventType.INCOMING_TELEGRAM_MESSAGE]) == 2


# ---------------------------------------------------------------------------
# unsubscribe
# ---------------------------------------------------------------------------

class TestAsyncEventBusUnsubscribe:
    def test_unsubscribe_removes_handler_from_subscribers(self, bus: AsyncEventBus) -> None:
        # arrange
        bus.subscribe(EventType.INCOMING_TELEGRAM_MESSAGE, _noop_handler)

        # act
        bus.unsubscribe(EventType.INCOMING_TELEGRAM_MESSAGE, _noop_handler)

        # assert
        assert _noop_handler not in bus._subscribers.get(
            EventType.INCOMING_TELEGRAM_MESSAGE, set()
        )

    def test_unsubscribe_nonexistent_event_type_does_not_raise(
        self, bus: AsyncEventBus
    ) -> None:
        # arrange / act / assert - must be a no-op, not a KeyError
        bus.unsubscribe(EventType.INCOMING_TELEGRAM_MESSAGE, _noop_handler)

    def test_unsubscribe_nonexistent_handler_does_not_raise(
        self, bus: AsyncEventBus
    ) -> None:
        # arrange
        bus.subscribe(EventType.INCOMING_TELEGRAM_MESSAGE, _noop_handler)

        # act / assert - discarding a handler that was never added is safe
        async def other(data: object) -> None: ...
        bus.unsubscribe(EventType.INCOMING_TELEGRAM_MESSAGE, other)


# ---------------------------------------------------------------------------
# publish
# ---------------------------------------------------------------------------

class TestAsyncEventBusPublish:
    async def test_publish_calls_registered_handler_with_data(
        self, bus: AsyncEventBus
    ) -> None:
        # arrange
        received: list[object] = []

        async def capture(data: object) -> None:
            received.append(data)

        bus.subscribe(EventType.INCOMING_TELEGRAM_MESSAGE, capture)

        # act
        await bus.publish(EventType.INCOMING_TELEGRAM_MESSAGE, "payload")

        # assert
        assert received == ["payload"]

    async def test_publish_calls_all_registered_handlers(
        self, bus: AsyncEventBus
    ) -> None:
        # arrange
        calls: list[str] = []

        async def handler_a(data: object) -> None:
            calls.append("a")

        async def handler_b(data: object) -> None:
            calls.append("b")

        bus.subscribe(EventType.INCOMING_TELEGRAM_MESSAGE, handler_a)
        bus.subscribe(EventType.INCOMING_TELEGRAM_MESSAGE, handler_b)

        # act
        await bus.publish(EventType.INCOMING_TELEGRAM_MESSAGE, None)

        # assert
        assert sorted(calls) == ["a", "b"]

    async def test_publish_with_no_subscribers_does_not_raise(
        self, bus: AsyncEventBus
    ) -> None:
        # arrange / act / assert
        await bus.publish(EventType.INCOMING_TELEGRAM_MESSAGE, "data")

    async def test_publish_to_unknown_event_type_does_not_raise(
        self, bus: AsyncEventBus
    ) -> None:
        # arrange / act / assert
        await bus.publish(EventType.SEND_TELEGRAM_MESSAGE, "data")


# ---------------------------------------------------------------------------
# _safe_execute - fault isolation
# ---------------------------------------------------------------------------

class TestAsyncEventBusSafeExecute:
    async def test_safe_execute_logs_error_when_handler_raises(
        self, bus: AsyncEventBus, caplog: pytest.LogCaptureFixture
    ) -> None:
        # arrange
        import logging

        with caplog.at_level(logging.ERROR, logger="AsyncEventBus"):
            # act
            await bus._safe_execute(_raising_handler, None)

        # assert - error must be logged, not re-raised
        assert any("boom" in record.message for record in caplog.records)

    async def test_safe_execute_does_not_reraise_handler_exception(
        self, bus: AsyncEventBus
    ) -> None:
        # arrange / act / assert - must swallow the exception
        await bus._safe_execute(_raising_handler, None)

    async def test_publish_continues_remaining_handlers_after_one_fails(
        self, bus: AsyncEventBus
    ) -> None:
        # arrange
        completed: list[str] = []

        async def good_handler(data: object) -> None:
            completed.append("good")

        bus.subscribe(EventType.INCOMING_TELEGRAM_MESSAGE, _raising_handler)
        bus.subscribe(EventType.INCOMING_TELEGRAM_MESSAGE, good_handler)

        # act
        await bus.publish(EventType.INCOMING_TELEGRAM_MESSAGE, None)

        # assert - the good handler must still run despite the failing sibling
        assert "good" in completed
