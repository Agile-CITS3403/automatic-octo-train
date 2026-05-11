import os
import json
import base64
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from migrations import run_all_migrations

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-fallback-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    owned_pictures_ids = db.Column(db.Text, default='[]')
    profile_description = db.Column(db.Text, default='')
    likes = db.Column(db.Text, default='[]')

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
        filepath = os.path.join('static', 'uploads', filename)
        
        with open(filepath, 'wb') as f:
            f.write(base64.b64decode(image_data))
        
        new_picture = Picture(filename=filename, user_id=current_user.id, description=description)
        db.session.add(new_picture)
        
        # Also update owned_pictures_ids for the user
        owned_ids = json.loads(current_user.owned_pictures_ids)
        # We'll store the filename or ID. Let's store the ID as the field name suggests.
        db.session.flush() # To get the new_picture.id
        owned_ids.append(new_picture.id)
        current_user.owned_pictures_ids = json.dumps(owned_ids)
        
        db.session.commit()
        return json.dumps({'success': True, 'filename': filename}), 201
    except Exception as e:
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
        return redirect(url_for('draw'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('draw'))
        else:
            flash('Invalid username or password')
            
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('draw'))

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
            return redirect(url_for('draw'))
            
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
    user_likes_ids = json.loads(current_user.likes)
    
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

@app.route('/feed')
@login_required
def feed():
    pictures = Picture.query.order_by(Picture.created_at.desc()).all()
    user_likes = json.loads(current_user.likes)
    
    pics_with_users = []
    for p in pictures:
        u = User.query.get(p.user_id)
        pics_with_users.append({
            'pic': p, 
            'username': u.username if u else 'Unknown',
            'is_liked': p.id in user_likes
        })
    return render_template('feed.html', pictures=pics_with_users)

@app.route('/api/like/<int:picture_id>', methods=['POST'])
@login_required
def toggle_like(picture_id):
    picture = Picture.query.get_or_404(picture_id)
    likes = json.loads(current_user.likes)
    
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

if __name__ == '__main__':
    app.run(debug=True, port=5001)
