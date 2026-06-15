EXPENDITURE_CATEGORIES = [
    "transport",
    "groceries",
    "health and wellness",
    "utilities",
    "home",
    "automotive",
    "pharmacy",
    "eating out",
    "shopping",
    "services",
    "insurance",
    "religious",
    "tax",
    "investments"
]

ALL_SUBCATEGORIES = [
    "transport:public transit",
    "transport:gas",
    "transport:tolls",
    "transport:parking",
    "automotive:parts/fluids",
    "groceries:staples",
    "groceries:coffee",
    "health and wellness:supplements",
    "health and wellness:gym",
    "health and wellness:medical",
    "health and wellness:pharmacy",
    "utilities:phone",
    "utilities:electric",
    "utilities:internet",
    "utilities:compost",
    "utilities:AI subscription",
    "utilities:water",
    "utilities:gas",
    "utilities:HOA",
    "home:home improvement",
    "home:furniture",
    "home:cleaning/soap",
    "eating out:coffee",
    "eating out:treats",
    "eating out:restaurant",
    "shopping:clothes",
    "shopping:appliances",
    "shopping:tools",
    "shopping:office",
    "shopping:baby",
    "services:cleaners",
    "services:car wash",
    "services:lawn mowing",
    "insurance:home",
    "insurance:auto",
    "insurance:health/life",
    "religious:candles",
    "religious:donation",
    "religious:books",
    "tax:payments",
    "tax:software",
    "pharmacy",
    "investments:metals",
    "investments:stocks"
]


NECESSITY = [
    "basic",
    "middle",
    "luxury",
    "donation",
    "investment"
]

# Necessity levels selected by default in the persistent filter (shared across
# all tabs). Excludes "donation" and "investment" so charts/tables focus on
# ordinary spending until the user opts those back in.
DEFAULT_NECESSITY_FILTER = ["basic", "middle", "luxury"]
