"""
SKOUT Automated Ice‑Breaker Bot
================================
Author : Derek Chan (Modified for general use)
Purpose: Log in to Skout, iterate through profile cards, send an ice‑breaker
         message to any profile you haven't contacted yet, and remember
         who you've messaged across runs.

Key Features
------------
* Persistent memory of messaged profiles via JSON.
* ActionChains‑powered clicks to avoid hidden‑element issues.
* Auto‑scrolling to surface more profiles.
* Graceful shutdown + logging for post‑mortem analysis.
"""

# ────────────── IMPORTS ──────────────
import os        # For file path handling and checking if files exist
import json      # For saving/loading messaged profile IDs persistently as JSON
import time      # To pause execution for waits/delays
import logging   # To log activity both to console and file with timestamps
import random    # To generate randomized wait times for human-like pacing

# Selenium modules for browser automation:
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains  # For advanced user interactions
from selenium.webdriver.support.ui import WebDriverWait            # Explicit waits until conditions met
from selenium.webdriver.support import expected_conditions as EC   # Common expected conditions
from selenium.common.exceptions import StaleElementReferenceException  # Handle dynamic page elements

# Webdriver manager for automatic ChromeDriver version management
from webdriver_manager.chrome import ChromeDriverManager

# Your canned icebreaker message imported from external file
from message_text import message   

# ────────────── RANDOM WAIT HELPER FUNCTION ──────────────
def random_wait(base_seconds=2, variation=2):
    """
    Pause execution for a random duration to simulate human-like behavior.

    Parameters:
    - base_seconds: minimum time to wait in seconds (float or int).
    - variation: maximum random seconds to add on top of base_seconds.

    Returns:
    - The actual sleep time used (float).

    Why:
    Introducing randomness prevents rigid timing patterns,
    which helps evade bot detection mechanisms.

    NOTE: Optimized for balanced speed - 33% faster, not too aggressive.
    """
    # Reduce wait times by 33% for balanced speed
    wait_time = (base_seconds / 1.5) + random.uniform(0, variation / 1.5)
    time.sleep(wait_time)
    return wait_time

# ────────────── LOGGING SETUP ──────────────
logging.basicConfig(
    filename="skout_bot_log.txt",  # Log file name
    level=logging.INFO,             # Log level (INFO and above)
    format="%(asctime)s - %(message)s",  # Timestamp plus message
)

def log(msg: str) -> None:
    """
    Print message to console AND write it to the log file.
    
    This unified logging simplifies debugging and keeps permanent records.
    """
    print(msg)
    logging.info(msg)

# ────────────── PERSISTENT MEMORY ──────────────
MESSAGED_JSON_PATH = "messaged_profiles.json"

# Load previously messaged profile IDs from disk
if os.path.exists(MESSAGED_JSON_PATH):
    with open(MESSAGED_JSON_PATH, "r") as f:
        messaged_profiles = set(json.load(f))  # Using a set for O(1) membership checks
else:
    messaged_profiles = set()  # Empty set if file missing (first run)

def save_profiles() -> None:
    """
    Save the in-memory set of messaged profiles to a JSON file.
    
    This guarantees that even if the script stops unexpectedly,
    you won't message the same profiles twice on restart.
    """
    with open(MESSAGED_JSON_PATH, "w") as f:
        json.dump(list(messaged_profiles), f)

# ────────────── SELENIUM DRIVER SETUP ──────────────
log("🚀 Setting up Chrome driver...")

options = Options()

# ===== ANTI-DETECTION MEASURES =====
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--start-maximized")

# Optional: Use your Chrome profile to stay logged in
# Uncomment and adjust to your username:
# options.add_argument(r'--user-data-dir=C:\Users\depan\AppData\Local\Google\Chrome\User Data')
# options.add_argument('--profile-directory=Default')
# NOTE: Close ALL Chrome windows before running if using your profile!

# If NOT using your profile, create a local temp profile for this bot
if not any('user-data-dir' in arg for arg in options.arguments):
    user_data_dir = os.path.join(os.getcwd(), "chrome_user_data")
    os.makedirs(user_data_dir, exist_ok=True)
    options.add_argument(f"user-data-dir={user_data_dir}")

