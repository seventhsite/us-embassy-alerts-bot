"""
Complete list of U.S. Embassy websites with country codes, names, and flags.

Each entry maps to an RSS feed at:
    https://{code}.usembassy.gov/category/alert/feed/

Countries are grouped by region for convenient navigation in inline keyboards.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Country:
    """A country with a U.S. Embassy presence."""

    code: str       # ISO 3166-1 alpha-2 (lowercase), used in the subdomain
    name: str       # English name
    flag: str       # Flag emoji

    @property
    def feed_url(self) -> str:
        """RSS feed URL for this country's embassy alerts."""
        return f"https://{self.code}.usembassy.gov/category/alert/feed/"


# All regions with their countries, sorted alphabetically within each region
REGIONS: dict[str, list[Country]] = {
    "🌍 Africa": sorted([
        Country("dz", "Algeria", "🇩🇿"),
        Country("ao", "Angola", "🇦🇴"),
        Country("bj", "Benin", "🇧🇯"),
        Country("bw", "Botswana", "🇧🇼"),
        Country("bf", "Burkina Faso", "🇧🇫"),
        Country("bi", "Burundi", "🇧🇮"),
        Country("cm", "Cameroon", "🇨🇲"),
        Country("cv", "Cabo Verde", "🇨🇻"),
        Country("cf", "Central African Republic", "🇨🇫"),
        Country("td", "Chad", "🇹🇩"),
        Country("km", "Comoros", "🇰🇲"),
        Country("cg", "Congo (Brazzaville)", "🇨🇬"),
        Country("cd", "Congo (Kinshasa)", "🇨🇩"),
        Country("ci", "Côte d'Ivoire", "🇨🇮"),
        Country("dj", "Djibouti", "🇩🇯"),
        Country("gq", "Equatorial Guinea", "🇬🇶"),
        Country("er", "Eritrea", "🇪🇷"),
        Country("sz", "Eswatini", "🇸🇿"),
        Country("et", "Ethiopia", "🇪🇹"),
        Country("ga", "Gabon", "🇬🇦"),
        Country("gm", "Gambia", "🇬🇲"),
        Country("gh", "Ghana", "🇬🇭"),
        Country("gn", "Guinea", "🇬🇳"),
        Country("gw", "Guinea-Bissau", "🇬🇼"),
        Country("ke", "Kenya", "🇰🇪"),
        Country("ls", "Lesotho", "🇱🇸"),
        Country("lr", "Liberia", "🇱🇷"),
        Country("ly", "Libya", "🇱🇾"),
        Country("mg", "Madagascar", "🇲🇬"),
        Country("mw", "Malawi", "🇲🇼"),
        Country("ml", "Mali", "🇲🇱"),
        Country("mr", "Mauritania", "🇲🇷"),
        Country("mu", "Mauritius", "🇲🇺"),
        Country("mz", "Mozambique", "🇲🇿"),
        Country("na", "Namibia", "🇳🇦"),
        Country("ne", "Niger", "🇳🇪"),
        Country("ng", "Nigeria", "🇳🇬"),
        Country("rw", "Rwanda", "🇷🇼"),
        Country("sn", "Senegal", "🇸🇳"),
        Country("sl", "Sierra Leone", "🇸🇱"),
        Country("so", "Somalia", "🇸🇴"),
        Country("za", "South Africa", "🇿🇦"),
        Country("ss", "South Sudan", "🇸🇸"),
        Country("sd", "Sudan", "🇸🇩"),
        Country("tz", "Tanzania", "🇹🇿"),
        Country("tg", "Togo", "🇹🇬"),
        Country("tn", "Tunisia", "🇹🇳"),
        Country("ug", "Uganda", "🇺🇬"),
        Country("zm", "Zambia", "🇿🇲"),
        Country("zw", "Zimbabwe", "🇿🇼"),
    ], key=lambda c: c.name),

    "🌏 East Asia & Pacific": sorted([
        Country("au", "Australia", "🇦🇺"),
        Country("bn", "Brunei", "🇧🇳"),
        Country("kh", "Cambodia", "🇰🇭"),
        Country("cn", "China", "🇨🇳"),
        Country("fj", "Fiji", "🇫🇯"),
        Country("id", "Indonesia", "🇮🇩"),
        Country("jp", "Japan", "🇯🇵"),
        Country("la", "Laos", "🇱🇦"),
        Country("my", "Malaysia", "🇲🇾"),
        Country("mh", "Marshall Islands", "🇲🇭"),
        Country("fm", "Micronesia", "🇫🇲"),
        Country("mn", "Mongolia", "🇲🇳"),
        Country("mm", "Myanmar", "🇲🇲"),
        Country("nz", "New Zealand", "🇳🇿"),
        Country("pw", "Palau", "🇵🇼"),
        Country("pg", "Papua New Guinea", "🇵🇬"),
        Country("ph", "Philippines", "🇵🇭"),
        Country("ws", "Samoa", "🇼🇸"),
        Country("sg", "Singapore", "🇸🇬"),
        Country("sb", "Solomon Islands", "🇸🇧"),
        Country("kr", "South Korea", "🇰🇷"),
        Country("tw", "Taiwan", "🇹🇼"),
        Country("th", "Thailand", "🇹🇭"),
        Country("tl", "Timor-Leste", "🇹🇱"),
        Country("to", "Tonga", "🇹🇴"),
        Country("vn", "Vietnam", "🇻🇳"),
    ], key=lambda c: c.name),

    "🌍 Europe": sorted([
        Country("al", "Albania", "🇦🇱"),
        Country("ad", "Andorra", "🇦🇩"),
        Country("am", "Armenia", "🇦🇲"),
        Country("at", "Austria", "🇦🇹"),
        Country("az", "Azerbaijan", "🇦🇿"),
        Country("by", "Belarus", "🇧🇾"),
        Country("be", "Belgium", "🇧🇪"),
        Country("ba", "Bosnia and Herzegovina", "🇧🇦"),
        Country("bg", "Bulgaria", "🇧🇬"),
        Country("hr", "Croatia", "🇭🇷"),
        Country("cy", "Cyprus", "🇨🇾"),
        Country("cz", "Czech Republic", "🇨🇿"),
        Country("dk", "Denmark", "🇩🇰"),
        Country("ee", "Estonia", "🇪🇪"),
        Country("fi", "Finland", "🇫🇮"),
        Country("fr", "France", "🇫🇷"),
        Country("ge", "Georgia", "🇬🇪"),
        Country("de", "Germany", "🇩🇪"),
        Country("gr", "Greece", "🇬🇷"),
        Country("hu", "Hungary", "🇭🇺"),
        Country("is", "Iceland", "🇮🇸"),
        Country("ie", "Ireland", "🇮🇪"),
        Country("it", "Italy", "🇮🇹"),
        Country("xk", "Kosovo", "🇽🇰"),
        Country("lv", "Latvia", "🇱🇻"),
        Country("lt", "Lithuania", "🇱🇹"),
        Country("lu", "Luxembourg", "🇱🇺"),
        Country("mt", "Malta", "🇲🇹"),
        Country("md", "Moldova", "🇲🇩"),
        Country("me", "Montenegro", "🇲🇪"),
        Country("nl", "Netherlands", "🇳🇱"),
        Country("mk", "North Macedonia", "🇲🇰"),
        Country("no", "Norway", "🇳🇴"),
        Country("pl", "Poland", "🇵🇱"),
        Country("pt", "Portugal", "🇵🇹"),
        Country("ro", "Romania", "🇷🇴"),
        Country("ru", "Russia", "🇷🇺"),
        Country("rs", "Serbia", "🇷🇸"),
        Country("sk", "Slovakia", "🇸🇰"),
        Country("si", "Slovenia", "🇸🇮"),
        Country("es", "Spain", "🇪🇸"),
        Country("se", "Sweden", "🇸🇪"),
        Country("ch", "Switzerland", "🇨🇭"),
        Country("tr", "Turkey", "🇹🇷"),
        Country("ua", "Ukraine", "🇺🇦"),
        Country("gb", "United Kingdom", "🇬🇧"),
    ], key=lambda c: c.name),

    "🌎 Americas": sorted([
        Country("ar", "Argentina", "🇦🇷"),
        Country("bs", "Bahamas", "🇧🇸"),
        Country("bb", "Barbados", "🇧🇧"),
        Country("bz", "Belize", "🇧🇿"),
        Country("bo", "Bolivia", "🇧🇴"),
        Country("br", "Brazil", "🇧🇷"),
        Country("ca", "Canada", "🇨🇦"),
        Country("cl", "Chile", "🇨🇱"),
        Country("co", "Colombia", "🇨🇴"),
        Country("cr", "Costa Rica", "🇨🇷"),
        Country("cu", "Cuba", "🇨🇺"),
        Country("do", "Dominican Republic", "🇩🇴"),
        Country("ec", "Ecuador", "🇪🇨"),
        Country("sv", "El Salvador", "🇸🇻"),
        Country("gt", "Guatemala", "🇬🇹"),
        Country("gy", "Guyana", "🇬🇾"),
        Country("ht", "Haiti", "🇭🇹"),
        Country("hn", "Honduras", "🇭🇳"),
        Country("jm", "Jamaica", "🇯🇲"),
        Country("mx", "Mexico", "🇲🇽"),
        Country("ni", "Nicaragua", "🇳🇮"),
        Country("pa", "Panama", "🇵🇦"),
        Country("py", "Paraguay", "🇵🇾"),
        Country("pe", "Peru", "🇵🇪"),
        Country("sr", "Suriname", "🇸🇷"),
        Country("tt", "Trinidad and Tobago", "🇹🇹"),
        Country("uy", "Uruguay", "🇺🇾"),
        Country("ve", "Venezuela", "🇻🇪"),
    ], key=lambda c: c.name),

    "🕌 Middle East & North Africa": sorted([
        Country("bh", "Bahrain", "🇧🇭"),
        Country("eg", "Egypt", "🇪🇬"),
        Country("iq", "Iraq", "🇮🇶"),
        Country("il", "Israel", "🇮🇱"),
        Country("jo", "Jordan", "🇯🇴"),
        Country("kw", "Kuwait", "🇰🇼"),
        Country("lb", "Lebanon", "🇱🇧"),
        Country("ma", "Morocco", "🇲🇦"),
        Country("om", "Oman", "🇴🇲"),
        Country("qa", "Qatar", "🇶🇦"),
        Country("sa", "Saudi Arabia", "🇸🇦"),
        Country("ae", "United Arab Emirates", "🇦🇪"),
        Country("ye", "Yemen", "🇾🇪"),
    ], key=lambda c: c.name),

    "🌏 South & Central Asia": sorted([
        Country("af", "Afghanistan", "🇦🇫"),
        Country("bd", "Bangladesh", "🇧🇩"),
        Country("in", "India", "🇮🇳"),
        Country("kz", "Kazakhstan", "🇰🇿"),
        Country("kg", "Kyrgyzstan", "🇰🇬"),
        Country("np", "Nepal", "🇳🇵"),
        Country("pk", "Pakistan", "🇵🇰"),
        Country("lk", "Sri Lanka", "🇱🇰"),
        Country("tj", "Tajikistan", "🇹🇯"),
        Country("tm", "Turkmenistan", "🇹🇲"),
        Country("uz", "Uzbekistan", "🇺🇿"),
    ], key=lambda c: c.name),
}

