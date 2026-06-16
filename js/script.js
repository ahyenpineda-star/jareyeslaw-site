document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.querySelector('.nav-toggle');
  const navMenu = document.querySelector('nav > ul');

  toggle.addEventListener('click', () => {
    navMenu.classList.toggle('open');
  });

  document.querySelectorAll('.dropdown > a').forEach(dropdownLink => {
    dropdownLink.addEventListener('click', (e) => {
      if (window.innerWidth <= 900) {
        e.preventDefault();
        dropdownLink.parentElement.classList.toggle('open');
      }
    });
  });

  const currentPage = location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('nav a').forEach(link => {
    if (link.getAttribute('href') === currentPage) {
      link.classList.add('active');
    }
  });
});
