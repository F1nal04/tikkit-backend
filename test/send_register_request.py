import requests

test_users = [
    {
        "email": "leongaborbojanowski04@gmail.com",
        "password": "Test1234",
        "name": "Leon Gabor Bojanowski"
    },
    {
        "email": "user1@example.com",
        "password": "Test1234",
        "name": "User 1"
    },
    {
        "email": "user2@example.com",
        "password": "Test1234",
        "name": "User 2"
    },
    {
        "email": "user3@example.com",
        "password": "Test1234",
        "name": "User 3"
    },
    {
        "email": "user4@example.com",
        "password": "Test1234",
        "name": "User 4"
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
