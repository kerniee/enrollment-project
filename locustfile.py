import logging
import uuid
from random import randint, choice, shuffle
from urllib import parse

from faker import Faker
from locust import HttpUser, TaskSet, constant, task
from locust.exception import RescheduleTask

fake = Faker()


def create_unit(parent_id=None):
    return {
        "name": fake.name(),
        "id": str(uuid.uuid4()),
        "parentId": parent_id,
    }


def create_item(parent_id=None):
    item = create_unit(parent_id)
    item["type"] = "OFFER"
    item["price"] = randint(99, 9999) * 10 + 9
    return item


def create_category(parent_id=None):
    item = create_unit(parent_id)
    item["type"] = "CATEGORY"
    return item


class MarketTaskSet(TaskSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dataset = None
        self.first_category = None
        self.round = 0

    def make_dataset(self, size=100, categories_size=50):
        first_category = create_category()
        dataset = [first_category]
        category_ids = [first_category["id"]]
        for i in range(categories_size - 1):
            random_parent_id = choice(category_ids)
            category = create_category(random_parent_id)
            dataset.append(category)
            category_ids.append(category["id"])
        for _ in range(size - categories_size):
            random_parent_id = choice(category_ids)
            item = create_item(random_parent_id)
            dataset.append(item)
        shuffle(dataset)
        return first_category["id"], dataset

    def request(self, method, path, expected_status, **kwargs):
        with self.client.request(
                method, path, catch_response=True, **kwargs
        ) as resp:
            if resp.status_code != expected_status:
                resp.failure(f'expected status {expected_status}, '
                             f'got {resp.status_code}')
            logging.info(
                'round %r: %s %s, http status %d (expected %d), took %rs',
                self.round, method, path, resp.status_code, expected_status,
                resp.elapsed.total_seconds()
            )
            return resp

    def create_import(self, dataset):
        resp = self.request('POST', 'imports', 200,
                            json={'items': dataset, "updateDate": "2022-05-28T00:00:00.000Z"})
        if resp.status_code != 200:
            raise RescheduleTask

    def get_node(self, unit_id):
        url = f"nodes/{unit_id}"
        resp = self.request('GET', url, 200, name="nodes/{id}")
        # print(resp.json())

    def delete(self, unit_id):
        url = f"delete/{unit_id}"
        self.request('DELETE', url, 200, name="delete/{id}")

    def get_sales(self):
        url = "sales"
        url += "?date=" + parse.quote_plus("2022-05-28T01:00:00.000Z")
        self.request('GET', url, 200, name="sales")

    def get_statistics(self, unit_id):
        url = f"node/{unit_id}/statistic"
        url += "?dateStart=" + parse.quote_plus("2022-05-27T01:00:00.000Z")
        url += "&dateEnd=" + parse.quote_plus("2022-05-28T01:00:00.000Z")
        resp = self.request('GET', url, 200, name="node/{id}/statistic")
        # print(resp.json())
    
    def on_start(self):
        first_category, dataset = self.make_dataset()
        self.create_import(dataset)
        self.first_category = first_category
        self.dataset = dataset

    @task
    def node(self):
        item = choice(self.dataset)
        self.get_node(item["id"])

    @task
    def sales(self):
        self.get_sales()

    @task
    def statistics(self):
        item = choice(self.dataset)
        self.get_statistics(item["id"])

    @task
    def task_delete(self):
        item = choice(self.dataset)
        self.delete(item["id"])


class WebsiteUser(HttpUser):
    tasks = {MarketTaskSet}
    wait_time = constant(0.001)
