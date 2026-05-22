# Efilwol - Modern Frontend Stack

## Stack Overview

This project uses a modern, production-ready frontend stack:

- **Tailwind CSS** - Utility-first CSS framework
- **DaisyUI** - Component library built on Tailwind
- **HTMX** - Modern interactions without heavy JavaScript
- **Alpine.js** - Lightweight reactive framework for UI interactions
- **Django** - Backend framework serving templates and API

## Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Build CSS (Development)

Watch for changes and rebuild automatically:

```bash
npm run dev
```

### 3. Build CSS (Production)

Build minified CSS for production:

```bash
npm run build
```

### 4. Run Django Server

```bash
python manage.py runserver
```

## Project Structure

```
Efilwol/
├── base/
│   ├── static/
│   │   ├── css/
│   │   │   ├── input.css          # Tailwind source file
│   │   │   └── output.css         # Generated CSS (gitignored)
│   │   └── js/
│   └── templates/
│       └── base/
│           ├── base.html           # Base template with CDN links
│           └── navbar.html         # Modern navbar with Alpine.js
├── game/
│   ├── static/
│   │   └── js/
│   │       └── game_controller.js  # Alpine.js game logic
│   └── templates/
│       └── game/
│           ├── game.html           # Main game page
│           ├── script-card.html    # Character card component
│           └── heal-card.html      # Heal button component
├── package.json                    # Node dependencies
├── tailwind.config.js              # Tailwind configuration
└── FRONTEND_SETUP.md              # This file
```

## Key Features

### Tailwind CSS + DaisyUI

- **Utility-first styling** - Build custom designs quickly
- **Pre-built components** - Buttons, cards, badges, etc.
- **Dark theme** - Custom "efilwol" theme with game-friendly colors
- **Responsive** - Mobile-first design

### Alpine.js Components

#### Game Controller (`game_controller.js`)
- Manages game state and battle loop
- Handles attacks, healing, and damage
- Real-time battle log
- Win/lose detection

#### Script Card Component
- Reactive health bars
- Attack animations
- Death states
- Click-to-target functionality

#### Heal Button Component
- Casting states
- Disabled states during cooldown
- Visual feedback

### HTMX Integration

Currently using Alpine.js for game logic. HTMX can be added for:
- Server-side game state management
- Real-time updates via SSE
- Form submissions without page reload

## Customization

### Changing Theme

Edit `tailwind.config.js` to modify the color scheme:

```javascript
daisyui: {
  themes: [
    {
      efilwol: {
        "primary": "#8b5cf6",    // Purple
        "secondary": "#ec4899",   // Pink
        "accent": "#14b8a6",      // Teal
        // ... more colors
      },
    },
  ],
}
```

### Adding Custom Styles

Add custom CSS to `base/static/css/input.css`:

```css
@layer components {
  .my-custom-class {
    @apply bg-primary text-white p-4 rounded-lg;
  }
}
```

Then rebuild with `npm run build`.

## Development Workflow

### For CSS Changes

1. Run `npm run dev` in one terminal
2. Run `python manage.py runserver` in another
3. Edit templates or `input.css`
4. Changes auto-rebuild and refresh

### For JavaScript Changes

1. Edit Alpine.js components in templates or `game_controller.js`
2. Refresh browser to see changes
3. Use browser DevTools for debugging

## Production Deployment

### 1. Build Optimized CSS

```bash
npm run build
```

### 2. Collect Static Files

```bash
python manage.py collectstatic
```

### 3. Set Django Settings

```python
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com']
```

### 4. Use CDN Links (Current Setup)

The base template uses CDN links for:
- Tailwind CSS
- DaisyUI
- HTMX
- Alpine.js

This is production-ready but you can also:
- Self-host these libraries
- Use a build process to bundle everything
- Implement a CDN for your static files

## Browser Support

- Chrome/Edge (latest 2 versions)
- Firefox (latest 2 versions)
- Safari (latest 2 versions)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Performance

- **Tailwind CSS**: ~10KB gzipped (with purge)
- **DaisyUI**: ~15KB gzipped
- **Alpine.js**: ~15KB gzipped
- **HTMX**: ~14KB gzipped

Total: ~54KB of JavaScript/CSS (very lightweight!)

## Troubleshooting

### CSS not updating?

1. Check if `npm run dev` is running
2. Hard refresh browser (Ctrl+Shift+R)
3. Clear browser cache

### Alpine.js not working?

1. Check browser console for errors
2. Ensure `x-data` is on parent element
3. Verify Alpine.js CDN is loading

### Game not starting?

1. Check browser console for errors
2. Verify API endpoints are working
3. Check Django server logs

## Next Steps

### Recommended Improvements

1. **Add HTMX for server communication**
   - Move game state to Django backend
   - Use SSE for real-time updates
   - Reduce client-side complexity

2. **Add WebSockets**
   - Real-time multiplayer
   - Live battle updates
   - Chat system

3. **Optimize Assets**
   - Compress images
   - Use WebP format
   - Implement lazy loading

4. **Add Testing**
   - Jest for JavaScript
   - Playwright for E2E tests
   - Django tests for backend

5. **Add Analytics**
   - Track game sessions
   - Monitor performance
   - User behavior analysis

## Resources

- [Tailwind CSS Docs](https://tailwindcss.com/docs)
- [DaisyUI Components](https://daisyui.com/components/)
- [Alpine.js Guide](https://alpinejs.dev/start-here)
- [HTMX Documentation](https://htmx.org/docs/)
- [Django Documentation](https://docs.djangoproject.com/)

## Support

For issues or questions:
1. Check browser console for errors
2. Review this documentation
3. Check Django logs
4. Open an issue on GitHub
