import asyncio

import pytest
import requests

from tests.clean_db import hook_db


admin_email = "admin@admin.com"
admin_password = "1234"

user_email = "user@user.com"
user_password = "1234"


def request_superuser_token(host, password="1234"):
    return requests.post(
        f"{host}/login", json={"email": "admin@admin.com", "password": password}
    )


def request_user_token(host, password="1234"):
    return requests.post(
        f"{host}/login", json={"email": "user@user.com", "password": password}
    )


def auth_request(host, token, method, path, json):
    return requests.Session().request(
        method, f"{host}/{path}", json=json, headers={"token": token}
    )


@pytest.fixture()
def su_token(url):
    return request_superuser_token(url).json()["token"]


@pytest.fixture()
def user_token(url):
    return request_user_token(url).json()["token"]


@pytest.fixture(scope="session", autouse=True)
def db_fixture():
    asyncio.run(hook_db())


@pytest.fixture(autouse=True)
def migration_fixture(url):
    request_superuser_token(url)


class TestEndpoits:
    def test_correct_login(self, url):
        response = request_superuser_token(url)
        assert response.status_code == 200
        assert response.json()["token"]

    def test_incorrent_login(self, url):
        response = request_superuser_token(url, "0000")
        assert response.status_code == 401

    def test_create_user(self, url, su_token):
        response = auth_request(
            url,
            su_token,
            "post",
            "user",
            {"email": "new@user.com", "password": "FGSDgse334ffdr2", "group_id": 2},
        )
        assert response.status_code == 200

    def test_create_existed_user(self, url, su_token):
        response = auth_request(
            url,
            su_token,
            "post",
            "user",
            {"email": "new@user.com", "password": "FGSDgse334ffdr2", "group_id": 2},
        )
        assert response.status_code == 409

    def test_create_user_bad_password(self, url, su_token):
        response = auth_request(
            url,
            su_token,
            "post",
            "user",
            {"email": "new@user.com", "password": "1234", "group_id": 2},
        )
        assert response.status_code == 400

    def test_create_user_without_privilege(self, url, user_token):
        response = auth_request(
            url,
            user_token,
            "post",
            "user",
            {"email": "new@user.com", "password": "FGSDgse334ffdr2", "group_id": 2},
        )
        assert response.status_code == 403

    def test_get_right(self, url, su_token):
        response = auth_request(url, su_token, "get", "right/1", None)
        assert response.status_code == 200

    def test_get_right_without_privilege(self, url, user_token):
        response = auth_request(url, user_token, "get", "right/1", None)
        assert response.status_code == 403

    def test_get_post_unexisted(self, url, user_token):
        response = auth_request(url, user_token, "get", "post/1", None)
        assert response.status_code == 404

    def test_create_post(self, url, user_token):
        response = auth_request(
            url,
            user_token,
            "post",
            "post",
            {"title": "some_title", "text": "some_text"},
        )
        assert response.status_code == 200

    def test_update_post(self, url, user_token):
        response = auth_request(
            url, user_token, "patch", "post/1", {"title": "new_title"}
        )
        assert response.status_code == 200
        assert response.json()["title"] == "new_title"
        response = auth_request(url, user_token, "get", "post/1", None)
        assert response.json()["title"] == "new_title"

    def test_update_post_not_owner(self, url, su_token):
        new_user_email = "new@user2.com"
        new_user_password = "FGSDgse334ffdr2"
        auth_request(
            url,
            su_token,
            "post",
            "user",
            {"email": new_user_email, "password": new_user_password, "group_id": 2},
        )
        new_user_token = requests.post(
            f"{url}/login",
            json={"email": new_user_email, "password": new_user_password},
        ).json()["token"]
        response = auth_request(
            url, new_user_token, "patch", "post/1", {"title": "new_title_2"}
        )
        assert response.status_code == 403
