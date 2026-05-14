async function toggleLike(btn, pictureId) {
    try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
        const response = await fetch(`/api/like/${pictureId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            }
        });
        
        if (!response.ok) {
            if (response.status === 401) {
                window.location.href = '/login';
                return;
            }
            throw new Error('Failed to toggle like');
        }
        
        const data = await response.json();
        const svg = btn.querySelector('svg');
        
        if (data.is_liked) {
            btn.classList.remove('text-white', 'bg-white/5', 'border-white/10');
            btn.classList.add('text-rose-500', 'bg-rose-500/10', 'border-rose-500/50');
            svg.setAttribute('fill', 'currentColor');
        } else {
            btn.classList.remove('text-rose-500', 'bg-rose-500/10', 'border-rose-500/50');
            btn.classList.add('text-white', 'bg-white/5', 'border-white/10');
            svg.setAttribute('fill', 'none');
        }

        // Reload if on profile page to update lists
        if (window.location.pathname === '/profile') {
            window.location.reload();
        }
    } catch (error) {
        console.error('Error toggling like:', error);
    }
}