# Flat lookup: code -> Country
ALL_COUNTRIES: dict[str, Country] = {}
for _countries in REGIONS.values():
    for _c in _countries:
        ALL_COUNTRIES[_c.code] = _c

# Reverse lookup: lowercase name -> Country (for /latest command)
_NAME_INDEX: dict[str, Country] = {}
for _c in ALL_COUNTRIES.values():
    _NAME_INDEX[_c.name.lower()] = _c


def find_country_by_name(query: str) -> Country | None:
    """
    Find a country by name (case-insensitive).

    Supports exact match and partial/prefix match as fallback.
    """
    q = query.strip().lower()
    if not q:
        return None

    # Match by country code first (highest priority)
    if q in ALL_COUNTRIES:
        return ALL_COUNTRIES[q]

    # Exact name match
    if q in _NAME_INDEX:
        return _NAME_INDEX[q]

    # Partial match (prefix)
    matches = [c for name, c in _NAME_INDEX.items() if name.startswith(q)]
    if len(matches) == 1:
        return matches[0]

    # Substring match (fallback)
    matches = [c for name, c in _NAME_INDEX.items() if q in name]
    if len(matches) == 1:
        return matches[0]

    return None


def get_region_names() -> list[str]:
    """Return the list of region names (with emoji)."""
    return list(REGIONS.keys())
