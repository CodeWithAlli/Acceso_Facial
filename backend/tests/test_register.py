# backend/tests/test_register.py
import pytest
from backend.app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c

def test_registro_sin_nombre(client):
    res = client.post('/api/registro',
                      json={'dni': '12345678', 'tipo_persona': 'empleado',
                            'imagen_base64': 'data:image/jpeg;base64,AAAA'},
                      content_type='application/json')
    assert res.status_code == 400

def test_registro_sin_dni(client):
    res = client.post('/api/registro',
                      json={'nombre_completo': 'Test Prueba', 'tipo_persona': 'empleado',
                            'imagen_base64': 'data:image/jpeg;base64,AAAA'},
                      content_type='application/json')
    assert res.status_code == 400

def test_registro_sin_imagen(client):
    res = client.post('/api/registro',
                      json={'nombre_completo': 'Test Prueba', 'dni': '12345678',
                            'tipo_persona': 'empleado'},
                      content_type='application/json')
    assert res.status_code == 400

def test_registro_tipo_persona_invalido(client):
    res = client.post('/api/registro',
                      json={'nombre_completo': 'Test Prueba', 'dni': '12345678',
                            'tipo_persona': 'invitado',
                            'imagen_base64': 'data:image/jpeg;base64,AAAA'},
                      content_type='application/json')
    assert res.status_code == 400
