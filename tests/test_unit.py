import pytest
from app import app, db, User, Interest

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
        with app.app_context():
            db.drop_all()

def test_home_page(client):
    """Test that the home page loads correctly."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'LowResGram' in response.data

def test_user_registration(client):
    """Test successful user registration."""
    response = client.post('/signup', data={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Interests' in response.data  # Should redirect to interests
    
    with app.app_context():
        user = User.query.filter_by(username='testuser').first()
        assert user is not None
        assert user.email == 'test@example.com'

def test_user_login(client):
    """Test user login with correct and incorrect credentials."""
    # Register first
    client.post('/signup', data={
        'username': 'logintest',
        'email': 'login@test.com',
        'password': 'password'
    })
    client.get('/logout') # Ensure logged out
    
    # Correct login
    response = client.post('/login', data={
        'username': 'logintest',
        'password': 'password'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Feed' in response.data or b'LowResGram' in response.data
    
    client.get('/logout')
    
    # Incorrect login
    response = client.post('/login', data={
        'username': 'logintest',
        'password': 'wrongpassword'
    }, follow_redirects=True)
    assert b'Invalid username or password' in response.data

def test_profile_auth_required(client):
    """Test that the profile page requires authentication."""
    response = client.get('/profile', follow_redirects=True)
    assert response.request.path == '/login' # Redirected to login
    assert b'log in' in response.data.lower() or b'sign in' in response.data.lower()

def test_interest_update(client):
    """Test updating user interests."""
    # Setup user
    client.post('/signup', data=dict(username='interestuser', email='int@test.com', password='pwd'), follow_redirects=True)
    
    with app.app_context():
        # Ensure there is at least one interest available
        interest = Interest(name='Testing')
        db.session.add(interest)
        db.session.commit()
        interest_id = interest.id
        
    response = client.post('/interests', data={
        'interests': [str(interest_id)]
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Interests updated successfully!' in response.data
    
    with app.app_context():
        user = User.query.filter_by(username='interestuser').first()
        assert len(user.interests) == 1
        assert user.interests[0].name == 'Testing'