import socket

import pytest


@pytest.fixture(autouse=True)
def disable_network(monkeypatch):
    """Prevent every routine test from making a real network connection."""

    def blocked(*args, **kwargs):
        raise RuntimeError("Network access is disabled during fixture-only tests")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", blocked)