# Create WebDriver instance - webdriver-manager will auto-download correct ChromeDriver
print("⏳ Initializing ChromeDriver (cached after first run)...")
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# Remove webdriver property to further hide automation
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

log("✅ Chrome driver initialized successfully!")

# Navigate to Skout homepage
print("🌐 Loading skout.com...")
driver.get("https://skout.com")

# ────────────── LOGIN FLOW ──────────────
try:
    # Wait up to 2 seconds for login button (quick check)
    login_button = WebDriverWait(driver, 2).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="menu-login-navigation"]/li/a'))
    )
    login_button.click()
    log("🔐 Clicked the login button.")
except Exception:
    # Login button not found: assume already logged in
    log("⚠️  Already logged in.")

# Wait until page fully loads (quick check - 2 seconds max)
print("⏳ Waiting for page load...")
WebDriverWait(driver, 2).until(
    lambda d: d.execute_script("return document.readyState") == "complete"
)
log("✅ Page loaded!")

# Countdown to start
for i in range(3, 0, -1):
    print(f"🤖 Starting bot in {i}...")
    time.sleep(1)

print("🚀 BOT ACTIVE - Beginning profile messaging!")
log("🤖 Bot started - messaging profiles")

# CRITICAL: Trigger page rendering by simulating scroll/zoom (fixes lazy loading)
print("🔄 Activating page elements...")
driver.execute_script("""
    // Scroll down and back up to trigger lazy loading
    window.scrollBy(0, 500);
    setTimeout(() => window.scrollBy(0, -500), 100);

    // Zoom in and out to wake up page (simulates mouse wheel)
    document.body.style.zoom = "110%";
    setTimeout(() => { document.body.style.zoom = "100%"; }, 200);
""")
time.sleep(1)
log("✅ Page elements activated")

# ────────────── ASCII ART HEADER ──────────────
ascii_art = r"""

███████╗██╗  ██╗ ██████╗ ██╗   ██╗████████╗    ██████╗ ███████╗ █████╗ ██╗     ███████╗██████╗ 
██╔════╝██║ ██╔╝██╔═══██╗██║   ██║╚══██╔══╝    ██╔══██╗██╔════╝██╔══██╗██║     ██╔════╝██╔══██╗
███████╗█████╔╝ ██║   ██║██║   ██║   ██║       ██║  ██║█████╗  ███████║██║     █████╗  ██████╔╝
╚════██║██╔═██╗ ██║   ██║██║   ██║   ██║       ██║  ██║██╔══╝  ██╔══██║██║     ██╔══╝  ██╔══██╗
███████║██║  ██╗╚██████╔╝╚██████╔╝   ██║       ██████╔╝███████╗██║  ██║███████╗███████╗██║  ██║
╚══════╝╚═╝  ╚═╝ ╚═════╝  ╚═════╝    ╚═╝       ╚═════╝ ╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝

"""
print(ascii_art)

# ────────────── SCROLL UTILITY ──────────────
def scroll_to_bottom() -> None:
    """
    Scroll to the bottom of the page to trigger lazy-loading
    of more profile cards on the page.

    Also attempts to click "Show more" button if it appears,
    which is critical for loading additional profiles beyond
    the initial set.

    Followed by a random wait to simulate reading/thinking time.
    Optimized for speed - reduced wait times.
    """
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    random_wait(1, 1)  # Wait 0.5-1.5 seconds (halved from 2-5)

    # Try to click "Show more" button if it appears (with retry logic for stale elements)
    for attempt in range(3):
        try:
            show_more_button = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable((By.XPATH, '//button[normalize-space(text())="Show more"]'))
            )
            # Scroll button into view
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", show_more_button)
            time.sleep(0.5)
            show_more_button.click()
            log("🔽 Clicked 'Show more' button - loading additional profiles!")
            time.sleep(1)
            break
        except StaleElementReferenceException:
            log(f"♻️ Retrying 'Show more' due to stale reference... ({attempt+1}/3)")
            time.sleep(0.5)
        except Exception:
            # "Show more" button not found - no more profiles to load
            break

