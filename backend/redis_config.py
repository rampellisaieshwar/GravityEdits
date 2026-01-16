import os
import redis
from rq import Queue

# Configure Redis connection
# Fallback to localhost if not set
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')

try:
    redis_conn = redis.from_url(REDIS_URL)
    # Ping to check connection
    redis_conn.ping()
except Exception as e:
    print(f"Warning: Redis connection failed: {e}")
    redis_conn = None

# Create Queues
# We can have different queues for priority (e.g. 'high', 'default', 'low')
if redis_conn:
    q_default = Queue('default', connection=redis_conn)
    q_analysis = Queue('analysis', connection=redis_conn)
    q_render = Queue('render', connection=redis_conn)
    q_videodb = Queue('videodb', connection=redis_conn)
else:
    q_default = None
    q_analysis = None
    q_render = None
    q_videodb = None
