# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import kernel_function

_BASE_SYSTEM_MSG = (
    "You are a helpful travel planning assistant. Always be professional and provide accurate information."
)


class FlightPlugin:
    @kernel_function
    def book_flight(self, flight_id: str) -> str:
        """Book a specific flight."""
        return f"Successfully booked flight with ID {flight_id}. Your booking reference is FLX12345."


class HotelPlugin:
    @kernel_function
    def book_hotel(self, hotel_id: str) -> str:
        """Book a specific hotel."""
        return f"Successfully booked hotel with ID {hotel_id}. Your booking reference is HTX12345."


class PlanningPlugin:
    @kernel_function
    def get_weather(self, location: str) -> str:
        """Get weather information for a location."""
        return f"Weather information for {location}: Sunny, 25°C."

    @kernel_function
    def search_hotels(self, location: str, check_in: str, check_out: str) -> str:
        """Search for available hotels."""
        available_hotels = [
            {"hotel_id": "HT123", "name": "Hotel Sunshine", "price": "$150/night", "accommodates": "2 people"},
            {"hotel_id": "HT456", "name": "Ocean View Resort", "price": "$200/night", "accommodates": "4 people"},
            {"hotel_id": "HT789", "name": "Mountain Retreat", "price": "$180/night", "accommodates": "2 people"},
        ]
        return f"Searching hotels in {location} from {check_in} to {check_out}:\n{available_hotels}"

    @kernel_function
    def search_flights(self, origin: str, destination: str, date: str) -> str:
        """Search for available flights."""
        available_flights = [
            {"flight_id": "FL123", "take-off-time": "10:00 AM", "arrival-time": "12:00 PM", "price": "$200"},
            {"flight_id": "FL456", "take-off-time": "2:00 PM", "arrival-time": "4:00 PM", "price": "$250"},
            {"flight_id": "FL789", "take-off-time": "6:00 PM", "arrival-time": "8:00 PM", "price": "$300"},
        ]
        return f"Available flights from {origin} to {destination} on {date}:\n{available_flights}"


def get_agents() -> dict[str, ChatCompletionAgent]:
    """Creates and returns a set of agents for the travel planning system."""
    # 1. Conversation Manager Agent
    conversation_manager = ChatCompletionAgent(
        name="conversation_manager",
        description="Manages conversation flow and coordinates between agents",
        instructions=f"{_BASE_SYSTEM_MSG} You coordinate the conversation and ensure users get comprehensive help.",
        service=AzureChatCompletion(),
    )

    # 2. Travel Planner Agent
    planner = ChatCompletionAgent(
        name="planner",
        description="Creates comprehensive travel plans including flights, hotels, and activities",
        instructions=(
            f"{_BASE_SYSTEM_MSG} You create detailed travel plans that include flights, hotels, and activities."
        ),
        service=AzureChatCompletion(),
        plugins=[PlanningPlugin()],
    )

    # 3. Router Agent
    router = ChatCompletionAgent(
        name="router",
        description="Routes tasks to appropriate specialized agents",
        instructions=f"{_BASE_SYSTEM_MSG} You analyze plans and delegate tasks to the right specialized agents.",
        service=AzureChatCompletion(),
    )

    # 4. Destination Expert Agent
    destination_expert = ChatCompletionAgent(
        name="destination_expert",
        description="Expert in destination recommendations and local information",
        instructions=(
            f"{_BASE_SYSTEM_MSG} You provide expert advice on destinations, attractions, and local experiences."
        ),
        service=AzureChatCompletion(),
        plugins=[PlanningPlugin()],
    )

    # 5. Flight Agent
    flight_agent = ChatCompletionAgent(
        name="flight_agent",
        description="Specializes in flight booking",
        instructions=f"{_BASE_SYSTEM_MSG} You handle all flight-related tasks including booking.",
        service=AzureChatCompletion(),
        plugins=[FlightPlugin()],
    )

    # 6. Hotel Agent
    hotel_agent = ChatCompletionAgent(
        name="hotel_agent",
        description="Specializes in hotel booking",
        instructions=f"{_BASE_SYSTEM_MSG} You handle all hotel-related tasks including booking.",
        service=AzureChatCompletion(),
        plugins=[HotelPlugin()],
    )

    return {
        conversation_manager.name: conversation_manager,
        planner.name: planner,
        router.name: router,
        destination_expert.name: destination_expert,
        flight_agent.name: flight_agent,
        hotel_agent.name: hotel_agent,
    }
