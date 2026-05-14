import json
import os
import zlib
import struct
import random

def save_png(filename, width, height, pixels):
    """Saves a list of (r, g, b) tuples as a PNG file using only standard library."""
    def chunk(type, data):
        return struct.pack('>I', len(data)) + type + data + struct.pack('>I', zlib.crc32(type + data) & 0xffffffff)

    png_signature = b'\x89PNG\r\n\x1a\n'
    ihdr = chunk(b'IHDR', struct.pack('>2I5B', width, height, 8, 2, 0, 0, 0))
    
    img_data = b''
    for y in range(height):
        img_data += b'\x00'  # Filter type 0 (None)
        for x in range(width):
            img_data += struct.pack('3B', *pixels[y * width + x])
            
    idat = chunk(b'IDAT', zlib.compress(img_data))
    iend = chunk(b'IEND', b'')
    
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'wb') as f:
        f.write(png_signature + ihdr + idat + iend)

def generate_random_art(seed_val):
    """Generates a list of pixels for a 32x32 image based on a seed."""
    random.seed(seed_val)
    width, height = 32, 32
    
    # Keeping the exact same color style base palette
    bg_color = (random.randint(20, 50), random.randint(20, 50), random.randint(50, 100))
    fg_color = (random.randint(150, 255), random.randint(150, 255), random.randint(150, 255))
    accent = (random.randint(150, 255), random.randint(50, 100), random.randint(50, 100))
    
    pixels = [bg_color] * (width * height)
    
    # Expanded from 3 to 7 distinct types of generative art
    art_type = random.randint(0, 6)
    
    if art_type == 0: # Random rectangles
        for _ in range(random.randint(4, 10)):
            x1, y1 = random.randint(0, 25), random.randint(0, 25)
            w, h = random.randint(4, 12), random.randint(4, 12)
            col = random.choice([fg_color, accent])
            for iy in range(y1, min(y1+h, height)):
                for ix in range(x1, min(x1+w, width)):
                    pixels[iy * width + ix] = col
                    
    elif art_type == 1: # Chunky Symmetrical Invaders
        for _ in range(15):
            x, y = random.randint(2, 14), random.randint(2, 28)
            col = random.choice([fg_color, accent])
            # Use 2x2 pixel blocks for a chunkier retro look
            for dy in range(2):
                for dx in range(2):
                    if y+dy < height and x+dx < width:
                        pixels[(y+dy) * width + (x+dx)] = col
                        # Mirror horizontally
                        pixels[(y+dy) * width + (31 - (x+dx))] = col
                        
    elif art_type == 2: # Crosses/Grid
        spacing = random.randint(4, 8)
        offset = random.randint(0, 3)
        for i in range(offset, 32, spacing):
            for j in range(32):
                pixels[i * 32 + j] = fg_color
                pixels[j * 32 + i] = accent
                
    elif art_type == 3: # Bubbles / Circles
        for _ in range(random.randint(4, 10)):
            cx, cy = random.randint(4, 28), random.randint(4, 28)
            r = random.randint(2, 8)
            col = random.choice([fg_color, accent])
            for y in range(height):
                for x in range(width):
                    if (x - cx)**2 + (y - cy)**2 <= r**2:
                        pixels[y * width + x] = col
                        
    elif art_type == 4: # Diagonal Stripes
        stripe_width = random.randint(3, 7)
        direction = random.choice([1, -1])
        for y in range(height):
            for x in range(width):
                val = (x + direction * y) // stripe_width
                if val % 3 == 0:
                    pixels[y * width + x] = fg_color
                elif val % 3 == 1:
                    pixels[y * width + x] = accent
                    
    elif art_type == 5: # Concentric Tunnels
        step = random.randint(3, 5)
        for y in range(height):
            for x in range(width):
                # Chebyshev distance for square shapes
                dist = max(abs(x - 15.5), abs(y - 15.5))
                val = int(dist) // step
                if val % 2 == 0:
                    pixels[y * width + x] = fg_color
                elif val % 3 == 0:
                    pixels[y * width + x] = accent
                    
    elif art_type == 6: # Random Walkers (Worms/Circuit traces)
        for _ in range(random.randint(3, 6)):
            x, y = random.randint(5, 26), random.randint(5, 26)
            col = random.choice([fg_color, accent])
            for _ in range(random.randint(30, 80)):
                pixels[y * width + x] = col
                # Thicken the trace slightly so it's visible
                if x < 31: pixels[y * width + x + 1] = col
                if y < 31: pixels[(y+1) * width + x] = col
                
                dx, dy = random.choice([(0,1), (0,-1), (1,0), (-1,0)])
                x = max(0, min(31, x + dx))
                y = max(0, min(31, y + dy))

    return pixels

def seed_database():
    from app import db, User, Picture, Interest
    
    # 1. Create a sample user if none exists
    if not User.query.filter_by(username='pixel_artist').first():
        sample_user = User(
            username='pixel_artist',
            email='artist@example.com',
            profile_description='Curator of algorithmically generated pixel vibes.'
        )
        sample_user.set_password('password123')
        db.session.add(sample_user)
        db.session.commit()
    
    user = User.query.filter_by(username='pixel_artist').first()

    if user and not user.interests:
        sample_interests = Interest.query.filter(Interest.name.in_([
            'Art',
            'Photography',
            'Tech'
        ])).all()
        user.interests = sample_interests
        db.session.commit()

    # 2. Add sample pictures if the table is empty
    if not Picture.query.first():
        print("Generating 20 sample artworks...")
        owned_ids = []
        
        adjectives = ["Cosmic", "Neon", "Cyber", "Retro", "Digital", "Abstract", "Techno", "Vivid"]
        nouns = ["Dream", "Wave", "Grid", "Portal", "Logic", "Pulse", "Zenith", "Flow"]
        all_interests = Interest.query.all()
        
        for i in range(20):
            filename = f'seed_art_{i}.png'
            filepath = os.path.join('static', 'uploads', filename)
            
            # Generate actual pixel data
            pixel_data = generate_random_art(f"seed_{i}")
            save_png(filepath, 32, 32, pixel_data)
            
            desc = f"{random.choice(adjectives)} {random.choice(nouns)} #{i+1}"
            
            pic = Picture(
                filename=filename,
                description=desc,
                user_id=user.id
            )

            if all_interests:
                pic.tags = random.sample(all_interests, k=random.randint(0, 3))

            db.session.add(pic)
            db.session.flush() # Get ID
            owned_ids.append(pic.id)
        
        # Update user's owned pictures
        user.owned_pictures_ids = json.dumps(owned_ids)
        db.session.commit()
        print("Database seeded with 20 unique artworks!")
    else:
        print("Database already contains content, skipping seed.")

if __name__ == '__main__':
    from app import app
    with app.app_context():
        seed_database()