# ────────────── PROFILE POPUP CLOSE ──────────────
def close_profile_popup() -> None:
    """
    Attempt to close the profile modal popup (the icebreaker dialog)
    with a two-step approach:
    
    1. Wait for the modal's animation to finish (either open or close).
    2. Click the close ('×') button if it exists and is clickable.
    
    Includes error handling and a random pause after closing.
    """
    try:
        # Brief pause for animations (optimized for speed)
        time.sleep(0.2)

        # Try multiple selectors for the close button
        close_selectors = [
            'button[aria-label="Close"]',
            'button[type="button"][aria-label="Close"]',
            'button.rounded-wds-button-corner-radius[aria-label="Close"]'
        ]

        for selector in close_selectors:
            try:
                close_button = WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )

                # Use ActionChains for more reliable clicking
                ActionChains(driver).move_to_element(close_button).click().perform()
                log("✅ Closed profile popup.")
                time.sleep(0.3)  # Quick pause after close
                return  # Success - exit function

            except Exception:
                continue  # Try next selector

        # If all selectors failed, try JavaScript click as last resort
        try:
            driver.execute_script("""
                const closeBtn = document.querySelector('button[aria-label="Close"]');
                if (closeBtn) closeBtn.click();
            """)
            log("✅ Closed profile popup (via JavaScript).")
        except Exception:
            log("⚠️  Could not find close button.")

    except Exception as e:
        log(f"⚠️  Error closing popup: {e}")

    time.sleep(0.5)  # Brief wait before next action

