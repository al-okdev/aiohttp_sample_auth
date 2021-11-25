import pytest


def pytest_addoption(parser):
    parser.addoption("--url", action="store", default="http://127.0.0.1:8080")


def pytest_generate_tests(metafunc):

    option_value = metafunc.config.option.url
    if "url" in metafunc.fixturenames and option_value is not None:
        metafunc.parametrize("url", [option_value])


@pytest.fixture(scope="session")
def get_url(request):
    return request.config.getoption("--url")