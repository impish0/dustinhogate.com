// Code copy functionality for code blocks
document.addEventListener('DOMContentLoaded', function() {
    // Process all code blocks
    document.querySelectorAll('pre').forEach(function(pre) {
        var code = pre.querySelector('code');
        if (!code) return;
        
        var language = '';
        
        // Extract language from class name
        var classes = code.className.split(' ');
        for (var i = 0; i < classes.length; i++) {
            if (classes[i].startsWith('language-')) {
                language = classes[i].replace('language-', '');
                break;
            }
        }
        
        if (language && language !== 'language-') {
            // Create wrapper div
            var wrapper = document.createElement('div');
            wrapper.className = 'code-block-wrapper';
            
            // Create header
            var header = document.createElement('div');
            header.className = 'code-block-header';
            
            var langSpan = document.createElement('span');
            langSpan.className = 'code-language';
            langSpan.textContent = language;
            
            var button = document.createElement('button');
            button.className = 'copy-button';
            button.textContent = '📋';
            button.title = 'Copy code';
            
            header.appendChild(langSpan);
            header.appendChild(button);
            
            // Insert wrapper and move pre into it
            pre.parentNode.insertBefore(wrapper, pre);
            wrapper.appendChild(header);
            wrapper.appendChild(pre);
            
            // Add click handler
            button.addEventListener('click', function() {
                var text = code.textContent || code.innerText;
                navigator.clipboard.writeText(text).then(function() {
                    button.textContent = '✓';
                    setTimeout(function() {
                        button.textContent = '📋';
                    }, 2000);
                });
            });
        } else {
            // No language, add button directly to pre
            var button = document.createElement('button');
            button.className = 'copy-button';
            button.textContent = '📋';
            button.title = 'Copy code';
            
            pre.appendChild(button);
            
            // Add click handler
            button.addEventListener('click', function() {
                var text = code.textContent || code.innerText;
                navigator.clipboard.writeText(text).then(function() {
                    button.textContent = '✓';
                    setTimeout(function() {
                        button.textContent = '📋';
                    }, 2000);
                });
            });
        }
    });
});