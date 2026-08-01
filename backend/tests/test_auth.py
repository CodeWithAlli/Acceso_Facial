# backend/tests/test_auth.py
import pytest
from backend.app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c

def test_evento_sin_imagen(client):
    res = client.post('/api/evento', json={}, content_type='application/json')
    assert res.status_code == 400
    assert b'imagen_base64' in res.data

def test_evento_imagen_invalida(client):
    res = client.post('/api/evento',
                      json={'imagen_base64': 'data:image/jpeg;base64,AAAA'},
                      content_type='application/json')
    assert res.status_code == 200
    data = res.get_json()
    assert data['acceso'] == False

def test_admin_login_credenciales_invalidas(client):
    res = client.post('/api/admin/login',
                      json={'usuario': 'no_existe', 'password': 'x'},
                      content_type='application/json')
    assert res.status_code == 401
