import re

MONTH_MAP = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12
}

KNOWN_INDIAN_LOCATIONS = [
    "ahmedabad", "gandhinagar", "surat", "gujarat",
    "pune", "mumbai", "nagpur", "maharashtra",
    "bangalore", "bengaluru", "mysore", "mangalore", "karnataka",
    "delhi", "new delhi",
    "hyderabad", "telangana",
    "chennai", "tiruchirappalli", "tamil nadu",
    "bhopal", "indore", "madhya pradesh", "mp",
    "jaipur", "jodhpur", "pilani", "rajasthan",
    "kanpur", "varanasi", "noida", "uttar pradesh", "up",
    "kolkata", "kharagpur", "west bengal",
    "kozhikode", "palakkad", "kerala",
    "roorkee", "uttarakhand",
    "rupnagar", "punjab"
]

FOREIGN_LOCATIONS = [
    "tokyo", "japan", "london", "uk", "paris", "france", "dubai", "uae",
    "new york", "usa", "us", "singapore", "germany", "berlin", "canada",
    "toronto", "australia", "sydney"
]


def parse_dates_and_location(text: str):
    """
    Intelligently parses:
    1. Any YYYY-MM-DD date ranges (e.g. 2026-03-01 to 2026-03-31, 2020-01-01)
    2. Month names (e.g. March, July to October, Dec 2026)
    3. Indian cities, states, and aliases (e.g. Bangalore, Pune, Maharashtra)
    4. Detects non-Indian foreign locations
    """
    lower = text.lower()

    # 1. Any YYYY-MM-DD dates
    date_matches = re.findall(r"\b\d{4}-\d{2}-\d{2}\b", text)
    from_date = date_matches[0] if len(date_matches) > 0 else ""
    to_date = date_matches[1] if len(date_matches) > 1 else ""

    # 2. Check for month names if exact YYYY-MM-DD dates not fully provided
    if not from_date or not to_date:
        found_months = []
        for word in re.findall(r"\b[a-zA-Z]+\b", lower):
            if word in MONTH_MAP:
                found_months.append(MONTH_MAP[word])

        if found_months:
            m_start = found_months[0]
            m_end = found_months[-1]
            if m_start > m_end:
                m_start, m_end = m_end, m_start

            year = "2026"
            year_match = re.search(r"\b(202\d)\b", text)
            if year_match:
                year = year_match.group(1)

            if not from_date:
                from_date = f"{year}-{m_start:02d}-01"
            if not to_date:
                end_day = 31 if m_end in [1, 3, 5, 7, 8, 10, 12] else (28 if m_end == 2 else 30)
                to_date = f"{year}-{m_end:02d}-{end_day:02d}"

    # 3. Check for foreign location
    is_foreign = False
    for floc in FOREIGN_LOCATIONS:
        if floc in lower:
            is_foreign = True
            return from_date, to_date, floc, is_foreign

    # 4. Known Indian states & cities
    found_loc = ""
    for loc in KNOWN_INDIAN_LOCATIONS:
        if loc in lower:
            if loc == "bengaluru":
                found_loc = "bangalore"
            elif loc == "mp":
                found_loc = "madhya pradesh"
            elif loc == "up":
                found_loc = "uttar pradesh"
            else:
                found_loc = loc
            break

    # If user typed arbitrary word that might be a city/state
    if not found_loc:
        words = [w.strip(".,;:?!") for w in text.split() if len(w) > 3 and not any(c.isdigit() for c in w)]
        stop = ["from", "date", "travel", "state", "city", "want", "find", "search", "india", "only", "give", "show", "seminar", "seminars", "please"]
        filtered = [w for w in words if w.lower() not in stop]
        if filtered:
            found_loc = filtered[0].lower()

    # Default fallback date window if none specified
    if not from_date:
        from_date = "2026-01-01"
    if not to_date:
        to_date = "2026-12-31"

    return from_date, to_date, found_loc, is_foreign
