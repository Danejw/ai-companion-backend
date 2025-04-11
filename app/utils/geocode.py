import httpx


async def reverse_geocode(latitude: float, longitude: float) -> str:
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {
        "lat": latitude,
        "lon": longitude,
        "format": "json",
        "zoom": 10,
    }
    headers = {
        "User-Agent": "AICompanion/1.0 (aicompanion@gmail.com)"  # Nominatim requires this
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data.get("display_name", "Unknown location")
        except Exception as e:
            print("Reverse geocode failed:", e)
            return "Unknown location"