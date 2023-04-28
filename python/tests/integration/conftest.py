def pytest_addoption(parser):
    parser.addoption("--use-env-vars", action="store", default=False)


def pytest_generate_tests(metafunc):
    # This is called for every test. Only get/set command line arguments
    # if the argument is specified in the list of test "fixturenames".
    if 'use-env-vars' in metafunc.fixturenames:
        metafunc.parametrize("use_env_vars", [True])
    else:
        metafunc.parametrize("use_env_vars", [False])