# ────────────── MAIN MESSAGE SENDING LOOP ──────────────
def send_message_to_profiles() -> None:
    """
    Main infinite loop that:
    - Fetches visible profile buttons on the page.
    - Randomizes the order to avoid pattern detection.
    - Iterates each profile:
      * Skips if no label or already messaged (persistent memory).
      * Opens profile modal via ActionChains click.
      * Checks if already messaged via chat badge.
      * Clicks icebreaker icon.
      * Types and sends canned icebreaker message.
      * Saves messaged profile to persistent memory.
      * Closes modal.
    - Scrolls down to load more profiles and repeats.
    
    Uses randomized waits throughout for natural timing.
    """
    wait = WebDriverWait(driver, 3)  # Explicit wait helper (optimized)
    no_new_profiles_count = 0  # Track consecutive loops with no new profiles

    while True:
        # Check if we've reached the end of all profiles
        try:
            end_message = driver.find_element(By.XPATH, '//p[contains(text(), "We have already shown you everyone.")]')
            if end_message.is_displayed():
                log("🎉 SUCCESS! All profiles have been shown. Campaign complete!")
                break
        except Exception:
            pass  # Message not found, continue processing

        # Grab all profile buttons visible on the page (DOM can change dynamically)
        profile_buttons = driver.find_elements(
            By.CSS_SELECTOR, "li.profile-card-element button.outline-hidden"
        )

        # If no profiles found, trigger loading with scroll
        if not profile_buttons:
            print("⚠️  No profiles visible, triggering page refresh...")
            driver.execute_script("window.scrollBy(0, 300);")
            time.sleep(1)
            driver.execute_script("window.scrollBy(0, -300);")
            time.sleep(1)
            no_new_profiles_count += 1
            # If no profiles found after 5 attempts, likely reached the end
            if no_new_profiles_count >= 5:
                log("🛑 No new profiles found after multiple scrolls. Campaign complete!")
                break
            continue

        no_new_profiles_count = 0  # Reset counter when profiles are found

        print(f"📋 Found {len(profile_buttons)} profiles on page")
        log(f"Found {len(profile_buttons)} visible profiles")

        # Shuffle list for randomized processing order every loop
        random.shuffle(profile_buttons)

        for i in range(len(profile_buttons)):
            try:
                # Refresh element reference since DOM updates cause stale elements
                profile_buttons = driver.find_elements(
                    By.CSS_SELECTOR, "li.profile-card-element button.outline-hidden"
                )
                button = profile_buttons[i]

                profile_label = button.get_attribute("aria-label")

                # Skip if no label or already messaged
                if not profile_label or profile_label in messaged_profiles:
                    continue

                # Mark as messaged immediately to avoid double-processing
                messaged_profiles.add(profile_label)

                # Open the profile modal using ActionChains for reliable click
                ActionChains(driver).move_to_element(button).click().perform()

                # CRITICAL: Wait for profile elements to fully load
                print(f"⏳ Waiting for profile '{profile_label}' to load...")
                try:
                    # Wait for either the icebreaker icon OR chat badge to appear (ensures profile is loaded)
                    WebDriverWait(driver, 5).until(
                        lambda d: d.find_elements(By.CSS_SELECTOR, 'span[data-testid="social-icebreaker-filled"]') or
                                  d.find_elements(By.CSS_SELECTOR, 'span[data-testid="chat-status-requested"]')
                    )
                    log(f"✅ Profile '{profile_label}' loaded - all elements visible")
                except Exception as e:
                    log(f"⚠️  Profile elements didn't load in time for '{profile_label}': {e}")
                    close_profile_popup()
                    continue

                # Check if chat already exists (skip if so)
                try:
                    driver.find_element(
                        By.CSS_SELECTOR, 'span[data-testid="chat-status-requested"]'
                    )
                    log(f"Skipping '{profile_label}' – already messaged.")
                    close_profile_popup()
                    continue
                except Exception:
                    # No chat badge found; proceed to send message
                    pass

                try:
                    # Wait for icebreaker icon to be clickable
                    print(f"📬 Looking for message icon...")
                    icebreaker_icon = wait.until(
                        EC.element_to_be_clickable(
                            (By.CSS_SELECTOR, 'span[data-testid="social-icebreaker-filled"]')
                        )
                    )
                    log(f"✅ Message icon found, clicking...")
                    icebreaker_icon.click()
                    random_wait(0.5, 0.5)  # Let message textarea render

                    # Locate message textarea & type message
                    message_box = wait.until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, 'textarea[name="message"]')
                        )
                    )
                    log(f"💬 Sending message to '{profile_label}'")

                    # CRITICAL: Click to focus textbox first (activates send button)
                    ActionChains(driver).move_to_element(message_box).click().perform()
                    random_wait(0.1, 0.2)  # Brief pause after focus

                    # Send single character to trigger button activation
                    message_box.send_keys("H")
                    random_wait(0.1, 0.2)

                    # Now inject full message via JavaScript
                    driver.execute_script("""
                        arguments[0].value = arguments[1];
                        arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                        arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                        arguments[0].focus();
                    """, message_box, message)
                    random_wait(0.2, 0.3)  # Brief pause after typing

                    # Click the send button
                    send_button = wait.until(
                        EC.element_to_be_clickable(
                            (By.CSS_SELECTOR, 'button[type="submit"] span[data-testid="send"]')
                        )
                    )
                    send_button.click()
                    log(f"📨 Message sent to '{profile_label}'")
                    random_wait(0.3, 0.5)  # Quick wait after sending (optimized)

                except Exception as e:
                    log(f"⚠️  Could not send message to '{profile_label}': {e}")

                # Save updated messaged profiles memory to disk
                save_profiles()
                # Close the profile popup to proceed
                close_profile_popup()

            # Handle dynamic page changes gracefully by retrying
            except StaleElementReferenceException:
                log("♻️  Stale element — retrying.")
                continue
            # Log and continue on any other unexpected exception
            except Exception as e:
                log(f"⚠️  Couldn't interact with profile '{profile_label}': {e}")
                close_profile_popup()

        # Scroll down to load more profiles and simulate reading time
        scroll_to_bottom()

# ────────────── SCRIPT ENTRY POINT ──────────────
try:
    send_message_to_profiles()

except KeyboardInterrupt:
    log("🛑 Script stopped manually by user.")

except Exception as e:
    log(f"💥 Fatal error: {e}")

finally:
    # On exit, save state and cleanly close Chrome driver
    try:
        save_profiles()
        driver.quit()
        log("✅ Chrome closed and profiles saved.")
    except Exception as e:
        log(f"⚠️  Shutdown error: {e}")
