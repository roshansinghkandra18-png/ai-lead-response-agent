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
# SIGNATURE BLOCKS  --  added 15 August 2026 after real email test C2b failed.
#
# A work signature carries a switchboard, a fax and a website on EVERY email
# that person sends, whether they are ordering stationery or reporting a leak.
# What they typed themselves has to win. But their signature is still better
# than nothing, so it stays as a fallback.
# ---------------------------------------------------------------------------

sample(
    "25. A work signature holding the office switchboard", LEAD,
    """From: barbara@example.com
Subject: leaking radiator

Hi, this is Barbara. The radiator in our back office has been leaking
since Monday and there's a bucket under it now. Best number for me is
216-555-0644, I'm usually in after 10.

Thanks,

Barbara Nolan
Office Manager | Nolan & Sons Ltd
Tel: 216-555-9000  |  Fax: 216-555-9001
barbara.nolan@nolanandsons.example.com
www.nolanandsons.example.com
""",
    {"name": "Barbara", "phone": "216-555-0644"},
)

sample(
    "26. The only phone number is in the signature", LEAD,
    """From: john@example.com
Subject: blocked drain

Hi, my kitchen drain is blocked and water is backing up.

Thanks,
John Petrie
216-555-0400
""",
    {"phone": "216-555-0400"},
)

sample(
    "27. Writing for his wife, and giving her number not his", LEAD,
    """From: greg@example.com
Subject: leak under sink

Hi, this is Greg. There is a leak under the kitchen sink.
You can reach my wife on 216-555-0200 during the day.
""",
    {"name": "Greg", "phone": "216-555-0200",
     "phone_belongs_to": "their wife"},
)

sample(
    "30. Her own number, and her landlord's for when she can't answer", LEAD,
    """From: rita@example.com
Subject: toilet leaking

Hi, this is Rita Shaw. The upstairs toilet is leaking onto the floor.
My number is 216-555-0455. If you are coming and I don't pick up then
call my landlord on 216-555-0900.
""",
    {"name": "Rita Shaw", "phone": "216-555-0455",
     "other_phone": "216-555-0900", "other_phone_note": "their landlord"},
)

sample(
    "31. The second number is mentioned long before its owner", LEAD,
    """From: nina@example.com
Subject: boiler not firing

Hi, I'm Nina Patel. The boiler will not fire up at all.
Call me on 216-555-0311 if you come by 2, or else my landlord will open
the door to you, he is on 216-555-0912.
""",
    {"name": "Nina Patel", "phone": "216-555-0311",
     "other_phone": "216-555-0912", "other_phone_note": "their landlord"},
)

sample(
    "32. A signature switchboard is never offered as a second contact", LEAD,
    """From: barbara@example.com
Subject: leaking radiator

Hi, this is Barbara. The radiator has been leaking since Monday. Best
number for me is 216-555-0644.

Thanks,

Barbara Nolan
Office Manager | Nolan & Sons Ltd
Tel: 216-555-9000  |  Fax: 216-555-9001
""",
    {"name": "Barbara", "phone": "216-555-0644", "other_phone": None},
)


# ---------------------------------------------------------------------------
# BOLD AND ITALIC  --  added 15 August 2026 after real email test C3 failed.
#
# Gmail sends a formatted message TWICE: once as a web page, once as plain
# text where bold is written *like this*. We read the plain-text copy, so the
# marks arrive as though they were letters - and a customer got greeted as
# "Hi *Marcus,".
# ---------------------------------------------------------------------------

sample(
    "33. A form where the labels and values were made bold", LEAD,
    """From: noreply@joesplumbing.com
Subject: New Website Inquiry

*Name:* *Marcus Webb*
*Phone:* *(216) 555-0700*
*Email:* m.webb@example.com
*Service Needed:* *Drain Cleaning*
*Message:* Kitchen sink is *completely* blocked.
""",
    {"name": "Marcus Webb", "phone": "(216) 555-0700",
     "email": "m.webb@example.com", "job_type": "Drain Cleaning"},
)

sample(
    "34. Somebody typing loosely, with their name in bold", LEAD,
    """From: marcus@example.com
Subject: blocked sink

Hi, I'm *Marcus*. The kitchen sink is completely blocked.
My number is 216-555-0700.
""",
    {"name": "Marcus", "phone": "216-555-0700"},
)

sample(
    "35. Underscores in an email address are left alone", LEAD,
    """From: noreply@joesplumbing.com
Subject: New Contact Form Submission

Name: Jose Ramirez
Phone: (216) 555-0512
Email: jose_ramirez@example.com
Service Needed: Garbage Disposal Repair
""",
    {"name": "Jose Ramirez", "email": "jose_ramirez@example.com"},
)


