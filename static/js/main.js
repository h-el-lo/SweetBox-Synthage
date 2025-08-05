// Main JavaScript for SweetBox Synthage

document.addEventListener('DOMContentLoaded', function() {
    // Profile Sidebar Functionality
    const sidebar = document.getElementById('profileSidebar');
    const overlay = document.getElementById('sidebarOverlay');
    const toggleBtn = document.getElementById('profileSidebarToggle');
    const closeBtn = document.getElementById('closeSidebarBtn');
    
    if (toggleBtn && sidebar && overlay) {
        toggleBtn.addEventListener('click', function() {
            sidebar.classList.add('open');
            overlay.classList.add('open');
        });
        
        overlay.addEventListener('click', function() {
            sidebar.classList.remove('open');
            overlay.classList.remove('open');
        });
        
        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                sidebar.classList.remove('open');
                overlay.classList.remove('open');
            });
        }
    }
    
    // Mobile profile icon triggers sidebar
    const mobileProfileBtn = document.getElementById('mobileProfileSidebarToggle');
    if (mobileProfileBtn && sidebar && overlay) {
        mobileProfileBtn.addEventListener('click', function() {
            sidebar.classList.add('open');
            overlay.classList.add('open');
        });
    }
    
    // Remove inline styles from primary buttons
    document.querySelectorAll('.btn.btn-primary').forEach(function(btn) {
        btn.removeAttribute('style');
    });
    
    // Hamburger Animation
    const hamburger = document.getElementById('hamburger');
    const navbarToggler = document.querySelector('.navbar-toggler');
    
    if (navbarToggler) {
        navbarToggler.addEventListener('click', function() {
            if (hamburger) {
                hamburger.classList.toggle('active');
            }
        });
    }
    
    // Close mobile menu when clicking on links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', function() {
            if (window.innerWidth < 992) {
                const navbarCollapse = document.getElementById('navbarNav');
                if (navbarCollapse) {
                    const bsCollapse = new bootstrap.Collapse(navbarCollapse, {toggle: false});
                    bsCollapse.hide();
                    if (hamburger) {
                        hamburger.classList.remove('active');
                    }
                }
            }
        });
    });
    
    // Auto-hide mobile menu on window resize
    window.addEventListener('resize', function() {
        if (window.innerWidth >= 992) {
            if (hamburger) {
                hamburger.classList.remove('active');
            }
        }
    });
    
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Auto-hide alerts
    setTimeout(function() {
        document.querySelectorAll('.alert-success').forEach(function(alert) {
            alert.classList.add('fade');
            setTimeout(function() {
                alert.remove();
            }, 500);
        });
    }, 5000);
}); 