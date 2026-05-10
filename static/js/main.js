// Elements
const screenMain = document.getElementById('screen-main');
const screenDraw = document.getElementById('screen-draw');
const screenFeed = document.getElementById('screen-feed');

const btnGoDraw = document.getElementById('btn-go-draw');
const btnGoFeed = document.getElementById('btn-go-feed');
const btnBacks = document.querySelectorAll('.btn-back');

const canvas = document.getElementById('paint-canvas');
const ctx = canvas.getContext('2d');
const colorPalette = document.getElementById('color-palette');
const btnClear = document.getElementById('btn-clear');
const btnSave = document.getElementById('btn-save');
const feedContainer = document.getElementById('feed-container');

// State
let isDrawing = false;
let currentColor = '#000000';
let lastX = 0;
let lastY = 0;

// Preselected colors (16 colors = 8 per row in the 8-column grid)
const colors = [
  '#000000', // Black
  '#4b5563', // Dark Gray
  '#9ca3af', // Gray
  '#ffffff', // White
  '#78350f', // Brown
  '#ef4444', // Red
  '#991b1b', // Dark Red
  '#f97316', // Orange
  '#facc15', // Yellow
  '#84cc16', // Lime
  '#22c55e', // Green
  '#166534', // Dark Green
  '#3b82f6', // Blue
  '#1e40af', // Dark Blue
  '#a855f7', // Purple
  '#ec4899', // Pink
];

function setupPalette() {
  colorPalette.innerHTML = '';
  colors.forEach(color => {
    const btn = document.createElement('button');
    btn.className = 'color-btn';
    btn.style.backgroundColor = color;
    if (color === currentColor) btn.classList.add('active');
    
    btn.addEventListener('click', () => {
      currentColor = color;
      document.querySelectorAll('.color-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
    });
    
    colorPalette.appendChild(btn);
  });
}

// Screen management
function showScreen(screenId) {
  [screenMain, screenDraw, screenFeed].forEach(s => s.classList.add('hidden'));
  document.getElementById(screenId).classList.remove('hidden');

  if (screenId === 'screen-feed') {
    renderFeed();
  }
}

btnGoDraw.addEventListener('click', () => showScreen('screen-draw'));
btnGoFeed.addEventListener('click', () => showScreen('screen-feed'));
btnBacks.forEach(btn => btn.addEventListener('click', () => showScreen('screen-main')));

// Drawing logic
function getCoordinates(e) {
  const rect = canvas.getBoundingClientRect();
  const scaleX = canvas.width / rect.width;
  const scaleY = canvas.height / rect.height;
  
  const clientX = e.touches ? e.touches[0].clientX : e.clientX;
  const clientY = e.touches ? e.touches[0].clientY : e.clientY;

  const x = Math.floor((clientX - rect.left) * scaleX);
  const y = Math.floor((clientY - rect.top) * scaleY);
  return { x, y };
}

function draw(e) {
  if (!isDrawing) return;
  e.preventDefault();
  
  // 1. Get the current mouse coordinates
  const { x, y } = getCoordinates(e);
  
  // 2. Calculate how far the mouse moved since the last frame
  const distanceX = x - lastX;
  const distanceY = y - lastY;
  
  // 3. Figure out how many "steps" we need to fill the gap.
  // We use whichever distance is bigger (X or Y) as our number of steps.
  const steps = Math.max(Math.abs(distanceX), Math.abs(distanceY));
  
  ctx.fillStyle = currentColor;

  if (steps === 0) {
    // If the mouse didn't move to a new pixel, just color the current one
    ctx.fillRect(x, y, 1, 1);
  } else {
    // 4. "Walk" from the last position to the new position
    for (let i = 0; i <= steps; i++) {
      // Calculate what percentage of the way we are (from 0.0 to 1.0)
      const progress = i / steps;
      
      // Find the pixel at this point along the path
      const moveX = lastX + (distanceX * progress);
      const moveY = lastY + (distanceY * progress);
      
      // Round to the nearest whole number to stay on the 32x32 grid
      ctx.fillRect(Math.round(moveX), Math.round(moveY), 1, 1);
    }
  }
  
  // 5. Update lastX and lastY so we know where to start the next line
  lastX = x;
  lastY = y;
}

canvas.addEventListener('mousedown', (e) => {
  isDrawing = true;
  const { x, y } = getCoordinates(e);
  lastX = x;
  lastY = y;
  draw(e);
});
canvas.addEventListener('mousemove', draw);
window.addEventListener('mouseup', () => isDrawing = false);

// Touch support
canvas.addEventListener('touchstart', (e) => {
  isDrawing = true;
  const { x, y } = getCoordinates(e);
  lastX = x;
  lastY = y;
  draw(e);
}, { passive: false });
canvas.addEventListener('touchmove', draw, { passive: false });
window.addEventListener('touchend', () => isDrawing = false);

btnClear.addEventListener('click', () => {
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
});

// Save logic
btnSave.addEventListener('click', async () => {
  const dataURL = canvas.toDataURL();
  
  try {
    const response = await fetch('/api/upload', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ image: dataURL })
    });
    
    if (!response.ok) throw new Error('Failed to upload');
    
    // Visual feedback
    const originalText = btnSave.innerText;
    btnSave.innerText = 'Saved!';
    btnSave.classList.replace('bg-emerald-600', 'bg-blue-600');
    setTimeout(() => {
      btnSave.innerText = originalText;
      btnSave.classList.replace('bg-blue-600', 'bg-emerald-600');
    }, 1500);
  } catch (error) {
    console.error('Error saving drawing:', error);
    alert('Failed to save drawing to server.');
  }
});

// Feed logic
async function renderFeed() {
  feedContainer.innerHTML = '<div class="col-span-full py-12 text-slate-400 font-medium">Loading...</div>';
  
  try {
    const response = await fetch('/api/pictures');
    const pictures = await response.json();
    
    feedContainer.innerHTML = '';

    if (pictures.length === 0) {
      feedContainer.innerHTML = '<div class="col-span-full py-12 text-slate-400 font-medium">No drawings yet. Start creating!</div>';
      return;
    }

    pictures.forEach(pic => {
      const img = document.createElement('img');
      img.src = pic.url;
      img.className = 'rounded-lg';
      feedContainer.appendChild(img);
    });
  } catch (error) {
    console.error('Error loading feed:', error);
    feedContainer.innerHTML = '<div class="col-span-full py-12 text-rose-400 font-medium">Error loading feed.</div>';
  }
}

// Initial state
function init() {
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  setupPalette();
}

init();
