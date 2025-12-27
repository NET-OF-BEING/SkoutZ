# SkoutZ - Marketing Automation Pro

**Professional SKOUT marketing automation with modern GUI**

## 🚀 Features

- **Dual Mode Operation** - Browse Profiles AND Match Game automation
- **Modern Tabbed Interface** - Easy switching between modes
- **Browse Profiles Mode**:
  - Smart "Show more" button detection for maximum reach
  - Persistent memory - never message the same person twice
  - Auto-save - profiles saved automatically
- **Match Game Mode** 🎮:
  - Automated messaging in Match Game
  - Continuous message loop
  - Fast-paced interaction
- **Customizable Messages** - Enter any message you want to send
- **Adjustable Speed Control** - Fine-tune automation speed (1-10, default: 7)
- **Real-time Activity Log** - Watch the bot work with live status updates
- **Anti-Detection** - Advanced techniques to avoid bot detection
- **SKOUT.com Branding** - Professional color palette throughout

## 📦 Installation

### Quick Start

```bash
cd /home/panda/Documents/PythonScripts/SKOUT
./launch_skoutz.sh
```

The launcher will automatically:
- Create virtual environment if needed
- Install all dependencies
- Launch the GUI

## 🎮 Usage

### GUI Mode (Recommended)

1. **Launch the application:**
   ```bash
   ./launch_skoutz.sh
   ```

2. **Choose your mode:**
   - **Browse Profiles** tab - Traditional profile-by-profile messaging
   - **Match Game** tab 🎮 - Rapid-fire Match Game automation

3. **Browse Profiles Mode:**
   - Enter your message in the text box
   - Adjust speed slider (1=slowest, 10=fastest, default=7)
   - Click **START** button
   - Bot will iterate through all profiles, clicking "Show more" as needed
   - Watch the live activity log
   - Click **STOP** to pause anytime

4. **Match Game Mode:** 🎮
   - Enter your message in the text box
   - Adjust speed slider for faster/slower messaging
   - Click **START** button
   - Bot will navigate to Match Game and continuously:
     - Click the message button
     - Type your message
     - Click send
     - Repeat
   - Click **STOP** to pause anytime

### Command Line Mode (Advanced)

For automation scripts or headless servers:

```bash
./venv/bin/python3 SKOUT_MESSAGE_BOT.py
```

Edit `message_text.py` to set your message.

## ⚙️ Configuration

### Speed Settings

- **Speed 1-3:** Slow & cautious (2x slower than default)
- **Speed 4-6:** Moderate pace
- **Speed 7:** Balanced (default) - 33% faster than conservative
- **Speed 8-9:** Fast
- **Speed 10:** Maximum speed (70% faster than default)

Higher speeds = more profiles contacted per hour, but may increase detection risk.

### Message Customization

**GUI:** Simply type your message in the text box

**CLI:** Edit `message_text.py`:
```python
message = "Your custom message here"
```

## 📊 How It Works

1. Opens Chrome with anti-detection measures
2. Navigates to SKOUT.com and handles login
3. Iterates through profile cards
4. For each new profile:
   - Opens profile modal
   - Waits for all elements to load
   - Clicks message icon
   - Types your message
   - Clicks send
   - Closes profile
5. Scrolls and clicks "Show more" to load additional profiles
6. Continues until all profiles contacted
7. Logs everything for review

## 🎨 Color Palette

SkoutZ uses the official SKOUT.com color scheme:

- **Primary Purple:** #8B5CF6
- **Secondary Indigo:** #6366F1
- **Success Green:** #10B981
- **Danger Red:** #EF4444
- **Dark Background:** #1F2937
- **Light Background:** #374151

## 📝 Files

- `skoutz_gui.py` - Main GUI application
- `SKOUT_MESSAGE_BOT.py` - Core bot engine (CLI mode)
- `launch_skoutz.sh` - GUI launcher script
- `run_skout_bot.sh` - CLI launcher script
- `messaged_profiles.json` - Persistent memory of contacted profiles
- `skout_bot_log.txt` - Activity log
- `chrome_user_data/` - Browser profile (keeps you logged in)
- `venv/` - Python virtual environment

## 🛠️ Dependencies

- Python 3.8+
- selenium
- webdriver-manager
- tkinter (included with Python)

## ⚠️ Important Notes

1. **First run:** You'll need to log in to SKOUT manually in the browser window
2. **Session persistence:** The bot remembers your login via Chrome profile
3. **Profile memory:** Contacted profiles are saved to `messaged_profiles.json`
4. **Logs:** All activity logged to `skout_bot_log.txt`
5. **Stopping:** Click STOP button or press Ctrl+C in terminal

## 🔒 Privacy & Safety

- All data stored locally
- No external servers or data sharing
- Session data in `chrome_user_data/` (keep private)
- Logs in `skout_bot_log.txt` (review regularly)

## 📄 License

See LICENSE file for details.

---

**SkoutZ v2.0** - Professional Marketing Automation
*Maximize your reach with dual-mode automation: Browse Profiles + Match Game* 🎮
