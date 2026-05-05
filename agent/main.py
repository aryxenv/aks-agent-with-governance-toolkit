import json
from typing import Annotated
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import openmeteo_requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from agent_framework import Agent, tool
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential
from pydantic import Field

client = FoundryChatClient(
    project_endpoint="https://learning-model-resource.services.ai.azure.com",
    model="gpt-5-mini",
    credential=AzureCliCredential(),
)
openmeteo = openmeteo_requests.Client()


# helper for get_weather tool
def geocode_location(location: str) -> tuple[str, float, float]:
    query = urlencode({"q": location, "format": "jsonv2", "limit": 1})
    request = Request(
        f"https://nominatim.openstreetmap.org/search?{query}",
        headers={"User-Agent": "learn-aks-agent/0.1"},
    )

    try:
        with urlopen(request, timeout=10) as response:
            results = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise RuntimeError(f"Nominatim geocoding failed with HTTP {exc.code}.") from exc
    except URLError as exc:
        raise RuntimeError(f"Nominatim geocoding failed: {exc.reason}.") from exc

    if not results:
        raise ValueError(f"Could not find coordinates for location '{location}'.")

    match = results[0]
    return match["display_name"], float(match["lat"]), float(match["lon"])


@tool(approval_mode="never_require")
def get_weather(
    location: Annotated[str, Field(description="The location to get the weather for.")],
) -> str:
    """Get the current temperature in Celsius for a location."""
    display_name, latitude, longitude = geocode_location(location)

    responses = openmeteo.weather_api(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current": ["temperature_2m"],
            "temperature_unit": "celsius",
        },
    )

    current = responses[0].Current()
    temperature_celsius = current.Variables(0).Value()
    return f"The current temperature in {display_name} is {temperature_celsius:.1f}°C."


agent = Agent(
    client=client,
    name="WeatherAgent",
    instructions="You are a helpful weather agent. Use the get_weather tool to answer questions.",
    tools=[get_weather],
)
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Running!"}


@app.get("/health")
def health_check():
    return {"status": "agent server healthy"}


# main endpoint for the agent
@app.get("/chat")
async def chat(query: str):
    def sse(event: str, data: dict) -> str:
        return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"

    async def stream_response():
        emitted_tool_calls = set()
        emitted_formulating = False

        yield sse("status", {"message": "Thinking..."})

        async for chunk in agent.run(query, stream=True):
            for content in chunk.contents:
                if (
                    content.type == "function_call"
                    and content.call_id not in emitted_tool_calls
                ):
                    emitted_tool_calls.add(content.call_id)
                    yield sse(
                        "tool_call",
                        {
                            "tool": content.name,
                            "message": f"Calling {content.name}...",
                        },
                    )

                elif content.type == "function_result":
                    yield sse(
                        "tool_result",
                        {
                            "message": "Tool completed.",
                            "result": content.result,
                        },
                    )

                elif content.type == "usage":
                    yield sse("usage", content.usage_details or {})

            if chunk.text:
                if not emitted_formulating:
                    emitted_formulating = True
                    yield sse("status", {"message": "Formulating an answer..."})
                yield sse("message", {"text": chunk.text})

        yield sse("done", {"message": "Completed."})

    return StreamingResponse(
        stream_response(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )
