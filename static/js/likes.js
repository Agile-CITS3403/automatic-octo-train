async function toggleLike(btn, pictureId) {
    try {
        const response = await fetch(`/api/like/${pictureId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
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
            btn.classList.remove('text-white');
            btn.classList.add('text-rose-500');
            svg.setAttribute('fill', 'currentColor');
        } else {
            btn.classList.remove('text-rose-500');
            btn.classList.add('text-white');
            svg.setAttribute('fill', 'none');
        }
    } catch (error) {
        console.error('Error toggling like:', error);
    }
}
