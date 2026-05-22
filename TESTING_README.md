# Game Testing - Start Here

## 🎮 Quick Start (One Command)

```bash
./run_all_tests.sh && ./start-dev.sh
```

Then visit: **http://localhost:8000/users/login/**

**Login:**
- Email: `test@elifwol.com`
- Password: `testpass123`

Go to: **http://localhost:8000/game/**

---

## 📋 What Was Fixed

The game had an **Alpine.js initialization race condition** where the game controller tried to start before script card components finished initializing.

**Result:** Game showed "game state not ready" repeatedly or all characters were dead immediately.

**Fix:** Improved initialization timing with retry logic and better error handling.

---

## 🛠️ Available Scripts

### Complete Setup (Recommended)
```bash
./run_all_tests.sh
```
Does everything: migrations, data population, test user creation, verification.

### Individual Scripts
```bash
./setup_game_data.sh          # Just populate database
python create_test_user.py    # Just create test user
python debug_game.py          # Check database status
```

### Test Alpine.js
Open `test_alpine.html` in your browser to test Alpine.js initialization separately.

---

## 📚 Documentation

| File | Purpose |
|------|---------|
| **QUICK_TEST_GUIDE.md** | Quick reference - start here |
| **GAME_TESTING_GUIDE.md** | Comprehensive testing guide |
| **ALPINE_FIX_SUMMARY.md** | Technical details of the fix |
| **TESTING_README.md** | This file - overview |

---

## ✅ What to Expect

### In Browser Console (F12)

**Success:**
```
Game controller initializing...
Found 3 enemy elements
Found 4 party elements
✅ All components ready, starting battle!
```

**Retrying (normal):**
```
⏳ 2 components not ready, retrying in 500ms...
```

**Failure:**
```
❌ Failed to initialize after 10 retries
```

### In the Game

**Working:**
- 3 enemies with health bars
- 4 party members with health bars
- Battle log shows "Battle started!"
- Characters attack automatically
- Health bars decrease
- You can cast heals

**Not Working:**
- All characters dead immediately
- "Game state not ready" keeps appearing
- Nothing happens

---

## 🔧 Troubleshooting

### No enemies in database
```bash
python manage.py populate_game_data
```

### User has no party
```bash
python create_test_user.py
```

### Components never ready
1. Check browser console for errors
2. Open `test_alpine.html` to test Alpine.js
3. Try a different browser
4. Read `GAME_TESTING_GUIDE.md`

---

## 📁 Files Created

### Scripts
- `run_all_tests.sh` - Complete setup
- `setup_game_data.sh` - Database setup
- `create_test_user.py` - Test user creator
- `debug_game.py` - Database checker
- `check_db.py` - Simple DB check
- `test_game.py` - Game tests

### Test Pages
- `test_alpine.html` - Alpine.js test

### Documentation
- `QUICK_TEST_GUIDE.md` - Quick reference
- `GAME_TESTING_GUIDE.md` - Full guide
- `ALPINE_FIX_SUMMARY.md` - Technical details
- `TESTING_README.md` - This file

### Modified
- `game/static/js/game_controller.js` - Fixed initialization

---

## 🎯 Success Checklist

- [ ] Run `./run_all_tests.sh` successfully
- [ ] Start server with `./start-dev.sh`
- [ ] Login at http://localhost:8000/users/login/
- [ ] Visit http://localhost:8000/game/
- [ ] See 3 enemies and 4 party members
- [ ] Battle starts automatically
- [ ] Characters attack each other
- [ ] Health bars update
- [ ] Battle log shows actions
- [ ] Can cast heals
- [ ] Game ends with victory or defeat

---

## 🆘 Still Having Issues?

1. **Read:** `GAME_TESTING_GUIDE.md` for detailed troubleshooting
2. **Check:** Browser console for specific errors
3. **Test:** Open `test_alpine.html` to verify Alpine.js
4. **Verify:** Run `python debug_game.py` to check database
5. **Share:** Console logs for further help

---

## 📝 Summary

| What | How |
|------|-----|
| **Setup** | `./run_all_tests.sh` |
| **Start** | `./start-dev.sh` |
| **Login** | test@elifwol.com / testpass123 |
| **Play** | http://localhost:8000/game/ |
| **Debug** | Browser console (F12) |
| **Help** | GAME_TESTING_GUIDE.md |

---

**Ready to play? Run:**
```bash
./run_all_tests.sh && ./start-dev.sh
```
