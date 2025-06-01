from dotenv import load_dotenv
import os
from ..models import Ticket
from rich.console import Console
from rich.progress import Progress
from rich.markdown import Markdown

load_dotenv()

api_key = os.getenv("OPENAI_KEY")

# Only initialize OpenAI client if API key is available
client = None
if api_key:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
    except ImportError:
        # Handle case where openai package might not be installed
        client = None


def generate_instructions(ticket: Ticket) -> str:
    instructions = """
    You are an IT support specialist.
    The user is a person aged between 20 and 50 years old.
    The user is not a technical expert.
    The user is not a child.

    You will get a broad topic of the issue.
    You will get a small description of the issue.
    You will get additional information if available.

    Do give solutions that are clear, and concise
    Answer in German.
    Do not include any additional information or context.
    The user can't answer back.
    """
    return instructions


def generate_prompt(ticket: Ticket) -> str:
    prompt: str
    prompt = f"""I need help with the following technical issue:
    """

    prompt += f"""
                Problem Category: {ticket.topic.value}
                Specific Issue: {ticket.description}
    """

    # Add additional context if provided
    if ticket.message and ticket.message.strip():
        prompt += f"""
                Additional Information: {ticket.message}
        """

    return prompt


def get_response(ticket: Ticket):
    if not client:
        raise RuntimeError(
            "OpenAI client is not available. Please set OPENAI_KEY environment variable.")

    instructions = generate_instructions(ticket)
    prompt = generate_prompt(ticket)
    response = client.responses.create(
        model="gpt-4.1-mini",
        instructions=instructions,
        input=prompt
    )
    return response.output_text


def is_ai_available() -> bool:
    """Check if AI functionality is available."""
    return client is not None


if __name__ == "__main__":
    if not client:
        print("Error: OpenAI API key not configured. Please set OPENAI_KEY environment variable.")
        exit(1)

    console = Console()
    progress = Progress()
    response = None
    while True:
        user_input = input("User: ")
        if user_input.lower() == "exit":
            break
        if not response:
            response = client.responses.create(
                model="gpt-4.1-nano",
                input=user_input
            )
        else:
            response = client.responses.create(
                model="gpt-4.1-nano",
                previous_response_id=response.id,
                input=user_input
            )
        console.print(Markdown("AI: " + response.output_text))
