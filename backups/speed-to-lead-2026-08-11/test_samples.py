"""
test_samples.py  --  runs the parser against every awkward email we can think of.

Each sample says what it EXPECTS to happen. If the parser disagrees, the test
prints FAIL so you can see exactly which case broke and why.

RUN IT
    python test_samples.py
"""

from parse_lead import (
    parse_email, LEAD, SKIP_AUTO_REPLY, SKIP_NOT_A_LEAD,
    THREAD_REPLY, NEEDS_REVIEW,
)


# ---------------------------------------------------------------------------
# THE THREE ORIGINAL SAMPLES  --  these already work, we keep them so a future
# change can't quietly break them again.
# ---------------------------------------------------------------------------

SAMPLES = []


def sample(title, expect_status, raw, expect_fields=None):
    SAMPLES.append({
        "title": title,
        "expect_status": expect_status,
        "raw": raw,
        "expect_fields": expect_fields or {},
    })


sample(
    "1. Plain text form (Contact Form 7 style)", LEAD,
    """From: noreply@joesplumbing.com
Subject: New Contact Form Submission

Name: John Smith
Phone: (555) 402-8871
Email: jsmith@gmail.com
Service Needed: Water Heater Repair
Message: Water heater started leaking last night, there is water
on the basement floor. Need someone soon.
""",
    {"name": "John Smith", "job_type": "Water Heater Repair",
     "email": "jsmith@gmail.com"},
)

sample(
    "2. HTML table form (WPForms style)", LEAD,
    """<html><body><table>
<tr><td><strong>Your Name</strong></td></tr><tr><td>Maria Gonzalez</td></tr>
<tr><td><strong>Best Number</strong></td></tr><tr><td>555-338-2011</td></tr>
<tr><td><strong>Service Address</strong></td></tr><tr><td>44 Oak Ave, Tampa FL 33601</td></tr>
<tr><td><strong>Service Type</strong></td></tr><tr><td>Drain Cleaning / Clog</td></tr>
<tr><td><strong>When do you need service?</strong></td></tr><tr><td>Within 24 hours</td></tr>
</table></body></html>
""",
    {"name": "Maria Gonzalez", "job_type": "Drain Cleaning / Clog"},
)

sample(
    "3. A newsletter, not a lead", SKIP_NOT_A_LEAD,
    """From: newsletter@plumbingsupply.com
Subject: August deals on copper fittings

Hi there,
Our summer sale is on. Message us to learn more about bulk pricing.
""",
)


# ---------------------------------------------------------------------------
# THE EIGHT TOUGH CASES
# ---------------------------------------------------------------------------

sample(
    "4. CASE 1 - no labels at all, just a person talking", LEAD,
    """From: john.smith@gmail.com
Subject: help

Hi, I'm John. My kitchen sink is leaking pretty bad.
Can someone come out? My number is 555-402-8871.
""",
    # BUG E: he wrote "Hi, I'm John" - we must catch that as his name.
    {"phone": "555-402-8871", "name": "John"},
)

sample(
    "5. CASE 2 - customer replying inside our own thread", THREAD_REPLY,
    """From: john.smith@gmail.com
Subject: Re: Your Water Heater Repair request

Tuesday works, thanks.

On Mon, Aug 10, 2026 at 2:14 PM Joe's Plumbing wrote:
> Hi John, thanks for reaching out about your Water Heater Repair.
> Reply 1 for Tue 2-4pm or 2 for Wed 9-11am.
> Name: John Smith
> Phone: (555) 402-8871
""",
)

sample(
    "6. CASE 3 - a forwarded enquiry", LEAD,
    """From: assistant@joesplumbing.com
Subject: Fwd: New Contact Form Submission

---------- Forwarded message ----------
From: noreply@joesplumbing.com
Subject: New Contact Form Submission

Name: Dave Wilson
Phone: (555) 771-2093
Service Needed: Toilet Installation
""",
    # BUG F: the From: address here is the assistant who forwarded it, NOT Dave.
    # We must not fall back to it, or Dave never gets his confirmation.
    {"name": "Dave Wilson", "email": None},
)

sample(
    "7. CASE 4 - marketplace lead (Thumbtack style)", LEAD,
    """From: leads@thumbtack.com
Subject: New lead: Plumbing

You have a new lead!

Customer: John S.
Project: Water heater installation
Location: Tampa, FL 33601
Requested: Within a week
""",
    {"name": "John S.", "job_type": "Water heater installation",
     "address": "Tampa, FL 33601", "urgency": "Within a week"},
)

