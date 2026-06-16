document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.querySelector('.nav-toggle');
  const navMenu = document.querySelector('nav ul');

  toggle.addEventListener('click', () => {
    navMenu.classList.toggle('open');
  });

  const currentPage = location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('nav a').forEach(link => {
    if (link.getAttribute('href') === currentPage) {
      link.classList.add('active');
    }
  });
});
