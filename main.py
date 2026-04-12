import requests
import os
import smtplib
import ssl
from datetime import datetime
from dotenv import load_dotenv
import Path

# CNOSTS
PROJECT_DIR = Path(__file__).resolve().parent


def scrape():
    url = "https://www.hertzfreerider.se/api/transport-routes"

    querystring = {"country":"SWEDEN"}

    payload = ""

    headers = {
        "Accept": "application/json, text/plain, */*",
        # "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Referer": "https://www.hertzfreerider.se/sv-se/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "TE": "trailers",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:145.0) Gecko/20100101 Firefox/145.0"
    }

    response = requests.request("GET", url, headers=headers, data=payload, params=querystring)

    # print(response.text)
    response_json = response.json()
    return response_json


"""
We want 
   - pickupLocationName
   - returnLocationName
    (routes[name]):
   - distance
   - originalDistance
   - travelTime
   - originalTravelTime
   - availableAt
   - latestReturn
   - expireTime
   - carModel

data from the json. 
"""


def parse(response):
    parsed_objects = []

    # Go through all the received adverts and get the data we want and send email for unsent
    for i, item in enumerate(response):
        # Routes is a list including duplicates of all ads with the same origin and goal, but we only care for unique ads.
        # Routes contains all the relevant data
        routes = item["routes"][0]

        availableAt = routes["availableAt"]
        latestReturn = routes["latestReturn"]
        expireTime = routes["expireTime"]

        ad_data = {
            # Origin and destination names
            "returnLocationName": item["returnLocationName"] ,
            "pickupLocationName": item["pickupLocationName"],

            "routes": routes,

            # Get all the relevant data from the json that we want to include in our mail
            "ad_id": routes["id"],
            "distance": routes["distance"],
            "originalDistance": routes["originalDistance"],
            "travelTime": routes["travelTime"],
            "originalTravelTime": routes["originalTravelTime"],

            "carModel": routes["carModel"],

            # date from source is on ISO-format "YYYY-MM-DDTHH:mm:ss"
            "availableAtfrmt": datetime.fromisoformat(availableAt).strftime("%d/%m"),
            "latestReturnfrmt": datetime.fromisoformat(latestReturn).strftime("%d/%m"),
            "expireTimefrmt": datetime.fromisoformat(expireTime).strftime("%H:%M %d/%m")
        }

        parsed_objects.append(ad_data)

    return parsed_objects


def send_mails(objects):
    # Read all the previously parsed ad ids
    with open("ids.txt", "r") as file:
        ids = file.readlines()

    # _delivery variables are for when there is a delivery to be done
    interested_pickup_locs_delivery = ["stockholm", "södertälje"]
    interested_return_locs_delivery = ["eslöv", "helsingborg", "hässleholm", "lund", "malmö"]

    # others are just for potential spontaneous trips
    interested_pickup_locs = ["eslöv", "helsingborg", "hässleholm", "lund", "malmö"]
    uninterested_return_locs = ["eslöv", "helsingborg", "hässleholm", "lund", "malmö", "ystad", "kristianstad"]

    # keep track of no. sent emails
    counter = 0
    for ad in objects:
        ad_id = ad["ad_id"]
        distance = ad["distance"]
        originalDistance = ad["originalDistance"]
        travelTime = ad["travelTime"]
        originalTravelTime = ad["originalTravelTime"]

        carModel = ad["carModel"]
        availableAtfrmt = ad["availableAtfrmt"]
        latestReturnfrmt = ad["latestReturnfrmt"]
        expireTimefrmt = ad["expireTimefrmt"]
        returnLocationName = ad["returnLocationName"]
        pickupLocationName = ad["pickupLocationName"]

        routes = ad["routes"]

        # Header/subject for generic car ad
        default_header = f"""Ny bil från {pickupLocationName.split()[0]} till {returnLocationName.split()[0]}  {latestReturnfrmt}! Boka senast {expireTimefrmt}."""

        # Header/subject for car ad for delivery
        delivery_header = f"""Ny bil från Stockholm till Skåne {latestReturnfrmt}! Boka senast {expireTimefrmt}."""

        # Email body, with formated datetime objects to not
        email = f"""Det finns en {carModel} att köra från {pickupLocationName} till {returnLocationName} som är tillgänglig mellan {availableAtfrmt} och {latestReturnfrmt}. Extra tid beräkad är {round(travelTime - originalTravelTime, 1)} minuter och extra sträcka är {round(distance - originalDistance, 1)} km. \n\nAnnonsen går ut {expireTimefrmt}.\n\nVisit at https://www.hertzfreerider.se/sv-se/."""

        # If we have already processed this ad, dont bother checking again
        ids_formatted = ",".join(ids).replace("\n", "")  # since ids list is \n separated 'in' will not work since every input has trailing \n
        if str(ad_id) in ids_formatted:
            print("Ad with id:", ad_id, "already parsed, skipping...")
            continue

        # Check if the specified locations exist in the posted pickup/return locations. Use any to check for any words in the list are present in the posted string.
        if (any(loc in pickupLocationName.lower() for loc in interested_pickup_locs_delivery) and any(
                loc in returnLocationName.lower() for loc in
                interested_return_locs_delivery)):
            # Send email with delivery header
            send_mail(delivery_header, email)
            counter += 1

        # Dont allow where pickup and return is in the same region
        elif (any(loc in pickupLocationName.lower() for loc in interested_pickup_locs) and not any(
                loc in returnLocationName.lower() for loc in uninterested_return_locs)):
            # Send email with generic header
            send_mail(default_header, email)
            counter += 1

        # add parsed id to file
        with open("ids.txt", "a+") as file:
            file.write(str(ad_id) + "\n")

    # Output results
    if counter == 0:
        print("Sent 0 mails (all ads were parsed already).")
    else:
        print("Sent", counter, "mails.")


def main():
    # Load all the environment variables and override in case there are old variables i dont want to keep
    load_dotenv(override=True)
    response_json = scrape()
    parse(response_json)


def get_time():
    # Helper function for getting the current time in a nice format
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    return current_time


def send_mail(header, content):
    # Setup and send mail
    receiver_email = os.getenv("receiver_email")
    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"
    # use environment variables for email login
    sender_email = os.getenv("sender_email")
    password = os.getenv("password")
    message = f"""\
Subject: {header}

{content}"""
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:

        print("Logging in!", get_time())
        server.login(sender_email, password)

        print("Sending mail", get_time())
        server.sendmail(sender_email, receiver_email, message.encode("utf-8"))

        print("Mail sent!", get_time())
        print()


if __name__ == "__main__":
    main()
