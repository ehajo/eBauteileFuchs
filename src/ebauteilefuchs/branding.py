"""Central product and branding metadata."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Branding:
    product_name: str = "eBauteileFuchs"
    tagline: str = "Clever finden statt lange suchen."
    attribution: str = "Ein Open-Source-Projekt von eHaJo."
    footer: str = "eBauteileFuchs – ein Open-Source-Projekt von eHaJo"
    owner_name: str = "eHaJo"
    website: str = "https://www.ehajo.de"
    primary_color: str = "#0b72b5"
    secondary_color: str = "#e67c23"
    theme_color: str = "#0b1118"


BRANDING = Branding()
