import os

from waitress import serve

from wsgi import app


if __name__ == "__main__":
    serve(
        app,
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "5000")),
        threads=int(os.getenv("WAITRESS_THREADS", "8")),
        channel_timeout=int(os.getenv("WAITRESS_CHANNEL_TIMEOUT", "120")),
    )
