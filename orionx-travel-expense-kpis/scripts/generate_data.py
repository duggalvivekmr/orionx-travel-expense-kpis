import pandas as pd
import random
from faker import Faker
from datetime import datetime, timedelta

fake = Faker()
ROWS = 70000

# Date range
START_DATE = datetime(2024, 7, 1)
END_DATE = datetime(2025, 12, 31)

def random_date(start, end):
    return start + timedelta(days=random.randint(0, (end - start).days))

# Departments
departments = [
    "Finance", "Global Support & Services", "Executive", "IT & Security",
    "Legal", "Marketing", "R&D", "Workplace", "People", "WWFO"
]

# Job family mapping
job_family_map = {
    "WWFO": ["Field Sales", "Strategic Account Management"],
    "Marketing": ["Field Sales", "Strategic Account Management", "Solutions Engineering"],
    "R&D": ["Solutions Engineering"],
    "IT & Security": ["Software Engineering", "Solutions Engineering"],
    "Global Support & Services": ["Software Engineering", "Strategic Account Management"],
    "Executive": ["Executive Assistant"],
    "Finance": ["Software Engineering"],
    "Legal": ["Software Engineering"],
    "People": ["Software Engineering"],
    "Workplace": ["Software Engineering"]
}

# Countries
countries = {
    "United States": ("AMER", "USD"),
    "Canada": ("AMER", "CAD"),
    "Germany": ("EMEA", "EUR"),
    "United Kingdom": ("EMEA", "GBP"),
    "India": ("APAC", "INR"),
    "Singapore": ("APAC", "SGD"),
    "Australia": ("APAC", "AUD"),
    "France": ("EMEA", "EUR"),
    "Brazil": ("AMER", "BRL"),
    "Japan": ("APAC", "JPY")
}

# Expense taxonomy
travel_expenses = [
    "Airfare – Customer Facing", "Airfare – Internal", "Airfare – Conference",
    "Airfare – Company Event", "Airfare – Offsite",
    "Hotel – Customer Facing", "Hotel – Internal", "Hotel – Conference",
    "Meal – Customer Facing", "Meal – Internal", "Meal – Conference",
    "Car – Internal", "Transportation – Internal",
    "Ground Transportation – Customer Facing",
    "Parking and Tolls", "Travel Internet",
    "Mileage – Personal Car", "Fuel / Gas Charges", "Relocation Expense"
]

non_travel_expenses = [
    "Software and Software Subscription", "Office Expense", "Internet",
    "Entertainment", "Education", "Seminars, & Conferences",
    "Gifts", "Donation", "Taxable Award", "Bank / FX Fees",
    "Computer/Laptop Accessories"
]

vendors = [
    "Uber", "Lyft", "Ola", "Grab",
    "Delta Airlines", "United Airlines", "American Airlines", "Lufthansa",
    "Marriott", "Hilton", "Hyatt", "IHG",
    "Starbucks", "Local Restaurant",
    "Shell", "BP", "ExxonMobil",
    "Microsoft", "AWS", "Google", "Adobe", "Atlassian",
    "Coursera", "Udemy Business", "LinkedIn Learning",
    "Ticketmaster", "Eventbrite"
]

approval_statuses = [
    "Approved",
    "Approved in Accounting Review",
    "Sent Back to Employee",
    "Submitted & Pending Approval"
]

payment_types = [
    "Company Paid",
    "Personal Credit Card",
    "Corporate Credit Card"
]

records = []

for _ in range(ROWS):
    dept = random.choice(departments)
    job_family = random.choice(job_family_map[dept])

    parent_expense = random.choice(["Travel", "Non-Travel"])
    expense_type = random.choice(
        travel_expenses if parent_expense == "Travel" else non_travel_expenses
    )

    txn_date = random_date(START_DATE, END_DATE)
    submit_delay = random.randint(0, 14)
    submit_date = txn_date + timedelta(days=submit_delay)
    mgr_date = submit_date + timedelta(days=random.randint(1, 7))
    acct_date = mgr_date + timedelta(days=random.randint(1, 5))

    country = random.choice(list(countries.keys()))
    region, currency = countries[country]

    local_amt = round(random.uniform(15, 3000), 2)
    fx_rate = random.uniform(0.5, 1.5)
    usd_amt = round(local_amt if currency == "USD" else local_amt * fx_rate, 2)

    records.append({
        "employee": fake.name(),
        "employee ID": random.randint(100000, 999999),
        "active": random.choice(["Yes", "No"]),
        "department name": dept,
        "job family": job_family,
        "payment type": random.choice(payment_types),
        "approval status": random.choice(approval_statuses),
        "report name": fake.word().capitalize() + " Expense Report",
        "report ID": fake.unique.bothify("####################"),
        "parent expense type": parent_expense,
        "expense type": expense_type,
        "vendor": random.choice(vendors),
        "purpose": fake.sentence(nb_words=6),
        "transaction date": txn_date.strftime("%m/%d/%Y"),
        "transaction month": txn_date.strftime("%B"),
        "transaction quarter": (txn_date.month - 1) // 3 + 1,
        "transaction year": txn_date.year,
        "first submitted date": submit_date.strftime("%m/%d/%Y"),
        "manager approval date": mgr_date.strftime("%m/%d/%Y"),
        "accounting approval date": acct_date.strftime("%m/%d/%Y"),
        "location": fake.city(),
        "country": country,
        "region": region,
        "subsidiary name": f"OrionX Labs {country}",
        "reimbursement currency": currency,
        "reporting currency": "USD",
        "number of attendees": random.randint(1, 12),
        "expense approved amount": local_amt,
        "expense approved amount(rpt)": usd_amt,
        "difference b/w submission_transc.": submit_delay
    })

df = pd.DataFrame(records)

output_file = "OrionX_Labs_Travel_Expense_Final_70000.xlsx"
df.to_excel(output_file, index=False)

print(f"Dataset generated: {output_file}")
