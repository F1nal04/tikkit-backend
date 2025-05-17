from fastapi.security import api_key
from openai import OpenAI
from dotenv import load_dotenv
import os
from models import Ticket
from rich.console import Console
from rich.progress import Progress
from rich.markdown import Markdown

load_dotenv()

api_key = os.getenv("OPENAI_KEY")
client = OpenAI(api_key=api_key)


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
    The user cant answer back.
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
    instructions = generate_instructions(ticket)
    prompt = generate_prompt(ticket)
    response = client.responses.create(
        model="gpt-4.1-mini",
        instructions=instructions,
        input=prompt
    )
    return response.output_text

# response = client.responses.create(
#     model="gpt-4.1-nano",
#     input="Hello! What Model are you?"
# )

# print(response.output_text)


if __name__ == "__main__":
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
