import multiprocessing

import gunicorn.arbiter
import uvicorn_worker

from config import config as config_
from workers import offer_fetcher


def on_starting(_arbiter: gunicorn.arbiter.Arbiter) -> None:
    multiprocessing.Process(target=offer_fetcher.run, daemon=True).start()


bind = f'{config_.api_host}:{config_.api_port}'
preload_app = True
worker_class = uvicorn_worker.UvicornWorker
workers = 4
