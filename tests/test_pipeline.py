import os
import sys
from fastapi.testclient import TestClient

# Add the project root folder to the sys.path list to resolve relative imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.core.config import settings

client = TestClient(app)

def run_health_test() -> None:
    print(">>> 1. Testing /health API endpoint...")
    response = client.get("/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response JSON: {response.json()}")
    assert response.status_code == 200
    print("Health check test passed!\n")

def run_upload_test() -> None:
    print(">>> 2. Testing /api/v1/document/upload API endpoint...")
    sample_file = os.path.join("data", "sample.txt")
    
    if not os.path.exists(sample_file):
        print(f"Error: Test file not found at {sample_file}")
        sys.exit(1)
        
    with open(sample_file, "rb") as f:
        response = client.post(
            "/api/v1/document/upload",
            files={"file": ("sample.txt", f, "text/plain")}
        )
        
    print(f"Status Code: {response.status_code}")
    print(f"Response JSON: {response.json()}")
    assert response.status_code == 201
    print("Document upload and local indexing test passed!\n")

def run_query_test() -> None:
    print(">>> 3. Testing /api/v1/document/query API endpoint...")
    response = client.post(
        "/api/v1/document/query",
        json={"query": "What is quantum superposition?", "k": 2}
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response JSON: {response.json()}")
    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) > 0
    print("Vector search query test passed!\n")

def run_chat_test() -> None:
    print(">>> 4. Testing /api/v1/chat RAG Chat endpoint...")
    session_id = "test-session-123"
    
    # First query
    print("--- Turn 1 (Initial Question) ---")
    query_1 = "What is Retrieval-Augmented Generation?"
    response_1 = client.post(
        "/api/v1/chat",
        json={"session_id": session_id, "query": query_1, "k": 2}
    )
    print(f"Status Code: {response_1.status_code}")
    print(f"Response: {response_1.json()['answer']}")
    print(f"Citations: {len(response_1.json()['citations'])} source(s) referenced.")
    assert response_1.status_code == 200
    
    # Second query (follow-up test to verify context-aware memory expansion)
    print("\n--- Turn 2 (Contextual Follow-up) ---")
    query_2 = "How does it reduce hallucinations?"
    response_2 = client.post(
        "/api/v1/chat",
        json={"session_id": session_id, "query": query_2, "k": 2}
    )
    print(f"Status Code: {response_2.status_code}")
    print(f"Response: {response_2.json()['answer']}")
    print(f"Citations: {len(response_2.json()['citations'])} source(s) referenced.")
    assert response_2.status_code == 200
    print("RAG chat session tests passed!\n")

def run_session_clear_test() -> None:
    print(">>> 5. Testing DELETE /api/v1/chat/session/{session_id} endpoint...")
    session_id = "test-session-123"
    response = client.delete(f"/api/v1/chat/session/{session_id}")
    print(f"Status Code: {response.status_code}")
    print(f"Response JSON: {response.json()}")
    assert response.status_code == 200
    
    # Try deleting again (should return 404 since it's already cleared)
    response_retry = client.delete(f"/api/v1/chat/session/{session_id}")
    print(f"Delete retry Status Code: {response_retry.status_code} (expected 404)")
    assert response_retry.status_code == 404
    print("Session clearing tests passed!\n")

if __name__ == "__main__":
    print("==================================================")
    print("RUNNING END-TO-END LOCAL PIPELINE TESTS")
    print("==================================================")
    
    # Ensure settings is set to local mode for this test
    if settings.MODEL_PROVIDER != "local":
         print("Warning: MODEL_PROVIDER is not set to 'local'. Setting it to 'local' for this offline test.")
         settings.MODEL_PROVIDER = "local"
         
    try:
        run_health_test()
        run_upload_test()
        run_query_test()
        run_chat_test()
        run_session_clear_test()
        print("==================================================")
        print("ALL END-TO-END LOCAL TESTS PASSED")
        print("==================================================")
    except AssertionError as e:
        print(f"Pipeline assertion check failed: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected pipeline test failure: {str(e)}")
        sys.exit(1)
