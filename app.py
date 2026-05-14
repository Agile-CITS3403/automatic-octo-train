import os
import json
import base64
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from migrations import run_all_migrations

INTEREST_OPTIONS = [
    'Music',
    'Fashion',
    'Gaming',
    'Memes',
    'Photography',
    'Art',
    'Food',
    'Sports',
    'Cars',
    'Anime',
    'Movies',
    'Campus life',
    'Study',
    'Travel',
    'Fitness',
    'Tech'
]

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-fallback-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

csrf = CSRFProtect(app)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# User Model
user_interests = db.Table(
    'user_interest',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('interest_id', db.Integer, db.ForeignKey('interest.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    owned_pictures_ids = db.Column(db.Text, default='[]')
    profile_description = db.Column(db.Text, default='')
    likes = db.Column(db.Text, default='[]')
    interests = db.relationship('Interest', secondary=user_interests, back_populates='users')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Picture Model
class Picture(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

class Interest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    users = db.relationship('User', secondary=user_interests, back_populates='interests')

def ensure_interests():
    existing = {interest.name for interest in Interest.query.all()}
    missing = [name for name in INTEREST_OPTIONS if name not in existing]
    if missing:
        db.session.add_all([Interest(name=name) for name in missing])
        db.session.commit()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('front_page.html')

@app.route('/draw')
@login_required
def draw():
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
@login_required
def upload_picture():
    data = request.get_json()
    if not data or 'image' not in data:
        return json.dumps({'error': 'No image data'}), 400
    
    image_data = data['image']
    description = data.get('description', '')
    # Remove metadata prefix if present (e.g., "data:image/png;base64,")
    if ',' in image_data:
        image_data = image_data.split(',')[1]
    
    try:
        filename = f"{uuid.uuid4()}.png"
        upload_dir = os.path.join('static', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, filename)
        
        with open(filepath, 'wb') as f:
            f.write(base64.b64decode(image_data))
        
        new_picture = Picture(filename=filename, user_id=current_user.id, description=description)
        db.session.add(new_picture)
        
        # Also update owned_pictures_ids for the user
        owned_ids = json.loads(current_user.owned_pictures_ids or '[]')
        # We'll store the filename or ID. Let's store the ID as the field name suggests.
        db.session.flush() # To get the new_picture.id
        owned_ids.append(new_picture.id)
        current_user.owned_pictures_ids = json.dumps(owned_ids)
        
        db.session.commit()
        return json.dumps({'success': True, 'filename': filename}), 201
    except Exception as e:
        import traceback
        print(f"UPLOAD ERROR: {str(e)}")
        traceback.print_exc()
        db.session.rollback()
        return json.dumps({'error': str(e)}), 500

@app.route('/api/pictures', methods=['GET'])
def get_pictures():
    pictures = Picture.query.order_by(Picture.created_at.desc()).all()
    return json.dumps([{
        'id': p.id,
        'url': url_for('static', filename='uploads/' + p.filename),
        'user_id': p.user_id
    } for p in pictures])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('feed'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('feed'))
        else:
            flash('Invalid username or password')
            
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('feed'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        user_exists = User.query.filter((User.username == username) | (User.email == email)).first()
        if user_exists:
            flash('Username or email already exists')
        else:
            new_user = User(username=username, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('interests'))
            
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.profile_description = request.form.get('profile_description')
        db.session.commit()
        flash('Profile updated successfully!')
        return redirect(url_for('profile'))
    
    owned_pictures = Picture.query.filter_by(user_id=current_user.id).order_by(Picture.created_at.desc()).all()
    user_likes_ids = json.loads(current_user.likes or '[]')
    
    # Prepare owned pictures with like status
    owned_pics_with_status = []
    for p in owned_pictures:
        owned_pics_with_status.append({
            'pic': p,
            'is_liked': p.id in user_likes_ids
        })
    
    # Fetch liked pictures objects
    liked_pictures_objs = Picture.query.filter(Picture.id.in_(user_likes_ids)).all() if user_likes_ids else []
    
    # Map them with username and like status (always true here)
    liked_pics_with_status = []
    for p in liked_pictures_objs:
        u = User.query.get(p.user_id)
        liked_pics_with_status.append({
            'pic': p,
            'username': u.username if u else 'Unknown',
            'is_liked': True
        })
    
    return render_template('profile.html', 
                         user=current_user, 
                         owned_pictures=owned_pics_with_status, 
                         liked_pictures=liked_pics_with_status)

@app.route('/interests', methods=['GET', 'POST'])
@login_required
def interests():
    ensure_interests()
    if request.method == 'POST':
        selected_ids = request.form.getlist('interests')
        selected_ids = [int(i) for i in selected_ids if i.isdigit()]
        selected_interests = Interest.query.filter(Interest.id.in_(selected_ids)).all()
        current_user.interests = selected_interests
        db.session.commit()
        flash('Interests updated successfully!')
        return redirect(url_for('profile'))

    interest_options = Interest.query.order_by(Interest.name.asc()).all()
    selected_ids = {interest.id for interest in current_user.interests}
    return render_template('interest.html',
                           interest_options=interest_options,
                           selected_ids=selected_ids)

@app.route('/feed')
@login_required
def feed():
    pictures = Picture.query.order_by(Picture.created_at.desc()).all()
    user_likes = json.loads(current_user.likes or '[]')
    
    pics_with_users = []
    for p in pictures:
        u = User.query.get(p.user_id)
        pics_with_users.append({
            'pic': p, 
            'username': u.username if u else 'Unknown',
            'is_liked': p.id in user_likes
        })
    return render_template('feed.html', pictures=pics_with_users)

@app.route('/picture/<int:picture_id>')
def view_picture(picture_id):
    picture = Picture.query.get_or_404(picture_id)
    u = User.query.get(picture.user_id)
    
    is_liked = False
    if current_user.is_authenticated:
        user_likes = json.loads(current_user.likes or '[]')
        is_liked = picture_id in user_likes
    
    # Context-aware back button
    back_url = url_for('feed')
    back_label = 'Back to Feed'
    referrer = request.referrer
    if referrer and '/profile' in referrer:
        back_url = url_for('profile')
        back_label = 'Back to Profile'
        
    return render_template('picture_view.html', 
                         pic=picture, 
                         username=u.username if u else 'Unknown', 
                         is_liked=is_liked,
                         back_url=back_url,
                         back_label=back_label)

@app.route('/api/like/<int:picture_id>', methods=['POST'])
@login_required
def toggle_like(picture_id):
    picture = Picture.query.get_or_404(picture_id)
    likes = json.loads(current_user.likes or '[]')
    
    if picture_id in likes:
        likes.remove(picture_id)
        is_liked = False
    else:
        likes.append(picture_id)
        is_liked = True
        
    current_user.likes = json.dumps(likes)
    db.session.commit()
    
    return json.dumps({'success': True, 'is_liked': is_liked}), 200

with app.app_context():
    db.create_all()
    run_all_migrations()
    ensure_interests()
    from seed_data import seed_database
    seed_database()

if __name__ == '__main__':
    app.run(debug=True, port=5001)