# ---------------------------------------------------------------------------
# FALSE EMERGENCIES  --  added 15 August 2026 after real email test C6 failed.
#
# A subject line too long to fit on one line is FOLDED by the mail server and
# continued on the next, indented. Only the first line carries a label, so the
# rest landed in the message body as though the customer had typed it - and
# the website's own wording contained the word "urgent".
# ---------------------------------------------------------------------------

sample(
    "36. A long subject folded across lines must not reach the message", LEAD,
    """From: noreply@joesplumbing.com
Subject: New Contact Form Submission from the website contact page
 regarding an urgent plumbing matter concerning the downstairs
 bathroom and kitchen area

Name: Priya Raman
Phone: (614) 555-7788
Email: p.raman@example.com
Service Needed: Drain Cleaning
""",
    {"name": "Priya Raman", "job_type": "Drain Cleaning", "emergency": False},
)

sample(
    "37. A customer saying it is NOT urgent", LEAD,
    """From: noreply@joesplumbing.com
Subject: New Contact Form Submission

Name: Gerald Pike
Phone: (216) 555-0800
Email: g.pike@example.com
Service Needed: Faucet Replacement
Message: Not urgent at all, just whenever you have a free slot next month.
""",
    {"name": "Gerald Pike", "emergency": False},
)

sample(
    "38. A customer who really does mean urgent", LEAD,
    """From: noreply@joesplumbing.com
Subject: New Contact Form Submission

Name: Helen Ward
Phone: (330) 555-0119
Email: helen.ward@example.com
Service Needed: Leak Repair
Message: This is urgent, water is coming through the ceiling.
""",
    {"name": "Helen Ward", "emergency": True},
)

sample(
    "39. A flooding basement is still an emergency, no matter the wording", LEAD,
    """From: noreply@joesplumbing.com
Subject: New Contact Form Submission

Name: Angela Foster
Phone: (216) 555-0143
Email: angela.foster@example.com
Service Needed: Burst Pipe
Message: The basement is flooding, water everywhere, please hurry.
""",
    {"name": "Angela Foster", "emergency": True},
)


# ---------------------------------------------------------------------------
# THE JOB IN THE CUSTOMER'S OWN WORDS
# Added 15 August 2026 after real email test C2 failed. Louise described a
# dripping tap in one clear sentence and got back "your plumbing job" - a
# reply that proves nobody read her email.
# ---------------------------------------------------------------------------

sample(
    "40. A dripping tap, described in ordinary words", LEAD,
    """From: louise@example.com
Subject: dripping tap

Hi, this is Louise. The bathroom tap has been dripping for a week.
My number is 216-555-0455.
""",
    {"name": "Louise", "phone": "216-555-0455", "job_type": "Faucet"},
)

sample(
    "41. A word that merely CONTAINS a job word is not a job", SKIP_NOT_A_LEAD,
    """From: newsletter@officesupplies.example.com
Subject: August offers

Hi there,
Our summer sale on packing tape and adaptors is now on. Message us
about bulk pricing.
""",
)

sample(
    "42. A blocked drain described as clogged", LEAD,
    """From: dan@example.com
Subject: kitchen problem

Hi, I'm Dan Reeve. The kitchen sink is completely clogged and won't
drain at all. Reach me on 216-555-0611.
""",
    {"name": "Dan Reeve", "job_type": "Drain Cleaning"},
)

sample(
    "43. Low water pressure, which the word list never had", LEAD,
    """From: mei@example.com
Subject: shower problem

Hi, my name is Mei Chen. There is almost no pressure in the upstairs
shower any more. My number is 216-555-0388.
""",
    {"name": "Mei Chen", "job_type": "Water Pressure"},
)


# ---------------------------------------------------------------------------
# NAMES THAT LOOK LIKE NAMES
# Added 15 August 2026 after real email test C7. An emoji was swallowed into
# the name and filed in the plumber's spreadsheet as "Chloe Barnett" with a
# smiley face after it. The customer never saw it - but the plumber did, and
# it does not look professional.
# ---------------------------------------------------------------------------

sample(
    "44. A customer who decorated her name with an emoji", LEAD,
    """From: noreply@joesplumbing.com
Subject: New message from your website

Name: Chloe Barnett \U0001F60E
Phone: (216) 555-0322
Email: chloe.b@example.com
Service Needed: Leak Repair
Message: Ceiling is dripping please help \U0001F62D\U0001F62D
""",
    {"name": "Chloe Barnett", "email": "chloe.b@example.com"},
)

