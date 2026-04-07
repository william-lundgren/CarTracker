import requests


def main():
    pass


def get_data():
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
    with open("results.json", "w") as file:
        file.write(response.text)


if __name__ == "__main__":
    main()
