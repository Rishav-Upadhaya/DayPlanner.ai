from app.services import graphrag


def test_embed_and_retrieve_vector_memory(client, auth_headers, monkeypatch) -> None:
    class DummyModel:
        def encode(self, _text_input: str, normalize_embeddings: bool = True):
            del normalize_embeddings
            return [0.1] * 384

    monkeypatch.setattr(graphrag, '_get_embedding_model', lambda: DummyModel())

    add_response = client.post(
        '/api/v1/memory/context',
        headers=auth_headers,
        json={
            'node_type': 'preference',
            'content': 'I prefer deep work in mornings',
            'confidence': 'high',
        },
    )
    assert add_response.status_code == 200

    response = client.get('/api/v1/memory/context?query=morning+focus+time', headers=auth_headers)
    assert response.status_code == 200
    snippets = response.json()['snippets']
    assert any('morning' in snippet.lower() for snippet in snippets)


def test_memory_fallback_when_no_embeddings(client, auth_headers, monkeypatch) -> None:
    monkeypatch.setattr(graphrag, '_get_embedding_model', lambda: None)

    response = client.get('/api/v1/memory/context', headers=auth_headers)
    assert response.status_code == 200
    assert 'items' in response.json()
