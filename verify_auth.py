from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

login_response = client.post('/api/auth/login', json={'email': 'user@example.com', 'password': 'Password123!'})
print('login_status', login_response.status_code)
print('login_body', login_response.json())

if login_response.status_code != 200:
    raise SystemExit(1)

token = login_response.json()['access_token']

research_response = client.post('/api/research', headers={'Authorization': f'Bearer {token}'}, json={
    'competitors': ['OpenAI'],
    'topics': ['AI'],
    'urls': ['https://example.com'],
    'context': 'test context',
})
print('research_status', research_response.status_code)
print('research_body', research_response.json())

if research_response.status_code != 200:
    raise SystemExit(2)

history_response = client.get('/api/history', headers={'Authorization': f'Bearer {token}'})
print('history_status', history_response.status_code)
print('history_body', history_response.json())

if history_response.status_code != 200:
    raise SystemExit(3)
