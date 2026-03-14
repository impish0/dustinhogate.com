// Dropdown keyboard accessibility
(function() {
    function initDropdowns() {
        var dropdowns = document.querySelectorAll('.dropdown');

        dropdowns.forEach(function(dropdown) {
            var toggle = dropdown.querySelector('.dropdown-toggle');
            var menu = dropdown.querySelector('.dropdown-menu');
            if (!toggle || !menu) return;

            var links = menu.querySelectorAll('a');
            var isOpen = false;

            // Add ARIA attributes
            toggle.setAttribute('aria-haspopup', 'true');
            toggle.setAttribute('aria-expanded', 'false');

            function openMenu() {
                isOpen = true;
                toggle.setAttribute('aria-expanded', 'true');
                menu.style.opacity = '1';
                menu.style.visibility = 'visible';
                menu.style.transform = 'translateY(0)';
            }

            function closeMenu() {
                isOpen = false;
                toggle.setAttribute('aria-expanded', 'false');
                menu.style.opacity = '';
                menu.style.visibility = '';
                menu.style.transform = '';
            }

            // Toggle on Enter/Space
            toggle.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    if (isOpen) {
                        closeMenu();
                    } else {
                        openMenu();
                        if (links.length > 0) links[0].focus();
                    }
                } else if (e.key === 'ArrowDown') {
                    e.preventDefault();
                    openMenu();
                    if (links.length > 0) links[0].focus();
                } else if (e.key === 'Escape') {
                    closeMenu();
                    toggle.focus();
                }
            });

            // Arrow key navigation in menu
            links.forEach(function(link, index) {
                link.addEventListener('keydown', function(e) {
                    if (e.key === 'ArrowDown') {
                        e.preventDefault();
                        var next = links[index + 1] || links[0];
                        next.focus();
                    } else if (e.key === 'ArrowUp') {
                        e.preventDefault();
                        var prev = links[index - 1] || links[links.length - 1];
                        prev.focus();
                    } else if (e.key === 'Escape') {
                        closeMenu();
                        toggle.focus();
                    } else if (e.key === 'Tab' && !e.shiftKey && index === links.length - 1) {
                        closeMenu();
                    } else if (e.key === 'Tab' && e.shiftKey && index === 0) {
                        closeMenu();
                    }
                });
            });

            // Close on click outside
            document.addEventListener('click', function(e) {
                if (!dropdown.contains(e.target) && isOpen) {
                    closeMenu();
                }
            });
        });
    }

    // Expose globally for dynamic content
    window.initDropdowns = initDropdowns;

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initDropdowns);
    } else {
        initDropdowns();
    }
})();
