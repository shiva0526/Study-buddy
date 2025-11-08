import requests, json

BASE = "http://localhost:8000/api/v1"

print("Health:", requests.get("http://localhost:8000/api/health").text)

username = "demo_user"
r = requests.get(f"{BASE}/users/{username}")
print("User:", r.json())

data = {"username": username, "subject": "Physics"}
r = requests.post(f"{BASE}/plans/create", data=data)
print("Create plan:", r.json())

plan_id = r.json()["plan_id"]
r = requests.post(f"{BASE}/sessions/start", json={"topic": "Optics"})
print("Session:", r.json())

r = requests.post(f"{BASE}/quizzes/generate", json={"topic": "Optics"})
print("Quiz:", r.json())

r = requests.post(f"{BASE}/quizzes/submit", json={"answers": [0, 1, 0]})
print("Submit Quiz:", r.json())

r = requests.post(f"{BASE}/revision/generate")
print("Revision:", r.json())
