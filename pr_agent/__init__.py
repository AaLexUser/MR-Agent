import typer
from typing import Annotated, Optional, List
from dataclasses import dataclass
import time
from contextlib import contextmanager
from pr_agent.log import get_logger
from pr_agent.utils import load_config
from pr_agent.git_providers import get_git_provider
from rich import print as rprint

logger = get_logger()


@dataclass
class TimingContext:
    start_time: float

    @property
    def time_elapsed(self) -> float:
        return time.time() - self.start_time


@contextmanager
def time_block(description: str, timer: TimingContext):
    """Context manager for timing code blocks and logging the duration."""
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        logger.info(f"It took {duration:.2f} seconds {description}. ")


def run_review(
    pr_url: str,
    config_path: Annotated[
        Optional[str],
        typer.Option(
            "--config-path", "-c", help="Path to the configuration file (config.yaml)"
        ),
    ] = None,
    config_overrides: Annotated[
        Optional[List[str]],
        typer.Option(
            "--config_overrides",
            "-o",
            help="Override config values. Format: key=value or key.nested=value. Can be used multiple times.",
        ),
    ] = None,
    author: Annotated[
        Optional[str],
        typer.Option("--author", "-a", help="Filter PRs by author"),
    ] = None,
):
    start_time = time.time()
    logger.info(f"Starting review of PR {pr_url}")
    try:
        config = load_config(config_path=config_path, overrides=config_overrides)
        logger.info("Successfully loaded config")
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        raise

    timer = TimingContext(start_time=start_time)
    # TODO: get all closed PRs in the period by author ... and repo ...
    for pr_url in pr_urls:
    with time_block("Fetching PR files", timer):
        git_provider = get_git_provider(
            config.git_provider.name,
            pr_url,
            config.git_provider.include,
            config.git_provider.exclude,
        )  # type: ignore
        rprint("[green]PR loaded![/green]")
        # TODO: get diff files in PR
        diff_files = git_provider.get_diff_files()
        # TODO: process diff files

def main():
    app = typer.Typer()
    app.command()(run_review)
    app()


if __name__ == "__main__":
    main()
