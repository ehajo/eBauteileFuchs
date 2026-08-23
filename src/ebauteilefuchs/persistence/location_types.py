"""Stable identifiers and seed values for built-in location types."""

from uuid import UUID

SYSTEM_LOCATION_TYPES = (
    (UUID("10000000-0000-4000-8000-000000000001"), "room", "Raum", 10),
    (UUID("10000000-0000-4000-8000-000000000002"), "cabinet", "Schrank", 20),
    (UUID("10000000-0000-4000-8000-000000000003"), "shelf", "Regal", 30),
    (UUID("10000000-0000-4000-8000-000000000004"), "magazine", "Magazin", 40),
    (UUID("10000000-0000-4000-8000-000000000005"), "drawer", "Schublade", 50),
    (
        UUID("10000000-0000-4000-8000-000000000006"),
        "compartment",
        "Unterfach",
        60,
    ),
    (UUID("10000000-0000-4000-8000-000000000007"), "box", "Box", 70),
    (UUID("10000000-0000-4000-8000-000000000008"), "crate", "Kiste", 80),
)
