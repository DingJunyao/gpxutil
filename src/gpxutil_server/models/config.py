from dataclasses import dataclass


@dataclass
class MongoDbConfig:
    host: str
    port: int
    username: str
    password: str
    db: str

@dataclass
class RedisConfig:
    host: str
    port: int
    password: str
    db: int

@dataclass
class Config:
    mongodb: MongoDbConfig
    redis: RedisConfig