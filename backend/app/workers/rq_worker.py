from redis import Redis
from rq import Connection, Queue, SimpleWorker
from rq.timeouts import TimerDeathPenalty
from app.core.config import settings

listen = ["default"]
redis_conn = Redis.from_url(settings.redis_url)

class WindowsSimpleWorker(SimpleWorker):
    # ✅ TimerDeathPenalty работи на Windows (не използва SIGALRM)
    death_penalty_class = TimerDeathPenalty

if __name__ == "__main__":
    with Connection(redis_conn):
        queues = [Queue(name) for name in listen]
        worker = WindowsSimpleWorker(queues)
        worker.work()