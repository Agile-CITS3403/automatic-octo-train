| UWA ID        | Name                  | Github Username  |
| ------------- |:----------------------| :-----|
| 22615371      | Ziri Wang             |        |
| 24537803      | Dean Sing Fat         | DSF100 |
| 24185633      | Ruslan Veselov        | rakkateichou |
| 23913198      | Nicholas Evan Anargya | kepepsi |


# LowRezGram
This is the repo for the group project for CITS3403 - Agile Web Development.

## Project Description
LowRezGram is a pixel art social app. Users create drawings on a 32x32 canvas, upload them to the server, and explore a community feed with likes and profile galleries.

## List of Features
- User authentication (sign up, log in, log out)
- Drawing studio with a fixed 32x32 canvas and curated palette
- Upload drawings to the server with an optional description
- Community feed with fullscreen viewing and pixel-grid overlay
- Likes system with per-user like tracking
- Profile page showing owned pictures and liked items
- Lightweight migrations runner for evolving the SQLite schema

## Technologies Used
- Backend: Flask, Flask-Login, Flask-SQLAlchemy, SQLite
- Frontend: HTML, Tailwind CSS (CLI build), vanilla JS
- Tooling: Python-dotenv, Tailwind CLI

## The Flow of the User Experience
1. Land on the home page and sign up or log in.
2. Browse the feed or open the drawing studio.
3. Draw on the 32x32 canvas and save to upload.
4. View new uploads in the feed or on your profile.
5. Like drawings to curate your liked items list.

## Important Design Decisions
- Keep the drawing grid fixed at 32x32 for a consistent pixel-art look.
- Store drawings as PNGs in static uploads for quick retrieval.
- Provide a simple like toggle instead of complex social graphs.
- Keep the UI focused on drawing and browsing.

## Setup and Running

### Python
1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the app:
   ```bash
   python app.py
   ```
   The app runs on http://localhost:5001.

### CSS Build (Tailwind)
1. Install Node dependencies:
   ```bash
   npm install
   ```
2. Build CSS once:
   ```bash
   npm run build:css
   ```
3. Or run the watcher during development:
   ```bash
   npm run dev:css
   ```

## Notes
- Set `SECRET_KEY` in your environment for production use.
- Database migrations run automatically on app startup.