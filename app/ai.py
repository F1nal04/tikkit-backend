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


def generate_prompt(ticket: Ticket) -> str:
    prompt = f"""As an IT support specialist, I need solutions for the following technical issue:
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

    # Add the request for solutions
    prompt += f"""
            Please provide:
            1. A brief analysis of what might be causing this issue
            2. Step-by-step troubleshooting instructions that a non-technical user could follow
            3. Any preventative measures to avoid this issue in the future

            Make the solutions clear, concise, and appropriate for the technical level of a typical office worker.
            Answer in German. Do not include any additional information or context. The User cant answer back.
        """

    return prompt


def get_response(ticket: Ticket):
    prompt = generate_prompt(ticket)
    response = client.responses.create(
        model="gpt-4.1-mini",
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
