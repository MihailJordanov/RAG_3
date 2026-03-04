from redis import Redis
from rq import Connection, Queue, SimpleWorker
from rq.timeouts import TimerDeathPenalty
from app.core.config import settings

LISTEN_QUEUES = ["default"]
redis_conn = Redis.from_url(settings.redis_url)

class WindowsSimpleWorker(SimpleWorker):
    """RQ worker for Windows (no SIGALRM)."""
    death_penalty_class = TimerDeathPenalty

def main() -> None:
    with Connection(redis_conn):
        queues = [Queue(name) for name in LISTEN_QUEUES]
        worker = WindowsSimpleWorker(queues)
        worker.work()

if __name__ == "__main__":
    main()