# encoding=utf8

import json
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

API_BASEURL = "http://localhost:80"

ROOT_ID = "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1"
DELETE_ID = "74b81fda-9cdc-4b63-8927-c978afed5cf4"
EDIT_IMPORT = {
    "items": [
        {
            "type": "OFFER",
            "name": "Xomiа Readme 10",
            "id": "b1d8fd7d-2ae3-47d5-b2f9-0f094af800d4",
            "parentId": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1",  # 069cb8d7-bbdd-47d3-ad8f-82ef4c269df1
            "price": 59999
        }
    ],
    "updateDate": "2022-02-04T00:00:00.000Z"
}

EDIT_IMPORT_CATEGORY = {
    "items": [
        {
            "type": "CATEGORY",
            "name": "Телевизоры",
            "id": "1cc0129a-2bfe-474c-9ee6-d435bf5fc8f2",
            "parentId": "d515e43f-f3f6-4471-bb77-6b455017a2d2",
                # before   069cb8d7-bbdd-47d3-ad8f-82ef4c269df1
                # after    d515e43f-f3f6-4471-bb77-6b455017a2d2

        }
    ],
    "updateDate": "2022-02-04T01:00:00.000Z"
}

IMPORT_BATCHES_WRONG = [
    {
        "items": [
            {
                "type": "CATEGORY",
                "name": "Товары",
                "id": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1",
                "parentId": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df2"
            }
        ],
        "updateDate": "2022-02-01T12:00:00.000Z"
    },
    {
        "items": [
            {
                "type": "CATEGORY",
                "name": "Товары",
                "id": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1",
                "parentId": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1"
            }
        ],
        "updateDate": "2022-02-01T12:00:00.000Z"
    },
    {
        "items": [
            {
                "type": "CATEGORY",
                "name": "Товары",
                "id": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1",
                "parentId": None
            }
        ]
    },
    {
        "items": [
            {
                "type": "SOME_VALUE",
                "name": "Товары",
                "id": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1",
                "parentId": None
            }
        ],
        "updateDate": "2022-02-01T12:00:00.000Z"
    },
    {
        "items": [
            {
                "type": "CATEGORY",
                "name": "Товары",
                "id": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1",
                "parentId": None
            },
            {}
        ],
        "updateDate": "2022-02-01T12:00:00.000Z"
    },
    {
        "items": [
            {
                "type": "CATEGORY",
                "name": "Товары",
                "id": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1",
                "price": 123,
                "parentId": None
            }
        ],
        "updateDate": "2022-02-01T12:00:00.000Z"
    },
    {
        "items": [
            {
                "type": "CATEGORY",
                "name": "Товары",
                "id": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1",
                "parentId": None
            },
            {
                "type": "CATEGORY",
                "name": "Не товары",
                "id": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1",
                "parentId": None
            }
        ],
        "updateDate": "2022-02-01T12:00:00.000Z"
    },
]

IMPORT_BATCHES = [
    {
        "items": [
            {
                "type": "CATEGORY",
                "name": "Товары",
                "id": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1",
                "parentId": None
            }
        ],
        "updateDate": "2022-02-01T12:00:00.000Z"
    },
    {
        "items": [
            {
                "type": "CATEGORY",
                "name": "Смартфоны",
                "id": "d515e43f-f3f6-4471-bb77-6b455017a2d2",
                "parentId": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1"
            },
            {
                "type": "OFFER",
                "name": "jPhone 13",
                "id": "863e1a7a-1304-42ae-943b-179184c077e3",
                "parentId": "d515e43f-f3f6-4471-bb77-6b455017a2d2",
                "price": 79999
            },
            {
                "type": "OFFER",
                "name": "Xomiа Readme 10",
                "id": "b1d8fd7d-2ae3-47d5-b2f9-0f094af800d4",
                "parentId": "d515e43f-f3f6-4471-bb77-6b455017a2d2",  # 069cb8d7-bbdd-47d3-ad8f-82ef4c269df1
                "price": 59999
            }
        ],
        "updateDate": "2022-02-02T12:00:00.000Z"
    },
    {
        "items": [
            {
                "type": "CATEGORY",
                "name": "Телевизоры",
                "id": "1cc0129a-2bfe-474c-9ee6-d435bf5fc8f2",
                "parentId": "069cb8d7-bbdd-47d3-ad8f-82ef4c269df1"
            },
            {
                "type": "OFFER",
                "name": "Samson 70\" LED UHD Smart",
                "id": "98883e8f-0507-482f-bce2-2fb306cf6483",
                "parentId": "1cc0129a-2bfe-474c-9ee6-d435bf5fc8f2",
                "price": 32999
            },
            {
                "type": "OFFER",
                "name": "Phyllis 50\" LED UHD Smarter",
                "id": "74b81fda-9cdc-4b63-8927-c978afed5cf4",
                "parentId": "1cc0129a-2bfe-474c-9ee6-d435bf5fc8f2",
                "price": 49999
            }
        ],
        "updateDate": "2022-02-03T12:00:00.000Z"
    },
    {
        "items": [
            {
                "type": "OFFER",
                "name": "Goldstar 65\" LED UHD LOL Very Cool",
                "id": "73bc3b36-02d1-4245-ab35-3106c9ee1c65",
                "parentId": "1cc0129a-2bfe-474c-9ee6-d435bf5fc8f2",
                "price": 59999
            }
        ],
        "updateDate": "2022-02-03T14:00:00.000Z"
    },
    {
        "items": [
            {
                "type": "OFFER",
                "name": "Goldstar 65\" LED UHD LOL Very Smart",
                "id": "73bc3b36-02d1-4245-ab35-3106c9ee1c65",
                "parentId": "1cc0129a-2bfe-474c-9ee6-d435bf5fc8f2",
                "price": 69999
            }
        ],
        "updateDate": "2022-02-03T15:00:00.000Z"
    },
    # {
    #     "items": [
    #         {
    #             "type": "OFFER",
    #             "name": "Goldstar 65\" LED UHD LOL Very Smart",
    #             "id": "73bc3b36-02d1-4245-ab35-3106c9ee1c65",
    #             "parentId": "1cc0129a-2bfe-474c-9ee6-d435bf5fc8f2",
    #             "price": 39999
    #         }
    #     ],
    #     "updateDate": "2022-02-03T15:00:00.000Z"
    # }
]

