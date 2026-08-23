"""
ArbiX Application Entry Point.

Responsible for:
    - Loading configuration
    - Initializing application components
    - Starting the application
    - Handling graceful shutdown

Business logic belongs inside the individual modules.
"""

from __future__ import annotations

import asyncio
import logging
import signal
from types import FrameType

from config.settings import Settings


logger = logging.getLogger("arbix")


class ArbiXApplication:
    """
    Main ArbiX application coordinator.

    The application currently provides the foundation for connecting
    the market-data, arbitrage, risk, execution, and analytics layers.

    Actual exchange integrations and trading loops should be connected
    here only after their individual components have been tested.
    """

    def __init__(
        self,
        settings: Settings,
    ) -> None:
        self.settings = settings

        self._shutdown_event = asyncio.Event()
        self._running = False

    async def start(self) -> None:
        """
        Start the ArbiX application.
        """

        if self._running:
            logger.warning(
                "ArbiX is already running."
            )
            return

        self._running = True

        logger.info(
            "Starting ArbiX..."
        )

        logger.info(
            "Trading mode: %s",
            self.settings.trading_mode,
        )

        logger.info(
            "ArbiX started successfully."
        )

    async def run(self) -> None:
        """
        Run the main application lifecycle.

        The application remains alive until a shutdown signal is
        received.
        """

        await self.start()

        try:
            await self._shutdown_event.wait()

        finally:
            await self.shutdown()

    async def shutdown(self) -> None:
        """
        Gracefully shut down the application.
        """

        if not self._running:
            return

        logger.info(
            "Shutting down ArbiX..."
        )

        self._running = False

        logger.info(
            "ArbiX shutdown completed."
        )

    def request_shutdown(self) -> None:
        """
        Request graceful application shutdown.
        """

        if not self._shutdown_event.is_set():
            logger.info(
                "Shutdown requested."
            )

            self._shutdown_event.set()


def configure_logging(
    settings: Settings,
) -> None:
    """
    Configure application logging.

    Logging configuration is intentionally kept simple for now.
    A dedicated logging subsystem can be introduced later.
    """

    logging.basicConfig(
        level=getattr(
            logging,
            settings.log_level.upper(),
            logging.INFO,
        ),
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),
    )


def install_signal_handlers(
    application: ArbiXApplication,
) -> None:
    """
    Register operating-system signal handlers.

    Graceful shutdown is especially important for a trading system
    because active tasks should be stopped safely.
    """

    loop = asyncio.get_running_loop()

    def handle_signal(
        signum: int,
        frame: FrameType | None,
    ) -> None:
        logger.info(
            "Received shutdown signal: %s",
            signum,
        )

        application.request_shutdown()

    for signal_name in (
        "SIGINT",
        "SIGTERM",
    ):
        signal_value = getattr(
            signal,
            signal_name,
            None,
        )

        if signal_value is None:
            continue

        try:
            loop.add_signal_handler(
                signal_value,
                handle_signal,
                signal_value,
                None,
            )
        except NotImplementedError:
            # Windows may not support add_signal_handler
            # for all signal types.
            signal.signal(
                signal_value,
                handle_signal,
            )


def load_settings() -> Settings:
    """
    Load application configuration.

    Settings is responsible for reading and validating configuration.
    """

    return Settings()


async def async_main() -> None:
    """
    Asynchronous application entry point.
    """

    settings = load_settings()

    configure_logging(
        settings
    )

    application = ArbiXApplication(
        settings=settings,
    )

    install_signal_handlers(
        application
    )

    await application.run()


def main() -> None:
    """
    Synchronous application entry point.
    """

    try:
        asyncio.run(
            async_main()
        )

    except KeyboardInterrupt:
        logger.info(
            "ArbiX interrupted by user."
        )


if __name__ == "__main__":
    main()