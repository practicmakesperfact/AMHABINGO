"""
Quick test script to verify backend API is working
Run: python test_api.py
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("\n1. Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    return response.status_code == 200

def test_auth():
    """Test authentication"""
    print("\n2. Testing authentication...")
    response = requests.post(f"{BASE_URL}/api/users/auth")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   User ID: {data['id']}")
        print(f"   Username: {data['username']}")
        print(f"   Balance: {data['balance']}")
        return True, data['id']
    else:
        print(f"   Error: {response.text}")
        return False, None

def test_create_game():
    """Test game creation"""
    print("\n3. Testing game creation...")
    payload = {
        "room": "beginner",
        "entry_fee": 10.0,
        "max_players": 100
    }
    response = requests.post(
        f"{BASE_URL}/api/games/",
        json=payload
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Game ID: {data['game_id']}")
        print(f"   Status: {data['status']}")
        print(f"   Entry Fee: {data['entry_fee']}")
        return True, data['game_id']
    else:
        print(f"   Error: {response.text}")
        return False, None

def test_list_games():
    """Test listing games"""
    print("\n4. Testing list games...")
    response = requests.get(f"{BASE_URL}/api/games/")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        games = response.json()
        print(f"   Total games: {len(games)}")
        if games:
            print(f"   First game: {games[0]['game_id']}")
        return True
    else:
        print(f"   Error: {response.text}")
        return False

def test_available_cards(game_id):
    """Test getting available cards"""
    print("\n5. Testing available cards...")
    response = requests.get(f"{BASE_URL}/api/games/{game_id}/available-cards")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Total available: {data['total_available']}")
        print(f"   Total taken: {data['total_taken']}")
        return True
    else:
        print(f"   Error: {response.text}")
        return False

def main():
    print("=" * 50)
    print("AMHABINGO Backend API Test")
    print("=" * 50)
    
    # Test 1: Health
    if not test_health():
        print("\n❌ Health check failed! Is the backend running?")
        return
    
    # Test 2: Auth
    success, user_id = test_auth()
    if not success:
        print("\n❌ Authentication failed!")
        return
    
    # Test 3: Create game
    success, game_id = test_create_game()
    if not success:
        print("\n❌ Game creation failed!")
        return
    
    # Test 4: List games
    if not test_list_games():
        print("\n❌ List games failed!")
        return
    
    # Test 5: Available cards
    if not test_available_cards(game_id):
        print("\n❌ Available cards failed!")
        return
    
    print("\n" + "=" * 50)
    print("✅ All tests passed!")
    print("=" * 50)
    print("\nBackend is working correctly!")
    print("You can now use the frontend at http://localhost:3000")

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to backend!")
        print("Please start the backend with:")
        print("  cd backend")
        print("  python -m uvicorn app.main:app --reload")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