with open("data/test_01_import.json") as f:
    EXPECTED_TREE = json.load(f)


def request(path, method="GET", data=None, json_response=False):
    try:
        params = {
            "url": f"{API_BASEURL}{path}",
            "method": method,
            "headers": {},
        }

        if data:
            params["data"] = json.dumps(
                data, ensure_ascii=False).encode("utf-8")
            params["headers"]["Content-Length"] = len(params["data"])
            params["headers"]["Content-Type"] = "application/json"

        req = urllib.request.Request(**params)

        with urllib.request.urlopen(req) as res:
            res_data = res.read().decode("utf-8")
            if json_response:
                res_data = json.loads(res_data)
            return (res.getcode(), res_data)
    except urllib.error.HTTPError as e:
        return (e.getcode(), None)


def deep_sort_children(node):
    if node.get("children"):
        node["children"].sort(key=lambda x: x["id"])

        for child in node["children"]:
            deep_sort_children(child)


def print_diff(expected, response):
    with open("expected.json", "w") as f:
        json.dump(expected, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")

    with open("response.json", "w") as f:
        json.dump(response, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")

    subprocess.run(["git", "--no-pager", "diff", "--no-index",
                    "expected.json", "response.json"])


def test_import():
    for index, batch in enumerate(IMPORT_BATCHES):
        print(f"Importing batch {index}")
        status, _ = request("/imports", method="POST", data=batch)

        assert status == 200, f"Expected HTTP status code 200, got {status}"

    print("Test import passed.")


def test_import_400():
    for index, batch in enumerate(IMPORT_BATCHES_WRONG):
        print(f"Importing batch {index}")
        status, _ = request("/imports", method="POST", data=batch)

        assert status == 400, f"Expected HTTP status code 400, got {status}"

    print("Test import 400 passed.")


def test_nodes():
    status, response = request(f"/nodes/{ROOT_ID}", json_response=True)
    # print(json.dumps(response, indent=2, ensure_ascii=False))

    assert status == 200, f"Expected HTTP status code 200, got {status}"

    deep_sort_children(response)
    deep_sort_children(EXPECTED_TREE)
    if response != EXPECTED_TREE:
        print_diff(EXPECTED_TREE, response)
        print("Response tree doesn't match expected tree.")
        sys.exit(1)

    print("Test nodes passed.")


def test_nodes_after_deletion():
    status, response = request(f"/nodes/{ROOT_ID}", json_response=True)
    # print(json.dumps(response, indent=2, ensure_ascii=False))

    assert status == 404, f"Expected HTTP status code 200, got {status}"

    print("Test nodes after deletion passed.")


def test_sales():
    params = urllib.parse.urlencode({
        "date": "2022-02-04T00:00:00.000Z"
    })
    status, response = request(f"/sales?{params}", json_response=True)
    assert status == 200, f"Expected HTTP status code 200, got {status}"
    print("Test sales passed.")


def test_stats():
    params = urllib.parse.urlencode({
        "dateStart": "2022-02-01T00:00:00.000Z",
        "dateEnd": "2022-02-03T00:00:00.000Z"
    })
    status, response = request(
        f"/node/{ROOT_ID}/statistic?{params}", json_response=True)
    print(len(response["items"]))
    assert status == 200, f"Expected HTTP status code 200, got {status}"

    # ---

    params = urllib.parse.urlencode({
        "dateStart": "2022-02-01T00:00:00.000Z",
        "dateEnd": "2022-02-04T00:00:00.000Z"
    })
    status, response = request(
        f"/node/{ROOT_ID}/statistic?{params}", json_response=True)

    print(len(response["items"]))
    assert status == 200, f"Expected HTTP status code 200, got {status}"

    # ---

    print("Test stats passed.")


def test_stats_after_deletion():
    TO_CHECK = [
        (ROOT_ID,
         urllib.parse.urlencode({
             "dateStart": "2022-02-01T00:00:00.000Z",
             "dateEnd": "2022-02-04T00:00:00.000Z"
         })),
        ("863e1a7a-1304-42ae-943b-179184c077e3",
         urllib.parse.urlencode({
             "dateStart": "2022-02-01T00:00:00.000Z",
             "dateEnd": "2022-02-04T00:00:00.000Z"
         })),
        ("d515e43f-f3f6-4471-bb77-6b455017a2d2",
         urllib.parse.urlencode({
             "dateStart": "2022-02-01T00:00:00.000Z",
             "dateEnd": "2022-02-04T00:00:00.000Z"
         })),
    ]

    for id_, params in TO_CHECK:
        status, response = request(
            f"/node/{id_}/statistic?{params}", json_response=True)

        assert status == 404, f"Expected HTTP status code 200, got {status}"

    print("Test stats after deletion passed.")


def test_delete():
    status, _ = request(f"/delete/{ROOT_ID}", method="DELETE")
    assert status == 200, f"Expected HTTP status code 200, got {status}"

    status, _ = request(f"/nodes/{ROOT_ID}", json_response=True)
    assert status == 404, f"Expected HTTP status code 404, got {status}"

    print("Test delete passed.")


def test_price_after_delete():
    status, _ = request(f"/delete/{DELETE_ID}", method="DELETE")
    assert status == 200, f"Expected HTTP status code 200, got {status}"

    status, response = request(f"/nodes/{ROOT_ID}", json_response=True)
    assert status == 200, f"Expected HTTP status code 200, got {status}"

    with open("data/test_02_deletion.json") as f:
        data = json.load(f)

    deep_sort_children(response)
    deep_sort_children(data)
    if response != data:
        print_diff(data, response)
        print("Response tree doesn't match expected tree.")
        sys.exit(1)

    print("Test price after delete passed.")


def test_price_after_edit_parent():
    status, _ = request("/imports", method="POST", data=EDIT_IMPORT)
    assert status == 200, f"Expected HTTP status code 200, got {status}"

    status, response = request(f"/nodes/{ROOT_ID}", json_response=True)
    assert status == 200, f"Expected HTTP status code 200, got {status}"

    with open("data/test_03_edit_parent.json") as f:
        data = json.load(f)

    deep_sort_children(response)
    deep_sort_children(data)
    if response != data:
        print_diff(data, response)
        print("Response tree doesn't match expected tree.")
        sys.exit(1)

    print("Test price after edit parent passed.")


def test_price_after_edit_category_parent():
    status, _ = request("/imports", method="POST", data=EDIT_IMPORT_CATEGORY)
    assert status == 200, f"Expected HTTP status code 200, got {status}"

    status, response = request(f"/nodes/{ROOT_ID}", json_response=True)
    assert status == 200, f"Expected HTTP status code 200, got {status}"

    with open("data/test_04_edit_category_parent.json") as f:
        data = json.load(f)

    deep_sort_children(response)
    deep_sort_children(data)
    if response != data:
        print_diff(data, response)
        print("Response tree doesn't match expected tree.")
        sys.exit(1)

    print("Test price after edit parent passed.")


def test_all():
    test_delete()
    test_import_400()
    test_import()
    test_nodes()
    test_sales()
    test_stats()

    test_price_after_delete()
    test_price_after_edit_parent()
    test_price_after_edit_category_parent()

    test_delete()
    test_stats_after_deletion()
    test_nodes_after_deletion()


def main():
    global API_BASEURL
    test_name = None

    for arg in sys.argv[1:]:
        if re.match(r"^https?://", arg):
            API_BASEURL = arg
        elif test_name is None:
            test_name = arg

    if API_BASEURL.endswith('/'):
        API_BASEURL = API_BASEURL[:-1]

    if test_name is None:
        test_all()
    else:
        test_func = globals().get(f"test_{test_name}")
        if not test_func:
            print(f"Unknown test: {test_name}")
            sys.exit(1)
        test_func()


if __name__ == "__main__":
    main()
