// Client-side search functionality
(function() {
    let searchIndex = [];
    let searchLoaded = false;
    
    // Load search index
    function loadSearchIndex() {
        if (searchLoaded) return Promise.resolve();
        
        return fetch('/search-index.json')
            .then(response => response.json())
            .then(data => {
                searchIndex = data;
                searchLoaded = true;
            })
            .catch(error => {
                console.error('Failed to load search index:', error);
            });
    }
    
    // Perform search
    function performSearch(query) {
        if (!query || query.length < 2) return [];
        
        const searchTerms = query.toLowerCase().split(' ').filter(term => term.length > 1);
        if (searchTerms.length === 0) return [];
        
        const results = searchIndex.map(post => {
            let score = 0;
            const titleLower = post.title.toLowerCase();
            const descLower = post.description.toLowerCase();
            const contentLower = post.content.toLowerCase();
            const categoriesLower = post.categories.map(cat => cat.toLowerCase()).join(' ');
            
            searchTerms.forEach(term => {
                // Title matches (highest weight)
                if (titleLower.includes(term)) {
                    score += 10;
                    if (titleLower.startsWith(term)) score += 5;
                }
                
                // Description matches (medium weight)
                if (descLower.includes(term)) {
                    score += 5;
                }
                
                // Category matches (medium weight)
                if (categoriesLower.includes(term)) {
                    score += 5;
                }
                
                // Content matches (lowest weight)
                if (contentLower.includes(term)) {
                    score += 1;
                }
            });
            
            return { post, score };
        })
        .filter(result => result.score > 0)
        .sort((a, b) => b.score - a.score)
        .map(result => result.post);
        
        return results.slice(0, 10); // Return top 10 results
    }
    
    // Highlight search terms in text
    function highlightTerms(text, terms) {
        let highlighted = text;
        terms.forEach(term => {
            const regex = new RegExp(`(${term})`, 'gi');
            highlighted = highlighted.replace(regex, '<mark>$1</mark>');
        });
        return highlighted;
    }
    
    // Format search result
    function formatResult(post, searchTerms) {
        const categoryLinks = post.categories.map(cat => 
            `<a href="/categories/${cat.toLowerCase().replace(' ', '-')}.html">${cat}</a>`
        ).join(', ');
        
        const highlightedTitle = highlightTerms(post.title, searchTerms);
        const highlightedDesc = highlightTerms(post.description || '', searchTerms);
        
        return `
            <article class="search-result post-preview">
                <h3><a href="/${post.url}">${highlightedTitle}</a></h3>
                <div class="post-meta">
                    <time datetime="${post.date}">${post.date}</time>
                    ${post.reading_time ? ` • <span class="reading-time">${post.reading_time} min read</span>` : ''}
                    ${categoryLinks ? ` • <span class="categories">${categoryLinks}</span>` : ''}
                </div>
                ${highlightedDesc ? `<p>${highlightedDesc}</p>` : ''}
            </article>
        `;
    }
    
    // Initialize search
    function initSearch() {
        const searchToggle = document.getElementById('search-toggle');
        const searchOverlay = document.getElementById('search-overlay');
        const searchInput = document.getElementById('search-input');
        const searchResults = document.getElementById('search-results');
        const searchClose = document.getElementById('search-close');
        
        if (!searchToggle || !searchOverlay) return;
        
        // Toggle search overlay
        searchToggle.addEventListener('click', async (e) => {
            e.preventDefault();
            await loadSearchIndex();
            searchOverlay.classList.add('active');
            searchInput.focus();
        });
        
        // Close search overlay
        searchClose.addEventListener('click', () => {
            searchOverlay.classList.remove('active');
            searchInput.value = '';
            searchResults.innerHTML = '';
        });
        
        // Close on ESC key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && searchOverlay.classList.contains('active')) {
                searchOverlay.classList.remove('active');
                searchInput.value = '';
                searchResults.innerHTML = '';
            }
        });
        
        // Close on overlay click
        searchOverlay.addEventListener('click', (e) => {
            if (e.target === searchOverlay) {
                searchOverlay.classList.remove('active');
                searchInput.value = '';
                searchResults.innerHTML = '';
            }
        });
        
        // Handle search input
        let searchTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            const query = e.target.value.trim();
            
            if (query.length < 2) {
                searchResults.innerHTML = '<p class="search-hint">Type at least 2 characters to search...</p>';
                return;
            }
            
            searchTimeout = setTimeout(() => {
                const results = performSearch(query);
                const searchTerms = query.toLowerCase().split(' ').filter(term => term.length > 1);
                
                if (results.length === 0) {
                    searchResults.innerHTML = '<p class="search-no-results">No results found.</p>';
                } else {
                    const resultsHtml = results.map(post => formatResult(post, searchTerms)).join('');
                    searchResults.innerHTML = `
                        <p class="search-count">${results.length} result${results.length !== 1 ? 's' : ''} found</p>
                        ${resultsHtml}
                    `;
                }
            }, 300); // Debounce search
        });
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initSearch);
    } else {
        initSearch();
    }
})();