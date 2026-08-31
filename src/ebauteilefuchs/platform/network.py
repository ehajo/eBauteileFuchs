"""Conservative local IPv4 discovery for M5 connection guidance."""

import ipaddress
import socket
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NetworkAddress:
    address: str
    is_private: bool


def hostname() -> str:
    return socket.gethostname() or "Dieser Computer"


def discover_ipv4_addresses() -> tuple[NetworkAddress, ...]:
    candidates: set[str] = set()
    try:
        for item in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            candidates.add(item[4][0])
    except OSError:
        pass
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.connect(("192.0.2.1", 9))
            candidates.add(probe.getsockname()[0])
    except OSError:
        pass

    usable = []
    for value in candidates:
        try:
            address = ipaddress.IPv4Address(value)
        except ipaddress.AddressValueError:
            continue
        if (
            address.is_loopback
            or address.is_link_local
            or address.is_multicast
            or address.is_unspecified
        ):
            continue
        usable.append(NetworkAddress(str(address), address.is_private))
    return tuple(sorted(usable, key=lambda item: (not item.is_private, item.address)))
