# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import kernel_function

_BASE_SYSTEM_MSG = (
    "You are a helpful travel planning assistant. Always be professional and provide accurate information."
)


class FlightPLugin:
    @kernel_function
    def search_flights(self, origin: str, destination: str, date: str) -> str:
        """Search for available flights."""
        available_flights = [
            {"flight_id": "FL123"},
            {"flight_id": "FL456"},
            {"flight_id": "FL789"},
        ]
        return f"Available flights from {origin} to {destination} on {date}:\n{available_flights}"

    @kernel_function
    def book_flight(self, flight_id: str) -> str:
        """Book a specific flight."""
        return f"Successfully booked flight with ID {flight_id}."

    @kernel_function
    def process_payment(self, amount: float) -> str:
        """Process payment for bookings."""
        return f"Payment of ${amount} processed successfully for flight booking."


class HotelPlugin:
    @kernel_function
    def search_hotels(self, location: str, check_in: str, check_out: str) -> str:
        """Search for available hotels."""
        available_hotels = [
            {"hotel_id": "HT123", "name": "Hotel Sunshine"},
            {"hotel_id": "HT456", "name": "Ocean View Resort"},
            {"hotel_id": "HT789", "name": "Mountain Retreat"},
        ]
        return f"Searching hotels in {location} from {check_in} to {check_out}:\n{available_hotels}"

    @kernel_function
    def book_hotel(self, hotel_id: str) -> str:
        """Book a specific hotel."""
        return f"Successfully booked hotel with ID {hotel_id}."

    @kernel_function
    def process_payment(self, amount: float) -> str:
        """Process payment for bookings."""
        return f"Payment of ${amount} processed successfully for hotel booking."


class GeneralPlugin:
    @kernel_function
    def get_weather(self, location: str) -> str:
        """Get weather information for a location."""
        return f"Weather information for {location}: Sunny, 25°C."

    @kernel_function
    def search_destinations(self, query: str) -> str:
        """Search for travel destinations."""
        return f"Results for '{query}':\n1. Paris\n2. New York\n3. Tokyo\n4. Bali\n5. Sydney"


def get_agents() -> list[ChatCompletionAgent]:
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
        description="Creates comprehensive travel plans and breaks down user requests",
        instructions=f"{_BASE_SYSTEM_MSG} You create detailed travel plans and identify what needs to be done.",
        service=AzureChatCompletion(),
        plugins=[GeneralPlugin()],
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
        plugins=[GeneralPlugin()],
    )

    # 5. Flight Agent
    flight_agent = ChatCompletionAgent(
        name="flight_agent",
        description="Specializes in flight search and booking",
        instructions=f"{_BASE_SYSTEM_MSG} You handle all flight-related tasks including search and booking.",
        service=AzureChatCompletion(),
        plugins=[FlightPLugin()],
    )

    # 6. Hotel Agent
    hotel_agent = ChatCompletionAgent(
        name="hotel_agent",
        description="Specializes in hotel search and booking",
        instructions=f"{_BASE_SYSTEM_MSG} You handle all hotel-related tasks including search and booking.",
        service=AzureChatCompletion(),
        plugins=[HotelPlugin()],
    )

    return [
        conversation_manager,
        planner,
        router,
        destination_expert,
        flight_agent,
        hotel_agent,
    ]
