import os
import csv

from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from tests import TEST_DATA
from tests.mock_requests import MockRequests
from zoo_keeper_server.zoo_keeper import Base, ZooKeeper

engine = create_engine("sqlite:///:memory:")


class TestSession(Session):
    _close_counts = []
    _commit_counts = []

    def __init__(self):
        super(TestSession, self).__init__(bind=engine)

    @classmethod
    def close_counts(cls):
        return len(cls._close_counts)

    @classmethod
    def commit_counts(cls):
        return len(cls._commit_counts)

    def close(self):
        self._close_counts.append(1)
        super(TestSession, self).close()

    def commit(self):
        self._commit_counts.append(1)
        super(TestSession, self).commit()

    @classmethod
    def reset_close_count(cls):
        cls._close_counts = []

    @classmethod
    def reset_commit_count(cls):
        cls._commit_counts = []


def load_csv(file_path):
    with open(file_path, 'r', newline='') as f:
        csv_reader = csv.reader(f, delimiter=',', quotechar='"', doublequote=True, skipinitialspace=True)
        raw = [row for row in csv_reader if row and not row[0].startswith('#')]
    return raw


def load_zoo_keeper(session):
    zoo_path = os.path.join(TEST_DATA, 'test_zoo_keeper_data.txt')
    lines = load_csv(zoo_path)
    keys = ['name', 'age', 'zoo_id', 'favorite_monkey_id', 'dream_monkey_id']
    with patch('zoo_keeper_server.zoo_service_request_handler.requests', MockRequests):
        for line in lines:
            kwargs = dict(zip(keys, line))
            new_kwargs = {key: _convert_value(value) for key, value in kwargs.items()}
            zoo_keeper = ZooKeeper(**new_kwargs)
            session.add(zoo_keeper)
    session.commit()


def _convert_value(value):
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return value


def create_empty_database(session):
    Base.metadata.create_all(engine)
    for zoo_keeper in session.query(ZooKeeper).all():
        session.delete(zoo_keeper)
    session.commit()


def create_all_test_data(session: Session):
    create_empty_database(session)
    load_zoo_keeper(session)


def create_simple_test_data(session: Session):
    create_empty_database(session)
    data = [
        {'name': 'a', 'age': 1, 'zoo_id': 1, 'favorite_monkey_id': 2, 'dream_monkey_id': 1},
        {'name': 'b', 'age': 2}
    ]
    for kwargs in data:
        keeper = ZooKeeper(**kwargs)
        session.add(keeper)
    session.commit()


if __name__ == '__main__':
    new_session = TestSession()
    create_all_test_data(new_session)
    all_zoo_keepers = new_session.query(ZooKeeper).all()

    from pprint import pprint
    pprint([zoo_keeper.to_dict() for zoo_keeper in all_zoo_keepers])
    new_session.close()