sample(
    "45. Emoji in the MESSAGE are stripped too - nothing the plumber "
    "reads has smiley faces in it", LEAD,
    """From: noreply@joesplumbing.com
Subject: New Contact Form Submission

Name: Chloe Barnett
Phone: (216) 555-0322
Email: chloe.b@example.com
Service Needed: Leak Repair
Message: Ceiling is dripping please help \U0001F62D
""",
    {"message": "Ceiling is dripping please help"},
)

sample(
    "47. Accents, dashes and ordinary punctuation survive the emoji strip",
    LEAD,
    """From: noreply@joesplumbing.com
Subject: New Contact Form Submission

Name: Jose Ramirez
Phone: (216) 555-0512
Email: jose.ramirez@example.com
Service Needed: Garbage Disposal Repair
Message: Disposal hums, but doesn't turn - it's been like that since
Monday. Cost?
""",
    {"name": "Jose Ramirez",
     "message": "Disposal hums, but doesn't turn - it's been like that since\nMonday. Cost?"},
)

sample(
    "48. A bold email address must not keep its asterisks", LEAD,
    """From: noreply@joesplumbing.com
Subject: New Website Inquiry

Name: Marcus Webb
Phone: (216) 555-0700
Email: *m.webb@example.com *
Service Needed: Drain Cleaning
""",
    {"name": "Marcus Webb", "email": "m.webb@example.com"},
)

sample(
    "49. An email address with an underscore is still left alone", LEAD,
    """From: noreply@joesplumbing.com
Subject: New Contact Form Submission

Name: Ana Silva
Phone: (216) 555-0733
Email: ana_silva.99@example.co.uk
Service Needed: Leak Repair
""",
    {"name": "Ana Silva", "email": "ana_silva.99@example.co.uk"},
)


# ---------------------------------------------------------------------------
# THE FORM'S QUESTIONS ARE NOT THE CUSTOMER'S WORDS
# Added 15 August 2026 after real email test D3 failed. Thumbtack asks "Is any
# part of the building currently flooded?" on EVERY lead. Denise answered No
# and had a dripping tap - and the agent declared a flooding emergency because
# the word was sitting in the question.
# ---------------------------------------------------------------------------

sample(
    "50. A form QUESTION containing an emergency word, answered No", LEAD,
    """From: leads@thumbtack.com
Subject: New lead: Plumbing

Customer: Denise W.
Is any part of the building currently flooded?: No
Which appliances, if any, are affected?: Kitchen faucet
What type of property do you have?: Condo
When do you need this job to start?: Within a few days
Send a message to the pro: Bathroom faucet dripping constantly.
Zip: 44113
Phone: (216) 555-0355
""",
    {"name": "Denise W.", "emergency": False, "job_type": "Faucet"},
)

sample(
    "51. The same form question, answered YES, is still an emergency", LEAD,
    """From: leads@thumbtack.com
Subject: New lead: Plumbing

Customer: Denise W.
Is any part of the building currently flooded?: Yes
Which appliances, if any, are affected?: Kitchen faucet
When do you need this job to start?: Right away
Send a message to the pro: Water is coming up through the floor.
Zip: 44113
Phone: (216) 555-0355
""",
    {"name": "Denise W.", "emergency": True},
)

sample(
    "52. An emergency the customer describes in their own answer", LEAD,
    """From: leads@thumbtack.com
Subject: New lead: Plumbing

Customer: Marcus T.
Is any part of the building currently flooded?: No
Send a message to the pro: A pipe has burst under the kitchen sink and
water is gushing out.
Zip: 44113
Phone: (216) 555-0361
""",
    {"name": "Marcus T.", "emergency": True},
)


# ---------------------------------------------------------------------------
# CAPS LOCK
# Added 16 August 2026 after real email test E1 failed. Walter typed with caps
# lock on and the agent shouted his own name back at him.
# ---------------------------------------------------------------------------

sample(
    "53. A form filled in entirely with caps lock on", LEAD,
    """From: noreply@joesplumbing.com
Subject: NEW CONTACT FORM SUBMISSION

NAME: WALTER KIM
PHONE: (216) 555-0955
EMAIL: W.KIM@EXAMPLE.COM
SERVICE NEEDED: SEWER LINE INSPECTION
""",
    {"name": "Walter Kim", "job_type": "Sewer Line Inspection",
     "email": "W.KIM@EXAMPLE.COM"},
)

sample(
    "54. An acronym is still allowed to shout", LEAD,
    """From: noreply@joesplumbing.com
Subject: NEW CONTACT FORM SUBMISSION

NAME: DIANE WALSH
PHONE: (216) 555-0388
EMAIL: d.walsh@example.com
SERVICE NEEDED: HVAC MAINTENANCE
""",
    {"name": "Diane Walsh", "job_type": "HVAC Maintenance"},
)

