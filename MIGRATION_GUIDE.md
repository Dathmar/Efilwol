# Migration Guide: Bootstrap to Tailwind + Alpine.js

## What Changed?

### Removed
- ❌ Bootstrap CSS and JavaScript
- ❌ jQuery dependencies
- ❌ Manual DOM manipulation with vanilla JS
- ❌ `scripts.js` fade-in functionality (can be re-added if needed)
- ❌ `transition.min.js` library

### Added
- ✅ Tailwind CSS (utility-first CSS framework)
- ✅ DaisyUI (component library)
- ✅ Alpine.js (reactive JavaScript framework)
- ✅ HTMX (ready for server-side interactions)
- ✅ Modern component architecture

## File Changes

### Modified Files

1. **`base/templates/base/base.html`**
   - Replaced Bootstrap with Tailwind CSS + DaisyUI (CDN)
   - Added Alpine.js and HTMX
   - Updated theme to dark mode
   - Removed old script references

2. **`base/templates/base/navbar.html`**
   - Converted from Bootstrap navbar to DaisyUI navbar
   - Added Alpine.js for mobile menu toggle
   - Added user avatar dropdown
   - Improved responsive design

3. **`game/templates/game/game.html`**
   - Complete redesign with Tailwind utilities
   - Added Alpine.js game controller
   - Improved layout (2-column grid)
   - Added real-time battle log
   - Added game status indicators

4. **`game/templates/game/script-card.html`**
   - Converted to Alpine.js component
   - Added reactive health bars
   - Added attack animations
   - Improved visual feedback

5. **`game/templates/game/heal-card.html`**
   - Converted to Alpine.js component
   - Added casting states
   - Added loading indicators

6. **`game/templates/game/index.html`**
   - Complete redesign as hero section
   - Added stats cards
   - Added feature highlights
   - Improved call-to-action

### New Files

1. **`game/static/js/game_controller.js`**
   - Alpine.js-based game controller
   - Replaces `game_loop.js`
   - Cleaner, more maintainable code
   - Better state management

2. **`package.json`**
   - Node.js dependencies
   - Build scripts for Tailwind

3. **`tailwind.config.js`**
   - Tailwind configuration
   - Custom theme colors
   - DaisyUI settings

4. **`base/static/css/input.css`**
   - Tailwind source file
   - Custom component styles
   - Game-specific animations

5. **`.gitignore`**
   - Ignores node_modules
   - Ignores generated CSS

6. **`FRONTEND_SETUP.md`**
   - Complete documentation
   - Development workflow
   - Customization guide

## CSS Class Mapping

### Layout
| Bootstrap | Tailwind |
|-----------|----------|
| `container` | `container mx-auto px-4` |
| `row` | `grid grid-cols-X` or `flex` |
| `col-*` | `col-span-*` |
| `d-flex` | `flex` |
| `justify-content-center` | `justify-center` |
| `align-items-center` | `items-center` |

### Components
| Bootstrap | DaisyUI |
|-----------|---------|
| `btn btn-primary` | `btn btn-primary` |
| `card` | `card` |
| `badge` | `badge` |
| `alert` | `alert` |
| `navbar` | `navbar` |
| `progress` | `progress` |

### Utilities
| Bootstrap | Tailwind |
|-----------|----------|
| `mt-3` | `mt-3` (same!) |
| `p-4` | `p-4` (same!) |
| `text-center` | `text-center` (same!) |
| `bg-dark` | `bg-base-300` |
| `text-white` | `text-base-content` |
| `rounded` | `rounded-lg` |

## JavaScript Migration

### Old Approach (Vanilla JS)
```javascript
const element = document.querySelector('#my-element');
element.addEventListener('click', () => {
  element.classList.add('active');
});
```

### New Approach (Alpine.js)
```html
<div x-data="{ active: false }">
  <button @click="active = !active" 
          :class="{ 'active': active }">
    Click me
  </button>
</div>
```

## Game Logic Changes

### Old: `game_loop.js`
- Manual DOM queries
- Direct element manipulation
- Callback-based async
- Hard to maintain state

### New: `game_controller.js`
- Alpine.js reactive data
- Component-based architecture
- Promise-based async
- Centralized state management

## Breaking Changes

### 1. Custom Bootstrap Classes
If you had custom Bootstrap overrides in `styles_v1.0.0.1.css`, you'll need to:
- Convert them to Tailwind utilities
- Add them to `input.css` using `@layer components`

### 2. JavaScript Event Listeners
Old event listeners on Bootstrap components won't work. Replace with:
- Alpine.js directives (`@click`, `x-show`, etc.)
- HTMX attributes (`hx-get`, `hx-post`, etc.)

### 3. jQuery Dependencies
If any code used jQuery:
- Rewrite with vanilla JS or Alpine.js
- Most jQuery can be replaced with Alpine.js

## Testing Checklist

After migration, test:

- [ ] Homepage loads correctly
- [ ] Navbar works (mobile menu, dropdowns)
- [ ] Login/Signup pages work
- [ ] Game page loads
- [ ] Character cards display correctly
- [ ] Health bars animate
- [ ] Attack animations work
- [ ] Heal buttons function
- [ ] Battle log updates
- [ ] Win/lose detection works
- [ ] Responsive design (mobile, tablet, desktop)

## Rollback Plan

If you need to rollback:

1. **Restore old templates:**
   ```bash
   git checkout HEAD~1 -- base/templates/
   git checkout HEAD~1 -- game/templates/
   ```

2. **Remove new files:**
   ```bash
   rm package.json tailwind.config.js
   rm -rf node_modules/
   ```

3. **Restore old JavaScript:**
   ```bash
   git checkout HEAD~1 -- game/static/js/game_loop.js
   ```

## Next Steps

1. **Test thoroughly** - Play through the game
2. **Customize theme** - Edit `tailwind.config.js`
3. **Add HTMX** - Move game state to server
4. **Optimize** - Build production CSS
5. **Deploy** - Follow deployment guide

## Common Issues

### Issue: Styles not applying
**Solution:** Check if Tailwind CDN is loading, or run `npm run build`

### Issue: Alpine.js not working
**Solution:** Check browser console, ensure Alpine.js CDN is loaded

### Issue: Game loop not starting
**Solution:** Check `game_controller.js` is loaded, verify API endpoints

### Issue: Mobile menu not working
**Solution:** Ensure Alpine.js is initialized, check `x-data` on navbar

## Support

If you encounter issues:
1. Check browser console for errors
2. Review `FRONTEND_SETUP.md`
3. Check Django server logs
4. Verify all CDN links are loading

## Resources

- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [DaisyUI Components](https://daisyui.com/components/)
- [Alpine.js Documentation](https://alpinejs.dev/)
- [HTMX Documentation](https://htmx.org/)
