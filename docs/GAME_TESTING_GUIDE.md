# Game Testing Guide

## Current Issue

The game is experiencing an Alpine.js initialization race condition where the game controller tries to start before all script card components are fully initialized, resulting in repeated "game state not ready" messages.

## What Was Fixed

### 1. Improved Game Controller Initialization (`game/static/js/game_controller.js`)

**Changes:**
- Added retry limit (10 attempts) to prevent infinite loops
- Added better logging to show which components are not ready
- Increased initial delay from 500ms to 1000ms
- Added `initRetries` counter to track initialization attempts
- Added error messages when no enemies or party members are found

**Key improvements:**
```javascript
// Now shows detailed info about what's not ready
console.warn(`Enemy ${i} (${el.getAttribute('script_name')}) not ready`);

// Limits retries to prevent infinite loop
if (this.initRetries > 10) {
    console.error('❌ Failed to initialize after 10 retries');
    this.addLog('ERROR: Game failed to initialize. Please refresh the page.', GAME_CONFIG.icons.tomb);
    return;
}
```

## Testing Steps

### Step 1: Setup Game Data

Run the setup script to ensure database has all required data:

```bash
./setup_game_data.sh
```

This will:
1. Run migrations
2. Populate NPCs, Scripts, and Actions
3. Show database status

### Step 2: Create a User (if needed)

```bash
python manage.py createsuperuser
```

Enter an email and password when prompted.

### Step 3: Add Scripts to User Party

You need to manually add scripts to your user's party. You can do this via Django admin:

1. Start the server: `./start-dev.sh`
2. Visit: http://localhost:8000/admin/
3. Login with your superuser credentials
4. Go to "User scripts"
5. Add 3-4 scripts to your user and mark them as "in_party"

### Step 4: Test Alpine.js Initialization

Before testing the actual game, you can test Alpine.js initialization with the test page:

```bash
# Open test_alpine.html in your browser
# This will show you how Alpine.js initializes components
```

The test page will show:
- When Alpine.js loads
- When each component initializes
- Whether components are ready
- How many retries are needed

### Step 5: Test the Game

1. Start the server: `./start-dev.sh`
2. Visit: http://localhost:8000/game/
3. Open browser console (F12)
4. Look for these log messages:

**Expected logs (success):**
```
Game controller initializing...
Found 3 enemy elements
Found 4 party elements
✅ All components ready, starting battle!
Battle started! Choose your targets wisely.
```

**If you see retry messages:**
```
⏳ 2 components not ready, retrying in 500ms...
Enemy 0 (Goblin Warrior) not ready
Party 1 (Knight) not ready
```

This means Alpine.js is still initializing. The game will retry up to 10 times.

**If initialization fails:**
```
❌ Failed to initialize after 10 retries
ERROR: Game failed to initialize. Please refresh the page.
```

## Common Issues and Solutions

### Issue 1: "No enemies found in the database"

**Solution:** Run `./setup_game_data.sh` to populate the database.

### Issue 2: "User has no party members"

**Solution:** Add scripts to your user via Django admin (see Step 3 above).

### Issue 3: Components never become ready

**Possible causes:**
1. Alpine.js CDN not loading (check network tab)
2. JavaScript errors preventing initialization (check console)
3. Template syntax errors in script-card.html

**Debug steps:**
1. Check browser console for errors
2. Open test_alpine.html to verify Alpine.js works
3. Check that script-card.html has proper Alpine.js syntax

### Issue 4: Battle starts but all characters are dead

**Cause:** This was the original issue - the game was checking for alive characters before they were initialized, so it counted 0 alive enemies and 0 alive party members.

**Solution:** The new initialization logic waits for all components to be ready before starting the game loop.

## Understanding the Fix

### The Problem

Alpine.js components initialize asynchronously. The game controller was trying to:
1. Count alive enemies/party members
2. Start the game loop

...before the script card components had finished initializing their `isDead` state.

### The Solution

The new code:
1. Waits 1000ms after controller init
2. Checks if all components have `__x.$data` (Alpine's internal state)
3. Retries every 500ms if not ready
4. Gives up after 10 retries with clear error message
5. Only starts game loop when ALL components are ready

### Why This Works

Alpine.js attaches its reactive state to DOM elements via the `__x` property. By checking for `el.__x.$data`, we can verify that Alpine has:
1. Found the element
2. Initialized the component
3. Set up reactive state

Only then is it safe to start the game loop.

## Next Steps

If the game still doesn't work after these fixes:

1. **Check the logs:** Look at browser console for specific error messages
2. **Test Alpine.js:** Open test_alpine.html to verify Alpine.js works
3. **Verify data:** Run `./setup_game_data.sh` to check database
4. **Check network:** Make sure Alpine.js CDN loads (Network tab in DevTools)
5. **Report back:** Share the console logs so we can diagnose further

## Files Modified

- `game/static/js/game_controller.js` - Improved initialization logic
- `setup_game_data.sh` - New setup script
- `test_alpine.html` - Alpine.js test page
- `GAME_TESTING_GUIDE.md` - This file

## Additional Test Scripts

- `debug_game.py` - Check database status
- `test_game.py` - Comprehensive game tests
- `check_db.py` - Simple database check
