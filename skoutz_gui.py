#!/usr/bin/env python3
"""
SkoutZ - Professional SKOUT Marketing Automation GUI
====================================================
Author: Derek Chan (Rebranded & Enhanced)
Features:
- Modern GUI with SKOUT.com color palette
- Adjustable speed control (1-10)
- Real-time status updates
- Start/Stop controls
- Live activity log viewer
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue
import os
import json
import time
import logging
import random
from pathlib import Path

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager


class SkoutZBot:
    """Core bot engine - refactored for GUI integration"""

    def __init__(self, message, speed, log_callback):
        self.message = message
        self.speed = speed  # 1-10
        self.log_callback = log_callback
        self.driver = None
        self.running = False
        self.messaged_profiles = set()
        self.messaged_json_path = "messaged_profiles.json"

        # Load previous profiles
        if os.path.exists(self.messaged_json_path):
            with open(self.messaged_json_path, "r") as f:
                self.messaged_profiles = set(json.load(f))

    def log(self, msg):
        """Send log messages to GUI"""
        if self.log_callback:
            self.log_callback(msg)
        logging.info(msg)

    def save_profiles(self):
        """Save messaged profiles to disk"""
        with open(self.messaged_json_path, "w") as f:
            json.dump(list(self.messaged_profiles), f)

    def random_wait(self, base_seconds=2, variation=2):
        """Speed-adjusted random wait"""
        # Speed 10 = fastest (0.3x), Speed 1 = slowest (2x)
        # Speed 7 (default) = 0.67x
        speed_multiplier = 2.0 - (self.speed / 10 * 1.7)

        wait_time = (base_seconds * speed_multiplier) + random.uniform(0, variation * speed_multiplier)
        time.sleep(wait_time)
        return wait_time

    def setup_driver(self):
        """Initialize Chrome driver with anti-detection"""
        self.log("🚀 Setting up Chrome driver...")

        options = Options()
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--start-maximized")

        # Use local Chrome profile
        user_data_dir = os.path.join(os.getcwd(), "chrome_user_data")
        os.makedirs(user_data_dir, exist_ok=True)
        options.add_argument(f"user-data-dir={user_data_dir}")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        self.log("✅ Chrome driver initialized!")

    def navigate_to_skout(self):
        """Navigate to SKOUT and handle login"""
        self.log("🌐 Loading skout.com...")
        self.driver.get("https://skout.com")

        try:
            login_button = WebDriverWait(self.driver, 2).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="menu-login-navigation"]/li/a'))
            )
            login_button.click()
            self.log("🔐 Clicked login button")
        except Exception:
            self.log("⚠️  Already logged in")

        WebDriverWait(self.driver, 2).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        self.log("✅ Page loaded!")

        # Activate page elements
        self.driver.execute_script("""
            window.scrollBy(0, 500);
            setTimeout(() => window.scrollBy(0, -500), 100);
            document.body.style.zoom = "110%";
            setTimeout(() => { document.body.style.zoom = "100%"; }, 200);
        """)
        time.sleep(1)

    def scroll_to_bottom(self):
        """Scroll and click 'Show more' button"""
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        self.random_wait(1, 1)

        # Try to click "Show more"
        for attempt in range(3):
            try:
                show_more = WebDriverWait(self.driver, 2).until(
                    EC.element_to_be_clickable((By.XPATH, '//button[normalize-space(text())="Show more"]'))
                )
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", show_more)
                time.sleep(0.5)
                show_more.click()
                self.log("🔽 Clicked 'Show more' - loading more profiles!")
                time.sleep(1)
                break
            except StaleElementReferenceException:
                self.log(f"♻️  Retrying 'Show more' ({attempt+1}/3)")
                time.sleep(0.5)
            except Exception:
                break

    def close_profile_popup(self):
        """Close profile modal"""
        try:
            time.sleep(0.2)
            close_selectors = [
                'button[aria-label="Close"]',
                'button[type="button"][aria-label="Close"]',
                'button.rounded-wds-button-corner-radius[aria-label="Close"]'
            ]

            for selector in close_selectors:
                try:
                    close_button = WebDriverWait(self.driver, 2).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    ActionChains(self.driver).move_to_element(close_button).click().perform()
                    self.log("✅ Closed profile popup")
                    time.sleep(0.3)
                    return
                except Exception:
                    continue

            # JavaScript fallback
            self.driver.execute_script("""
                const closeBtn = document.querySelector('button[aria-label="Close"]');
                if (closeBtn) closeBtn.click();
            """)
        except Exception as e:
            self.log(f"⚠️  Error closing popup: {e}")

        time.sleep(0.5)

    def send_messages(self):
        """Main messaging loop"""
        wait = WebDriverWait(self.driver, 3)
        no_new_profiles_count = 0
        profiles_messaged = 0

        while self.running:
            # Check for end message
            try:
                end_message = self.driver.find_element(By.XPATH, '//p[contains(text(), "We have already shown you everyone.")]')
                if end_message.is_displayed():
                    self.log(f"🎉 SUCCESS! Messaged {profiles_messaged} profiles. Campaign complete!")
                    break
            except Exception:
                pass

            # Get profile buttons
            profile_buttons = self.driver.find_elements(
                By.CSS_SELECTOR, "li.profile-card-element button.outline-hidden"
            )

            if not profile_buttons:
                self.log("⚠️  No profiles visible, triggering refresh...")
                self.driver.execute_script("window.scrollBy(0, 300);")
                time.sleep(1)
                self.driver.execute_script("window.scrollBy(0, -300);")
                time.sleep(1)
                no_new_profiles_count += 1
                if no_new_profiles_count >= 5:
                    self.log(f"🛑 Campaign complete! Messaged {profiles_messaged} profiles total.")
                    break
                continue

            no_new_profiles_count = 0
            self.log(f"📋 Found {len(profile_buttons)} profiles on page")

            # Shuffle for randomness
            random.shuffle(profile_buttons)

            for i in range(len(profile_buttons)):
                if not self.running:
                    self.log("⏹️  Bot stopped by user")
                    return

                try:
                    profile_buttons = self.driver.find_elements(
                        By.CSS_SELECTOR, "li.profile-card-element button.outline-hidden"
                    )
                    button = profile_buttons[i]
                    profile_label = button.get_attribute("aria-label")

                    if not profile_label or profile_label in self.messaged_profiles:
                        continue

                    self.messaged_profiles.add(profile_label)

                    # Open profile
                    ActionChains(self.driver).move_to_element(button).click().perform()

                    self.log(f"⏳ Loading profile '{profile_label}'...")
                    try:
                        WebDriverWait(self.driver, 5).until(
                            lambda d: d.find_elements(By.CSS_SELECTOR, 'span[data-testid="social-icebreaker-filled"]') or
                                      d.find_elements(By.CSS_SELECTOR, 'span[data-testid="chat-status-requested"]')
                        )
                        self.log(f"✅ Profile loaded: {profile_label}")
                    except Exception as e:
                        self.log(f"⚠️  Profile load timeout: {e}")
                        self.close_profile_popup()
                        continue

                    # Check if already messaged
                    try:
                        self.driver.find_element(By.CSS_SELECTOR, 'span[data-testid="chat-status-requested"]')
                        self.log(f"⏭️  Skipping '{profile_label}' - already messaged")
                        self.close_profile_popup()
                        continue
                    except Exception:
                        pass

                    # Send message
                    try:
                        icebreaker_icon = wait.until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, 'span[data-testid="social-icebreaker-filled"]'))
                        )
                        icebreaker_icon.click()
                        self.random_wait(0.5, 0.5)

                        message_box = wait.until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, 'textarea[name="message"]'))
                        )

                        # Focus textbox
                        ActionChains(self.driver).move_to_element(message_box).click().perform()
                        self.random_wait(0.1, 0.2)

                        # Type single char to activate button
                        message_box.send_keys("H")
                        self.random_wait(0.1, 0.2)

                        # Inject full message
                        self.driver.execute_script("""
                            arguments[0].value = arguments[1];
                            arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                            arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                            arguments[0].focus();
                        """, message_box, self.message)
                        self.random_wait(0.2, 0.3)

                        # Send
                        send_button = wait.until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"] span[data-testid="send"]'))
                        )
                        send_button.click()
                        profiles_messaged += 1
                        self.log(f"📨 Message sent to '{profile_label}' ({profiles_messaged} total)")
                        self.random_wait(0.3, 0.5)

                    except Exception as e:
                        self.log(f"⚠️  Failed to message '{profile_label}': {e}")

                    self.save_profiles()
                    self.close_profile_popup()

                except StaleElementReferenceException:
                    self.log("♻️  Stale element - retrying")
                    continue
                except Exception as e:
                    self.log(f"⚠️  Error with profile: {e}")
                    self.close_profile_popup()

            # Scroll for more
            self.scroll_to_bottom()

    def run(self):
        """Main bot execution"""
        try:
            self.running = True
            self.setup_driver()
            self.navigate_to_skout()
            self.log(f"🤖 Bot started with speed {self.speed}/10")
            self.log(f"💬 Message: {self.message}")
            self.send_messages()
        except Exception as e:
            self.log(f"💥 Fatal error: {e}")
        finally:
            self.stop()

    def stop(self):
        """Stop the bot and cleanup"""
        self.running = False
        if self.driver:
            try:
                self.save_profiles()
                self.driver.quit()
                self.log("✅ Browser closed, profiles saved")
            except Exception as e:
                self.log(f"⚠️  Shutdown error: {e}")


class SkoutZGUI:
    """Modern GUI for SkoutZ Bot"""

    # SKOUT.com Color Palette
    COLORS = {
        'primary': '#8B5CF6',      # Purple
        'secondary': '#6366F1',    # Indigo
        'success': '#10B981',      # Green
        'danger': '#EF4444',       # Red
        'bg_dark': '#1F2937',      # Dark gray
        'bg_light': '#374151',     # Light gray
        'text': '#F9FAFB',         # White text
        'text_muted': '#9CA3AF',   # Muted text
    }

    def __init__(self, root):
        self.root = root
        self.root.title("SkoutZ - Marketing Automation")
        self.root.geometry("800x700")
        self.root.configure(bg=self.COLORS['bg_dark'])

        self.bot = None
        self.bot_thread = None
        self.log_queue = queue.Queue()

        # Configure styles
        self.setup_styles()
        self.create_widgets()
        self.process_log_queue()

    def setup_styles(self):
        """Configure ttk styles with SKOUT colors"""
        style = ttk.Style()
        style.theme_use('clam')

        # Configure frame
        style.configure('Dark.TFrame', background=self.COLORS['bg_dark'])
        style.configure('Light.TFrame', background=self.COLORS['bg_light'])

        # Configure labels
        style.configure('Title.TLabel',
                       background=self.COLORS['bg_dark'],
                       foreground=self.COLORS['primary'],
                       font=('Arial', 24, 'bold'))
        style.configure('Header.TLabel',
                       background=self.COLORS['bg_dark'],
                       foreground=self.COLORS['text'],
                       font=('Arial', 12, 'bold'))
        style.configure('Normal.TLabel',
                       background=self.COLORS['bg_dark'],
                       foreground=self.COLORS['text'],
                       font=('Arial', 10))

    def create_widgets(self):
        """Build GUI layout"""
        # Main container
        main_frame = ttk.Frame(self.root, style='Dark.TFrame', padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title = ttk.Label(main_frame, text="SkoutZ", style='Title.TLabel')
        title.pack(pady=(0, 10))

        subtitle = ttk.Label(main_frame, text="Marketing Automation Pro",
                           style='Normal.TLabel')
        subtitle.pack(pady=(0, 20))

        # Message section
        msg_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        msg_frame.pack(fill=tk.X, pady=10)

        ttk.Label(msg_frame, text="Message to Send:", style='Header.TLabel').pack(anchor=tk.W)

        self.message_text = tk.Text(msg_frame, height=4, width=60,
                                   bg=self.COLORS['bg_light'],
                                   fg=self.COLORS['text'],
                                   font=('Arial', 11),
                                   insertbackground=self.COLORS['text'],
                                   relief=tk.FLAT,
                                   padx=10, pady=10)
        self.message_text.pack(fill=tk.X, pady=5)
        self.message_text.insert('1.0', 'Hi! How are you doing today? 😊')

        # Speed control section
        speed_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        speed_frame.pack(fill=tk.X, pady=10)

        speed_label_frame = ttk.Frame(speed_frame, style='Dark.TFrame')
        speed_label_frame.pack(fill=tk.X)

        ttk.Label(speed_label_frame, text="Speed:", style='Header.TLabel').pack(side=tk.LEFT)
        self.speed_value_label = ttk.Label(speed_label_frame, text="7",
                                          style='Header.TLabel',
                                          foreground=self.COLORS['primary'])
        self.speed_value_label.pack(side=tk.LEFT, padx=10)

        ttk.Label(speed_label_frame, text="(1=Slow, 10=Fast)",
                 style='Normal.TLabel',
                 foreground=self.COLORS['text_muted']).pack(side=tk.LEFT)

        # Speed slider
        self.speed_var = tk.IntVar(value=7)
        self.speed_slider = tk.Scale(speed_frame, from_=1, to=10,
                                    orient=tk.HORIZONTAL,
                                    variable=self.speed_var,
                                    command=self.update_speed_label,
                                    bg=self.COLORS['bg_light'],
                                    fg=self.COLORS['text'],
                                    troughcolor=self.COLORS['bg_dark'],
                                    activebackground=self.COLORS['primary'],
                                    highlightthickness=0,
                                    length=400,
                                    width=20,
                                    relief=tk.FLAT)
        self.speed_slider.pack(pady=5)

        # Control buttons
        btn_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        btn_frame.pack(pady=20)

        self.start_btn = tk.Button(btn_frame, text="▶ START",
                                  command=self.start_bot,
                                  bg=self.COLORS['success'],
                                  fg='white',
                                  font=('Arial', 14, 'bold'),
                                  width=15,
                                  height=2,
                                  relief=tk.FLAT,
                                  cursor='hand2',
                                  activebackground='#059669')
        self.start_btn.pack(side=tk.LEFT, padx=10)

        self.stop_btn = tk.Button(btn_frame, text="⏹ STOP",
                                 command=self.stop_bot,
                                 bg=self.COLORS['danger'],
                                 fg='white',
                                 font=('Arial', 14, 'bold'),
                                 width=15,
                                 height=2,
                                 relief=tk.FLAT,
                                 cursor='hand2',
                                 state=tk.DISABLED,
                                 activebackground='#DC2626')
        self.stop_btn.pack(side=tk.LEFT, padx=10)

        # Status section
        status_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        status_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        ttk.Label(status_frame, text="Activity Log:", style='Header.TLabel').pack(anchor=tk.W)

        # Log viewer
        self.log_viewer = scrolledtext.ScrolledText(status_frame,
                                                    height=15,
                                                    bg=self.COLORS['bg_light'],
                                                    fg=self.COLORS['text'],
                                                    font=('Courier', 9),
                                                    relief=tk.FLAT,
                                                    padx=10,
                                                    pady=10)
        self.log_viewer.pack(fill=tk.BOTH, expand=True, pady=5)
        self.log_viewer.config(state=tk.DISABLED)

        # Footer
        footer = ttk.Label(main_frame,
                         text="SkoutZ v2.0 | Powered by SkoutZ Marketing Automation",
                         style='Normal.TLabel',
                         foreground=self.COLORS['text_muted'])
        footer.pack(pady=10)

    def update_speed_label(self, value):
        """Update speed label when slider moves"""
        self.speed_value_label.config(text=str(value))

    def log_message(self, message):
        """Queue log message for GUI thread"""
        self.log_queue.put(message)

    def process_log_queue(self):
        """Process queued log messages"""
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.log_viewer.config(state=tk.NORMAL)
                self.log_viewer.insert(tk.END, message + '\n')
                self.log_viewer.see(tk.END)
                self.log_viewer.config(state=tk.DISABLED)
        except queue.Empty:
            pass

        self.root.after(100, self.process_log_queue)

    def start_bot(self):
        """Start the bot in background thread"""
        message = self.message_text.get('1.0', tk.END).strip()

        if not message:
            messagebox.showerror("Error", "Please enter a message to send!")
            return

        speed = self.speed_var.get()

        # Disable controls
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.message_text.config(state=tk.DISABLED)
        self.speed_slider.config(state=tk.DISABLED)

        # Clear log
        self.log_viewer.config(state=tk.NORMAL)
        self.log_viewer.delete('1.0', tk.END)
        self.log_viewer.config(state=tk.DISABLED)

        # Start bot
        self.bot = SkoutZBot(message, speed, self.log_message)
        self.bot_thread = threading.Thread(target=self.bot.run, daemon=True)
        self.bot_thread.start()

        self.log_message("🚀 SkoutZ Bot Starting...")

    def stop_bot(self):
        """Stop the running bot"""
        if self.bot:
            self.log_message("⏹️  Stopping bot...")
            self.bot.stop()

        # Re-enable controls
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.message_text.config(state=tk.NORMAL)
        self.speed_slider.config(state=tk.NORMAL)


def main():
    """Application entry point"""
    # Setup logging
    logging.basicConfig(
        filename="skout_bot_log.txt",
        level=logging.INFO,
        format="%(asctime)s - %(message)s"
    )

    # Create and run GUI
    root = tk.Tk()
    app = SkoutZGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
