def build_plausible_script_url(options):
    '''Build Plausible script URL with optional extensions'''
    if not options:
        return 'https://plausible.io/js/script.js'
    
    # Valid Plausible extensions
    valid_options = {
        'hash', 'outbound-links', 'file-downloads', '404', 
        'custom-events', 'local', 'manual', 'compat'
    }
    
    # Filter to only valid options and sort for consistency
    clean_options = sorted([opt for opt in options if opt in valid_options])
    
    if not clean_options:
        return 'https://plausible.io/js/script.js'
    
    options_string = '.'.join(clean_options)
    return f'https://plausible.io/js/script.{options_string}.js'