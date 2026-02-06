import multiprocessing

import gunicorn.arbiter
import uvicorn_worker

from workers import offer_fetcher


def on_starting(_arbiter: gunicorn.arbiter.Arbiter) -> None:
    multiprocessing.Process(target=offer_fetcher.run, daemon=True).start()


bind = '0.0.0.0:5211'
preload_app = True
worker_class = uvicorn_worker.UvicornWorker
workers = 4
