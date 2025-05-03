import redis

from persistence.base import PersistenceBackend


class RedisStore(PersistenceBackend):

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: str | None = None,
        prefix: str = "github_release_tracker",
    ) -> None:
        self.redis = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            ssl=True,
            decode_responses=False,
        )
        self.prefix = prefix

    def get_last_release(self, repo: str) -> str | None:
        key = f"{self.prefix}:{repo}"
        val = self.redis.get(key)
        # noinspection PyUnresolvedReferences
        return val.decode("utf-8") if val is not None else None

    def set_last_release(self, repo: str, tag: str) -> None:
        key = f"{self.prefix}:{repo}"
        self.redis.set(key, tag)

    def close(self) -> None:
        self.redis.close()
