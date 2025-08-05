// Theme Toggle JavaScript for SweetBox Synthage

(function() {
    const body = document.body;
    const sidebarToggleBtn = document.getElementById('theme-toggle-sidebar');
    const sidebarIcon = document.getElementById('theme-icon-sidebar');
    
    function setTheme(dark) {
        if (dark) {
            body.classList.add('dark-mode');
            if (sidebarIcon) sidebarIcon.className = 'bi bi-moon-fill';
            localStorage.setItem('theme', 'dark');
        } else {
            body.classList.remove('dark-mode');
            if (sidebarIcon) sidebarIcon.className = 'bi bi-sun-fill';
            localStorage.setItem('theme', 'light');
        }
    }
    
    // Initialize theme
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    setTheme(savedTheme === 'dark' || (!savedTheme && prefersDark));
    
    // Theme toggle handler (sidebar)
    if (sidebarToggleBtn) {
        sidebarToggleBtn.addEventListener('click', function() {
            setTheme(!body.classList.contains('dark-mode'));
        });
    }
    
    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
        if (!localStorage.getItem('theme')) {
            setTheme(e.matches);
        }
    });
})(); 