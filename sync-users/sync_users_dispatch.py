import os
import sys
import sqlite3
import requests
from contextlib import closing
from dataclasses import dataclass
from dispatch import Registry


FILE = "users.db"
BATCH_SIZE = 10


endpoint = os.getenv("DISPATCH_ENDPOINT_URL")
if not endpoint:
    print(f"error: DISPATCH_ENDPOINT_URL not set")
    exit(1)


dispatch = Registry(endpoint)


@dataclass
class User:
    id: int
    first_name: str
    last_name: str
    address: str
    email: str


def export_users_to_salesforce(db, instance_url, access_token):
    with closing(db.cursor()) as cursor:
        cursor.execute("SELECT id, first_name, last_name, address, email FROM users")
        batch = dispatch.client.batch()
        for row in cursor:
            batch.add(send_user_to_salesforce, User(*row), instance_url, access_token)
            if len(batch.calls) == BATCH_SIZE:
                batch.dispatch()
        if len(batch.calls) > 0:
            batch.dispatch()


@dispatch.function
def send_user_to_salesforce(user, instance_url, access_token): ...


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"error: {sys.argv[0]} <URL> <TOKEN>")
        exit(1)

    _, instance_url, access_token = sys.argv

    db = sqlite3.connect(FILE)
    try:
        with db:
            export_users_to_salesforce(db, instance_url, access_token)
    except KeyboardInterrupt:
        pass
    finally:
        db.close()
