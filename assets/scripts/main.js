// Footer year
document.getElementById('year').textContent = new Date().getFullYear();

// Lightbox: open full image when a figure with [data-full] is clicked
const lightbox = document.getElementById('lightbox');
const lightboxImg = lightbox.querySelector('.lightbox__img');
const closeBtn = lightbox.querySelector('.lightbox__close');

function openLightbox(src, alt) {
	lightboxImg.src = src;
	lightboxImg.alt = alt || '';
	lightbox.classList.add('open');
	lightbox.setAttribute('aria-hidden', 'false');
	document.body.style.overflow = 'hidden';
}

function closeLightbox() {
	lightbox.classList.remove('open');
	lightbox.setAttribute('aria-hidden', 'true');
	lightboxImg.src = '';
	document.body.style.overflow = '';
}

document.querySelectorAll('[data-full]').forEach((fig) => {
	fig.addEventListener('click', () => {
		const img = fig.querySelector('img');
		openLightbox(fig.dataset.full, img ? img.alt : '');
	});
});

closeBtn.addEventListener('click', closeLightbox);
lightbox.addEventListener('click', (e) => {
	if (e.target === lightbox) closeLightbox();
});
document.addEventListener('keydown', (e) => {
	if (e.key === 'Escape' && lightbox.classList.contains('open')) closeLightbox();
});
