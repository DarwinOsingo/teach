import requests

API_URL = "http://localhost:8000/chat"
session_id = None

print("Chat started. Type 'quit' to exit, 'reset' to start a new session.\n")

while True:
    user_input = input("You: ").strip()
    
    if user_input.lower() == "quit":
        break
    
    if user_input.lower() == "reset":
        session_id = None
        print("Session reset.\n")
        continue
    
    if not user_input:
        continue

    payload = {
        "message": user_input,
        "session_id": session_id
    }

    try:
        response = requests.post(API_URL, json=payload)
        data = response.json()

        if response.status_code != 200:
            print(f"Error: {data['detail']}\n")
            continue

        session_id = data["session_id"]
        print(f"Jarvis: {data['reply']}\n")

    except Exception as e:
        print(f"Connection error: {e}\n")