sample(
    "8. CASE 5 - colons inside the customer's own message", LEAD,
    """From: noreply@joesplumbing.com
Subject: New Contact Form Submission

Name: Sarah Chen
Phone: 555-889-4412
Message: Here's the situation:
Problem: burst pipe under the sink
Urgency: whenever you can, honestly
""",
    # BUG B: her form gave no email. We must NOT fall back to the site's
    # noreply@ robot address, or she never receives the reply.
    {"name": "Sarah Chen", "email": None},
)

sample(
    "9. CASE 6 - out-of-office auto-reply (MUST stay silent)", SKIP_AUTO_REPLY,
    """From: john.smith@gmail.com
Subject: Automatic reply: Your Water Heater Repair request

I am out of the office until August 20th with limited access to email.
For urgent matters call 555-402-8871.
""",
)

sample(
    "10. CASE 7 - spam / phishing (MUST stay silent)", SKIP_NOT_A_LEAD,
    """From: winner@prize-notification.biz
Subject: URGENT: Your account requires verification

Dear Customer,
Please confirm your details immediately.
Contact: support@prize-notification.biz  Phone: 1-800-555-0199
""",
)

sample(
    "11. CASE 8 - unknown extra fields we've never seen", LEAD,
    """From: noreply@joesplumbing.com
Subject: New Contact Form Submission

Name: Robert Lee
Phone: (555) 220-7788
How did you hear about us?: Google
Are you a returning customer?: No
Preferred technician: Mike
Service Needed: Water Heater Repair
""",
    # BUG B again - same noreply@ trap.
    {"name": "Robert Lee", "job_type": "Water Heater Repair", "email": None},
)


# ---------------------------------------------------------------------------
# REAL-FORMAT CASES
# Built from the actual Angi and Thumbtack forms Roshan filled in, plus
# published formats for Squarespace, Gravity Forms and Google Local Services.
# ---------------------------------------------------------------------------

sample(
    "12. Angi lead - real question wording, name split in two", LEAD,
    """From: leads@angi.com
Subject: New lead: Plumbing

What plumbing do you need help with?: Water Heater
What needs to be installed or replaced?: Water heater
What kind of location is this?: Home
When do you need this work done?: Within a week
Please tell us a little about your project: Old unit is 14 years old and noisy.
What's your project address?: 812 Maple St, Columbus OH 43004
First Name: Michael
Last Name: Torres
Phone: (614) 555-2201
Email: mtorres@example.com
""",
    {"name": "Michael Torres", "job_type": "Water Heater",
     "urgency": "Within a week", "email": "mtorres@example.com",
     "emergency": False},
)

sample(
    "13. Thumbtack lead - phone only, flooded = Yes", LEAD,
    """From: no-reply@thumbtack.com
Subject: New lead: Emergency Plumbing

Customer: Dana R.
Is any part of the building currently flooded?: Yes
Which appliances, if any, are affected?: Water heater, washing machine
What type of property do you have?: Single family home
When do you need this job to start?: Right away
Send a message to the pro: Water everywhere in the basement.
Zip: 33612
Phone: (813) 555-0147
""",
    # Thumbtack hides the customer's email, so we must NOT invent one.
    {"name": "Dana R.", "email": None, "emergency": True},
)

sample(
    "14. Google Local Services - just a link to their dashboard", NEEDS_REVIEW,
    """From: noreply@localservicesads.google.com
Subject: You have a new lead

You have a new message lead.
View the details in your lead inbox.
https://ads.google.com/localservices/leads
""",
)

sample(
    "15. Squarespace form - first and last name in separate boxes", LEAD,
    """From: form-submission@squarespace.info
Subject: Form Submission

First Name: Angela
Last Name: Brooks
Email: abrooks@example.com
Phone Number: 704-555-8890
Message: Shower drips constantly, would like a quote.
""",
    {"name": "Angela Brooks", "email": "abrooks@example.com"},
)

sample(
    "16. Gravity Forms - HTML table, label and value in one row", LEAD,
    """<html><body><table>
<tr><td>Name</td><td>Priya Nair</td></tr>
<tr><td>Phone</td><td>408.555.7712</td></tr>
<tr><td>Service Needed</td><td>Garbage Disposal Replacement</td></tr>
<tr><td>Message</td><td>Disposal jammed and humming.</td></tr>
</table></body></html>
""",
    {"name": "Priya Nair", "phone": "408.555.7712",
     "job_type": "Garbage Disposal Replacement", "email": None},
)

