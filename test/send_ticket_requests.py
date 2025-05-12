import requests
import random
from enum import Enum


class Priority(Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Topic(Enum):
    printer = "printer"
    nas = "nas"
    wifi = "wifi"
    lan = "lan"
    macbook = "macbook"
    imac = "imac"
    other = "other"


API_URL = "http://localhost:8000"
LOGIN_ENDPOINT = f"{API_URL}/token"
TICKET_ENDPOINT = f"{API_URL}/ticket"

user_credentials = [
    {"email": "leongaborbojanowski04@gmail.com",
        "password": "Test1234", "name": "Leon Gabor Bojanowski"},
    {"email": "user1@example.com", "password": "Test1234", "name": "User 1"},
    {"email": "user2@example.com", "password": "Test1234", "name": "User 2"},
    {"email": "user3@example.com", "password": "Test1234", "name": "User 3"},
]

user_tokens = []

for i, creds in enumerate(user_credentials, 1):
    # Login to get token and user ID
    login_data = {"username": creds["email"], "password": creds["password"]}
    login_resp = requests.post(LOGIN_ENDPOINT, data=login_data)
    if login_resp.status_code == 200:
        token = login_resp.json()["access_token"]
        user_tokens.append(token)
    else:
        print(f"User {i} login error: {login_resp.text}")
        user_tokens.append(None)


test_tickets = [
    {
        "topic": Topic.printer.value,
        "description": "Drucker im 2. Stock druckt keine Farben mehr",
        "priority": Priority.high.value,
        "message": "Bitte dringend prüfen, wichtige Präsentation morgen"
    },
    {
        "topic": Topic.wifi.value,
        "description": "WLAN-Signal im Konferenzraum sehr schwach",
        "priority": Priority.medium.value,
        "message": "Verbindungsabbrüche während Meetings"
    },
    {
        "topic": Topic.macbook.value,
        "description": "MacBook startet nicht mehr nach Update",
        "priority": Priority.high.value,
        "message": "Grauer Bildschirm beim Start"
    },
    {
        "topic": Topic.nas.value,
        "description": "Zugriff auf gemeinsamen Ordner nicht möglich",
        "priority": Priority.medium.value,
        "message": "Fehlermeldung: Zugriff verweigert"
    },
    {
        "topic": Topic.imac.value,
        "description": "Software-Installation erforderlich",
        "priority": Priority.low.value,
        "message": "Bitte Adobe Suite installieren"
    },
    {
        "topic": Topic.lan.value,
        "description": "Ethernet-Verbindung im Büro 105 ausgefallen",
        "priority": Priority.high.value,
        "message": "Kompletter Ausfall seit heute Morgen"
    },
    {
        "topic": Topic.other.value,
        "description": "Bildschirm-Kalibrierung erforderlich",
        "priority": Priority.low.value,
        "message": "Farben werden falsch dargestellt"
    },
    {
        "topic": Topic.printer.value,
        "description": "Papierstau im Hauptdrucker",
        "priority": Priority.medium.value,
        "message": "Kann nicht behoben werden"
    },
    {
        "topic": Topic.wifi.value,
        "description": "Neues WLAN-Passwort benötigt",
        "priority": Priority.low.value,
        "message": "Für Gast-Netzwerk"
    },
    {
        "topic": Topic.macbook.value,
        "description": "Battery Service erforderlich",
        "priority": Priority.medium.value,
        "message": "Akku hält nur noch 1 Stunde"
    }
]


for i, ticket_data in enumerate(test_tickets, 1):
    random_index = random.randint(0, len(user_tokens))
    token = user_tokens[random_index]
    ticket_data = ticket_data.copy()
    headers = {"Content-Type": "application/json",
               "Authorization": f"Bearer {token}"}
    try:
        response = requests.post(
            TICKET_ENDPOINT, json=ticket_data, headers=headers)
        print(f"\nTicket {i}:")
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Erfolgreich erstellt!")
            print(f"Response: {response.json()}")
        else:
            print(f"Fehler: {response.text}")
    except Exception as e:
        print(f"Fehler beim Senden von Ticket {i}: {str(e)}")
