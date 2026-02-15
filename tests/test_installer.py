import install


def test_detect_platform_wsl(monkeypatch):
    monkeypatch.setattr(install.platform, "system", lambda: "Linux")
    monkeypatch.setattr(install.platform, "release", lambda: "5.15.167.4-microsoft-standard-WSL2")

    os_name, is_wsl = install.detect_platform()

    assert os_name == "linux"
    assert is_wsl is True


def test_detect_platform_macos(monkeypatch):
    monkeypatch.setattr(install.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(install.platform, "release", lambda: "24.0.0")

    os_name, is_wsl = install.detect_platform()

    assert os_name == "macos"
    assert is_wsl is False


def test_docker_services_to_start_defaults_to_full_stack():
    services = install.docker_services_to_start(use_own_databases=False, use_own_searxng=False)
    assert services == ["neo4j", "weaviate", "searxng"]


def test_docker_services_to_start_with_user_services():
    services = install.docker_services_to_start(use_own_databases=True, use_own_searxng=False)
    assert services == ["searxng"]
