import requests

test_users = [
    {
        "email": "user1@example.com",
        "password": "Leon2901",
        "name": "User 1"
    },
    {
        "email": "user2@example.com",
        "password": "Leon2901",
        "name": "User 2"
    },
]


endpoint = "http://localhost:8000/register"
headers = {"Content-Type": "application/json"}

for i, user_data in enumerate(test_users, 1):
    try:
        response = requests.post(endpoint, json=user_data, headers=headers)
        print(f"\nUser {i}:")
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Erfolgreich erstellt!")
            print(f"Response: {response.json()}")
        else:
            print(f"Fehler: {response.text}")
    except Exception as e:
        print(f"Fehler beim Senden von User {i}: {str(e)}")
