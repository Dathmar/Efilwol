# Quick Test Guide

## TL;DR - Run This One Command

```bash
./run_all_tests.sh
```

This will:
1. Run migrations
2. Populate game data (NPCs, Scripts, Actions)
3. Create test user with party members
4. Verify everything is set up correctly

## Then Start the Game

```bash
./start-dev.sh
```

Visit: http://localhost:8000/users/login/

**Login:**
- Email: `test@elifwol.com`
- Password: `testpass123`

Then go to: http://localhost:8000/game/

## What to Look For

### In Browser Console (F12)

**Good (working):**
```
Game controller initializing...
Found 3 enemy elements
Found 4 party elements
✅ All components ready, starting battle!
```

**Bad (not working):**
```
⏳ 2 components not ready, retrying in 500ms...
Enemy 0 (Goblin Warrior) not ready
```

If you see retries, wait a few seconds. If it retries more than 10 times, there's a problem.

### In the Game UI

**Good:**
- You see 3 enemies with health bars
- You see 4 party members with health bars
- Battle log shows "Battle started!"
- Characters start attacking each other

**Bad:**
- All enemies are dead immediately
- All party members are dead immediately
- "Game state not ready" messages keep appearing
- Nothing happens

## Troubleshooting

### Problem: "No enemies found in database"

```bash
python manage.py populate_game_data
```

### Problem: "User has no party members"

```bash
python create_test_user.py
```

### Problem: Components never become ready

1. Check browser console for JavaScript errors
2. Open `test_alpine.html` in browser to test Alpine.js
3. Make sure you're using a modern browser (Chrome, Firefox, Edge)

### Problem: Still not working

Read the full guide: `GAME_TESTING_GUIDE.md`

## What Was Fixed

The game had an Alpine.js initialization race condition. The game controller was trying to count alive enemies/party before the script card components finished initializing.

**The fix:**
- Wait 1000ms for Alpine.js to initialize
- Check if all components are ready
- Retry up to 10 times if not ready
- Show clear error messages

## Files You Can Run

- `./run_all_tests.sh` - Complete setup (recommended)
- `./setup_game_data.sh` - Just populate database
- `python create_test_user.py` - Just create test user
- `python debug_game.py` - Check database status
- `test_alpine.html` - Test Alpine.js initialization

## Next Steps

If everything works:
- The game should start automatically
- Characters should attack each other
- You can cast heals by clicking a party member then clicking a heal button
- Battle log shows all actions

If it doesn't work:
- Share the browser console logs
- Check `GAME_TESTING_GUIDE.md` for detailed troubleshooting
