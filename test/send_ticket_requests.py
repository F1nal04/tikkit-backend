
import requests
from uuid import uuid4
from enum import Enum

# Enums für die Ticket-Daten


class Topic(str, Enum):
    printer = "printer"
    nas = "nas"
    wifi = "wifi"
    lan = "lan"
    macbook = "macbook"
    imac = "imac"
    other = "other"


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


test_users = [str(uuid4()) for _ in range(3)]


test_tickets = [
    {
        "topic": Topic.printer.value,
        "description": "Drucker im 2. Stock druckt keine Farben mehr",
        "priority": Priority.high.value,
        "author": test_users[0],
        "message": "Bitte dringend prüfen, wichtige Präsentation morgen"
    },
    {
        "topic": Topic.wifi.value,
        "description": "WLAN-Signal im Konferenzraum sehr schwach",
        "priority": Priority.medium.value,
        "author": test_users[1],
        "message": "Verbindungsabbrüche während Meetings"
    },
    {
        "topic": Topic.macbook.value,
        "description": "MacBook startet nicht mehr nach Update",
        "priority": Priority.high.value,
        "author": test_users[2],
        "message": "Grauer Bildschirm beim Start"
    },
    {
        "topic": Topic.nas.value,
        "description": "Zugriff auf gemeinsamen Ordner nicht möglich",
        "priority": Priority.medium.value,
        "author": test_users[0],
        "message": "Fehlermeldung: Zugriff verweigert"
    },
    {
        "topic": Topic.imac.value,
        "description": "Software-Installation erforderlich",
        "priority": Priority.low.value,
        "author": test_users[1],
        "message": "Bitte Adobe Suite installieren"
    },
    {
        "topic": Topic.lan.value,
        "description": "Ethernet-Verbindung im Büro 105 ausgefallen",
        "priority": Priority.high.value,
        "author": test_users[2],
        "message": "Kompletter Ausfall seit heute Morgen"
    },
    {
        "topic": Topic.other.value,
        "description": "Bildschirm-Kalibrierung erforderlich",
        "priority": Priority.low.value,
        "author": test_users[0],
        "message": "Farben werden falsch dargestellt"
    },
    {
        "topic": Topic.printer.value,
        "description": "Papierstau im Hauptdrucker",
        "priority": Priority.medium.value,
        "author": test_users[1],
        "message": "Kann nicht behoben werden"
    },
    {
        "topic": Topic.wifi.value,
        "description": "Neues WLAN-Passwort benötigt",
        "priority": Priority.low.value,
        "author": test_users[2],
        "message": "Für Gast-Netzwerk"
    },
    {
        "topic": Topic.macbook.value,
        "description": "Battery Service erforderlich",
        "priority": Priority.medium.value,
        "author": test_users[0],
        "message": "Akku hält nur noch 1 Stunde"
    }
]


endpoint = "http://localhost:8000/ticket"
headers = {"Content-Type": "application/json"}

for i, ticket_data in enumerate(test_tickets, 1):
    try:
        response = requests.post(endpoint, json=ticket_data, headers=headers)
        print(f"\nTicket {i}:")
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Erfolgreich erstellt!")
            print(f"Response: {response.json()}")
        else:
            print(f"Fehler: {response.text}")
    except Exception as e:
        print(f"Fehler beim Senden von Ticket {i}: {str(e)}")
