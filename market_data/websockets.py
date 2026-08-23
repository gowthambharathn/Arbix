"""
ArbiX WebSocket Infrastructure

Provides a reusable asynchronous WebSocket abstraction for real-time
market-data communication.

Exchange-specific WebSocket implementations should build on top of
this layer rather than placing exchange-specific logic here.
"""

from __future__ import annotations

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any

try:
    import websockets
    from websockets.asyncio.client import ClientConnection
except ImportError:  # pragma: no cover
    websockets = None
    ClientConnection = Any


logger = logging.getLogger(__name__)


class WebSocketError(Exception):
    """Base exception for WebSocket-related errors."""


class WebSocketConnectionError(WebSocketError):
    """Raised when a WebSocket connection cannot be established."""


class WebSocketMessageError(WebSocketError):
    """Raised when a WebSocket message cannot be processed."""


class BaseWebSocketClient(ABC):
    """
    Abstract asynchronous WebSocket client.

    Responsibilities:
        - Establish a WebSocket connection.
        - Receive messages.
        - Send messages.
        - Handle connection lifecycle.
        - Provide reconnect support.

    This class intentionally contains no exchange-specific protocol logic.
    """

    def __init__(
        self,
        url: str,
        reconnect_delay: float = 5.0,
        max_reconnect_attempts: int = 5,
    ) -> None:
        if not url:
            raise ValueError("WebSocket URL cannot be empty.")

        if reconnect_delay < 0:
            raise ValueError(
                "Reconnect delay cannot be negative."
            )

        if max_reconnect_attempts < 0:
            raise ValueError(
                "Maximum reconnect attempts cannot be negative."
            )

        self.url = url
        self.reconnect_delay = reconnect_delay
        self.max_reconnect_attempts = max_reconnect_attempts

        self._connection: ClientConnection | None = None
        self._closed = False

    @property
    def is_connected(self) -> bool:
        """Return whether the WebSocket connection is currently active."""

        return self._connection is not None

    async def connect(self) -> None:
        """
        Establish the WebSocket connection.

        Raises:
            WebSocketConnectionError:
                If the connection cannot be established.
        """

        if self._closed:
            raise WebSocketConnectionError(
                "Cannot connect a closed WebSocket client."
            )

        if websockets is None:
            raise WebSocketConnectionError(
                "The 'websockets' package is not installed."
            )

        if self.is_connected:
            return

        try:
            logger.info(
                "Connecting to WebSocket: %s",
                self.url,
            )

            self._connection = await websockets.connect(
                self.url,
                ping_interval=20,
                ping_timeout=20,
                close_timeout=10,
            )

            logger.info(
                "WebSocket connected: %s",
                self.url,
            )

        except Exception as error:
            self._connection = None

            logger.error(
                "Failed to connect to WebSocket %s: %s",
                self.url,
                error,
            )

            raise WebSocketConnectionError(
                f"Failed to connect to {self.url}."
            ) from error

    async def disconnect(self) -> None:
        """Close the active WebSocket connection."""

        self._closed = True

        if self._connection is None:
            return

        try:
            await self._connection.close()
        finally:
            self._connection = None

        logger.info(
            "WebSocket disconnected: %s",
            self.url,
        )

    async def send(self, message: dict[str, Any]) -> None:
        """
        Send a JSON message through the WebSocket.

        Args:
            message: JSON-serializable message.

        Raises:
            WebSocketConnectionError:
                If no connection is available.
            WebSocketMessageError:
                If the message cannot be serialized.
        """

        if self._connection is None:
            raise WebSocketConnectionError(
                "WebSocket is not connected."
            )

        try:
            payload = json.dumps(message)
        except (TypeError, ValueError) as error:
            raise WebSocketMessageError(
                "Failed to serialize WebSocket message."
            ) from error

        try:
            await self._connection.send(payload)
        except Exception as error:
            self._connection = None

            raise WebSocketConnectionError(
                "Failed to send WebSocket message."
            ) from error

    async def receive(self) -> dict[str, Any]:
        """
        Receive and decode one JSON message.

        Returns:
            Decoded JSON object.

        Raises:
            WebSocketConnectionError:
                If the connection is unavailable.
            WebSocketMessageError:
                If the received message is invalid JSON.
        """

        if self._connection is None:
            raise WebSocketConnectionError(
                "WebSocket is not connected."
            )

        try:
            raw_message = await self._connection.recv()
        except Exception as error:
            self._connection = None

            raise WebSocketConnectionError(
                "Failed to receive WebSocket message."
            ) from error

        if isinstance(raw_message, bytes):
            raw_message = raw_message.decode("utf-8")

        try:
            message = json.loads(raw_message)
        except (json.JSONDecodeError, TypeError) as error:
            raise WebSocketMessageError(
                "Received invalid JSON from WebSocket."
            ) from error

        if not isinstance(message, dict):
            raise WebSocketMessageError(
                "WebSocket message must be a JSON object."
            )

        return message

    async def messages(self) -> AsyncIterator[dict[str, Any]]:
        """
        Continuously yield incoming WebSocket messages.

        The connection is automatically established if necessary.
        """

        if self._closed:
            raise WebSocketConnectionError(
                "WebSocket client is closed."
            )

        if not self.is_connected:
            await self.connect()

        while not self._closed:
            try:
                yield await self.receive()

            except WebSocketConnectionError:
                if self._closed:
                    break

                logger.warning(
                    "WebSocket connection lost: %s",
                    self.url,
                )

                await self._reconnect()

    async def _reconnect(self) -> None:
        """Attempt to reconnect to the WebSocket server."""

        for attempt in range(1, self.max_reconnect_attempts + 1):
            if self._closed:
                return

            logger.warning(
                "WebSocket reconnect attempt %d/%d: %s",
                attempt,
                self.max_reconnect_attempts,
                self.url,
            )

            if self.reconnect_delay > 0:
                await asyncio.sleep(self.reconnect_delay)

            try:
                await self.connect()

                logger.info(
                    "WebSocket successfully reconnected: %s",
                    self.url,
                )

                return

            except WebSocketConnectionError:
                continue

        raise WebSocketConnectionError(
            f"Unable to reconnect to {self.url} after "
            f"{self.max_reconnect_attempts} attempts."
        )

    async def subscribe(
        self,
        subscription: dict[str, Any],
    ) -> None:
        """
        Send a subscription message.

        Exchange-specific clients can override this method when their
        subscription protocol requires custom behavior.

        Args:
            subscription: Exchange-specific subscription payload.
        """

        await self.send(subscription)

    @abstractmethod
    async def handle_message(
        self,
        message: dict[str, Any],
    ) -> Any:
        """
        Process an exchange-specific WebSocket message.

        Concrete implementations must normalize exchange-specific
        messages into ArbiX domain models.
        """

    async def run(self) -> AsyncIterator[Any]:
        """
        Connect, receive, and process WebSocket messages continuously.

        Yields:
            Processed exchange-specific messages.
        """

        async for message in self.messages():
            try:
                result = await self.handle_message(message)

                if result is not None:
                    yield result

            except WebSocketMessageError:
                logger.exception(
                    "Failed to process WebSocket message."
                )

    async def __aenter__(self) -> BaseWebSocketClient:
        """Enter asynchronous context."""

        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: Any,
    ) -> None:
        """Exit asynchronous context and close the connection."""

        await self.disconnect()


class ExchangeWebSocketClient(BaseWebSocketClient):
    """
    Generic exchange WebSocket client.

    This class can be extended by individual exchange integrations.

    Example:

        class BinanceWebSocketClient(ExchangeWebSocketClient):
            async def handle_message(self, message):
                ...
    """

    def __init__(
        self,
        exchange_name: str,
        url: str,
        reconnect_delay: float = 5.0,
        max_reconnect_attempts: int = 5,
    ) -> None:
        super().__init__(
            url=url,
            reconnect_delay=reconnect_delay,
            max_reconnect_attempts=max_reconnect_attempts,
        )

        if not exchange_name:
            raise ValueError(
                "Exchange name cannot be empty."
            )

        self.exchange_name = exchange_name

    async def handle_message(
        self,
        message: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Return the raw exchange message.

        Concrete exchange clients should override this method and
        convert the response into ArbiX domain models.
        """

        return message