

import asyncio
import requests

# url = "https://api.countrystatecity.in/v1/countries/IN/cities"

# headers = {
#   'X-CSCAPI-KEY': 'API_KEY'
# }

# response = requests.request("GET", url, headers=headers)

# print(response.text)


from fastapi import FastAPI
import httpx

# app = FastAPI()

# @app.get("/api/cities/{country}")


# async def get_cities_and_towns(country: str):
#     # Replace 'YOUR_MAPBOX_ACCESS_TOKEN' with your Mapbox access token
#     access_token = 'pk.eyJ1IjoibW5nYWFmYXIiLCJhIjoiY2xuc214aXB2MW9mYjJscWl0MjcyOTJzZyJ9.d5GjDt-nLQrAKJ32mT09wg'
#     url = f'https://api.mapbox.com/geocoding/v5/mapbox.places/{country}.json'

#     async with httpx.AsyncClient() as client:
#         response = await client.get(url, params={'access_token': access_token})
#         data = response.json()

#         try:
#             # Process the data and extract cities and towns
#             cities_and_towns = [feature['place_name']
#                                 for feature in data['features']]
#             print(cities_and_towns)
#         except KeyError:
#             # Return an empty list if no features are found
#             cities_and_towns = []
#     return {"cities_and_towns": cities_and_towns}


# # test get cities and towns await

# loop = asyncio.get_event_loop()
# loop.run_until_complete(get_cities_and_towns("Kuwait"))
# loop.close()