sample(
    "17. Emergency written in plain words, no form at all", LEAD,
    """From: tom.baker@example.com
Subject: URGENT - basement flooding

Hi, this is Tom. My basement is flooding right now. Please help.
You can reach me on 312-555-9034.
""",
    {"name": "Tom", "emergency": True},
)

sample(
    "18. Routine job - must NOT be flagged as an emergency", LEAD,
    """From: noreply@joesplumbing.com
Subject: New Contact Form Submission

Name: Ellen Park
Phone: (503) 555-1188
Service Needed: Faucet Installation
When do you need this work done?: Sometime next month
Message: Would like a quote for replacing two bathroom faucets.
""",
    {"name": "Ellen Park", "emergency": False, "urgency": "Sometime next month"},
)

sample(
    "19. Messy form - stray spaces and SHOUTING labels", LEAD,
    """From: noreply@site.com
Subject: New Contact Form Submission

   NAME   :   Carla Diaz
   PHONE NUMBER :   (786) 555-3321
   SERVICE NEEDED :   Sewer Line Repair
""",
    {"name": "Carla Diaz", "job_type": "Sewer Line Repair"},
)

sample(
    "20. Bounce message - mail could not be delivered", SKIP_AUTO_REPLY,
    """From: MAILER-DAEMON@googlemail.com
Subject: Delivery Status Notification (Failure)

Your message could not be delivered to jsmith@gmial.com.
""",
)

sample(
    "21. Yelp quote request - details locked in their app", NEEDS_REVIEW,
    """From: leads@yelp.com
Subject: New quote request

You have a new quote request from a customer.
Log in to Yelp for Business to respond.
""",
)

sample(
    "22. Someone else's email inside the message", LEAD,
    """From: noreply@joesplumbing.com
Subject: New Contact Form Submission

Name: Greg Hall
Email: ghall@example.com
Phone: (206) 555-4412
Service Needed: Toilet Repair
Message: My landlord is manager@bigrealty.com, copy him in if needed.
""",
    # The labelled field must win over the address buried in the message.
    {"email": "ghall@example.com", "name": "Greg Hall"},
)

sample(
    "23. No labels - 'my name is' in the middle of a sentence", LEAD,
    """From: jenny.k@example.com
Subject: quote

my name is Jenny Kowalski and I need a new sump pump installed.
Call 617-555-2245.
""",
    {"name": "Jenny Kowalski", "job_type": "Sump Pump"},
)

sample(
    "24. HTML form using &amp; instead of a plain ampersand", LEAD,
    """<html><body><table>
<tr><td><strong>Your Name</strong></td></tr><tr><td>Luis Ortega</td></tr>
<tr><td><strong>Best Number</strong></td></tr><tr><td>305-555-6620</td></tr>
<tr><td><strong>Service Type</strong></td></tr><tr><td>Drain &amp; Sewer Cleaning</td></tr>
</table></body></html>
""",
    {"name": "Luis Ortega", "job_type": "Drain & Sewer Cleaning"},
)


# ---------------------------------------------------------------------------
# THE TEST RUNNER
# ---------------------------------------------------------------------------

def run():
    passed = failed = 0

    for s in SAMPLES:
        result = parse_email(s["raw"])
        problems = []

        if result["status"] != s["expect_status"]:
            problems.append(
                f"expected status {s['expect_status']}, got {result['status']}")

        for field, expected in s["expect_fields"].items():
            actual = result.get(field)
            if actual != expected:
                problems.append(f"{field}: expected '{expected}', got '{actual}'")

        mark = "FAIL" if problems else "pass"
        if problems:
            failed += 1
        else:
            passed += 1

        print(f"[{mark}] {s['title']}")
        print(f"       status : {result['status']}"
              + (f"  ({result['reason']})" if result.get("reason") else ""))

        if result["status"] in (LEAD, NEEDS_REVIEW):
            if result.get("emergency"):
                print("       *** EMERGENCY - alert the plumber, do not book ***")
            for field in ("name", "phone", "email", "job_type", "address",
                          "urgency", "property_type", "appliances"):
                value = result.get(field)
                if value:
                    print(f"       {field:<13}: {value}")
            if result.get("missing"):
                print(f"       would ask: {', '.join(result['missing'])}")

        for p in problems:
            print(f"       ^^^ {p}")
        print()

    print("=" * 62)
    print(f"  {passed} passed, {failed} failed, {len(SAMPLES)} total")
    print("=" * 62)


if __name__ == "__main__":
    run()