sample(
    "55. A name that already has small letters is left alone", LEAD,
    """From: noreply@joesplumbing.com
Subject: New Contact Form Submission

Name: Mary-Anne O'Brien
Phone: (216) 555-0755
Email: ma.obrien@example.com
Service Needed: Toilet Installation
""",
    {"name": "Mary-Anne O'Brien", "job_type": "Toilet Installation"},
)


# ---------------------------------------------------------------------------
# A FORM FIELD IS A BOX
# Added 16 August 2026 after real email test E2 failed. The note explaining a
# second phone number ran backwards out of the message, across two other form
# fields, and came out as "com Leak Detection Call my mobile 216-555-0801...".
# ---------------------------------------------------------------------------

sample(
    "56. The note about a second number stays inside its own field", LEAD,
    """From: noreply@joesplumbing.com
Subject: New Contact Form Submission

Name: Ian Prescott
Phone: (216) 555-0733
Email: ian.prescott@example.com
Service Needed: Leak Detection
Message: Call my mobile 216-555-0801 if the house phone doesn't answer.
""",
    {"name": "Ian Prescott", "phone": "(216) 555-0733",
     "other_phone": "216-555-0801",
     "other_phone_said":
         "Call my mobile 216-555-0801 if the house phone doesn't answer."},
)

sample(
    "57. A wrapped sentence in free text is still kept whole", LEAD,
    """From: rita@example.com
Subject: toilet leaking

Hi, this is Rita Shaw. The upstairs toilet is leaking onto the floor.
My number is 216-555-0455. If you are coming and I don't pick up then
call my landlord on 216-555-0900.
""",
    {"name": "Rita Shaw", "phone": "216-555-0455",
     "other_phone": "216-555-0900", "other_phone_note": "their landlord",
     "other_phone_said":
         "If you are coming and I don't pick up then call my landlord on "
         "216-555-0900."},
)

sample(
    "46. Real names keep their apostrophes, hyphens and accents", LEAD,
    """From: noreply@joesplumbing.com
Subject: New Contact Form Submission

Name: Mary-Anne O'Brien
Phone: (216) 555-0755
Email: ma.obrien@example.com
Service Needed: Toilet Installation
""",
    {"name": "Mary-Anne O'Brien"},
)

sample(
    "28. His own number AND his landlord's", LEAD,
    """From: owen@example.com
Subject: water heater

Hi, I'm Owen Fletcher. The water heater has stopped working.
My number is 216-555-0777. I rent - my landlord's number is
216-555-0900 if you need access.
""",
    {"name": "Owen Fletcher", "phone": "216-555-0777"},
)

sample(
    "29. A phone field with the fax number on the same line", LEAD,
    """From: noreply@joesplumbing.com
Subject: New Contact Form Submission

Name: Helen Ward
Tel: 330-555-0119  |  Fax: 330-555-0120
Service Needed: Faucet Replacement
""",
    {"name": "Helen Ward", "phone": "330-555-0119"},
)


# ---------------------------------------------------------------------------
# THE TEST RUNNER
# ---------------------------------------------------------------------------

def _describe(status, fields):
    """Turn a status and some fields into one readable line."""
    parts = [f"status {status}"]
    for field, value in fields.items():
        shown = f'"{value}"' if value is not None else "nothing"
        parts.append(f"{field} {shown}")
    return "; ".join(parts)


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

        # --- FED IN: the actual email the agent was handed ---
        print("       fed in  : an email that reads -")
        for line in s["raw"].strip().splitlines():
            print(f"            {line}")

        # --- EXPECTED ---
        print(f"       expected: {_describe(s['expect_status'], s['expect_fields'])}")

        # --- GOT ---
        got_fields = {f: result.get(f) for f in s["expect_fields"]}
        print(f"       got     : {_describe(result['status'], got_fields)}")
        if result.get("reason"):
            print(f"                 (reason: {result['reason']})")

        # --- everything else it worked out, beyond what we checked ---
        if result["status"] in (LEAD, NEEDS_REVIEW):
            extras = []
            if result.get("emergency"):
                extras.append("*** EMERGENCY - alert the plumber, do not book ***")
            for field in ("name", "phone", "email", "job_type", "address",
                          "urgency", "property_type", "appliances"):
                value = result.get(field)
                if value and field not in s["expect_fields"]:
                    extras.append(f"{field} \"{value}\"")
            if result.get("missing"):
                extras.append(f"would ask for: {', '.join(result['missing'])}")
            if extras:
                print(f"       also    : {'; '.join(extras)}")

        for p in problems:
            print(f"       ^^^ {p}")
        print()

    print("=" * 70)
    print(f"  {passed} passed, {failed} failed, {len(SAMPLES)} total")
    print("=" * 70)


if __name__ == "__main__":
    run()
