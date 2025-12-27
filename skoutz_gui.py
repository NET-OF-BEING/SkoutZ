#!/usr/bin/env python3
"""
SkoutZ - Professional SKOUT Marketing Automation GUI v2.0
==========================================================
Author: Derek Chan (Enhanced with Match Game)
Features:
- Modern GUI with SKOUT.com color palette
- Browse Profiles tab - Traditional profile messaging
- Match Game tab - Automated match game messaging
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
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager


class MatchGameBot:
    """Match Game automation engine"""

    def __init__(self, message, speed, log_callback):
        self.message = message
        self.speed = speed  # 1-10
        self.log_callback = log_callback
        self.driver = None
        self.running = False

    def log(self, msg):
        """Send log messages to GUI"""
        if self.log_callback:
            self.log_callback(msg)
        logging.info(msg)

    def random_wait(self, base_seconds=1, variation=1):
        """Speed-adjusted random wait"""
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

    def navigate_to_match_game(self):
        """Navigate to Match Game"""
        self.log("🎮 Loading Match Game...")
        self.driver.get("https://app.skout.com/match-game")
        self.random_wait(2, 1)
        self.log("✅ Match Game loaded!")

    def send_message_loop(self):
        """Main messaging loop for Match Game"""
        messages_sent = 0

        while self.running:
            try:
                # Click message button in the middle
                self.log("📨 Looking for message button...")

                try:
                    # Wait for message button to be clickable
                    message_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[.//span[contains(text(), 'Message')]]"))
                    )
                    message_button.click()
                    self.log("✅ Clicked message button")
                    self.random_wait(0.5, 0.5)

                except Exception as e:
                    self.log(f"⚠️  Message button not found, retrying... ({e})")
                    self.random_wait(1, 1)
                    continue

                # Click and type in textarea
                try:
                    textarea = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'textarea[data-testid="chat-message-input"]'))
                    )

                    # Click to focus
                    ActionChains(self.driver).move_to_element(textarea).click().perform()
                    self.random_wait(0.2, 0.2)

                    # Clear and type message
                    textarea.clear()
                    textarea.send_keys(self.message)
                    self.log(f"💬 Typed message: {self.message}")
                    self.random_wait(0.3, 0.3)

                except Exception as e:
                    self.log(f"⚠️  Textarea not found: {e}")
                    continue

                # Click send button
                try:
                    send_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"][data-testid="send"], button[type="submit"] span[data-testid="send"]'))
                    )
                    send_button.click()
                    messages_sent += 1
                    self.log(f"📤 Message sent! ({messages_sent} total)")
                    self.random_wait(1, 1)

                except Exception as e:
                    self.log(f"⚠️  Send button not found: {e}")
                    continue

                # Wait before next iteration
                self.random_wait(2, 2)

            except Exception as e:
                self.log(f"⚠️  Error in message loop: {e}")
                self.random_wait(2, 1)

        self.log(f"🛑 Match Game bot stopped. Total messages sent: {messages_sent}")

    def run(self):
        """Main bot execution"""
        try:
            self.running = True
            self.setup_driver()
            self.navigate_to_match_game()
            self.log(f"🤖 Match Game bot started with speed {self.speed}/10")
            self.log(f"💬 Message: {self.message}")
            self.send_message_loop()
        except Exception as e:
            self.log(f"💥 Fatal error: {e}")
        finally:
            self.stop()

    def stop(self):
        """Stop the bot and cleanup"""
        self.running = False
        if self.driver:
            try:
                self.driver.quit()
                self.log("✅ Browser closed")
            except Exception as e:
                self.log(f"⚠️  Shutdown error: {e}")


class SkoutZBot:
    """Core bot engine - Browse Profiles mode"""

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
            try:
                end_message = self.driver.find_element(By.XPATH, '//p[contains(text(), "We have already shown you everyone.")]')
                if end_message.is_displayed():
                    self.log(f"🎉 SUCCESS! Messaged {profiles_messaged} profiles. Campaign complete!")
                    break
            except Exception:
                pass

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

                    try:
                        self.driver.find_element(By.CSS_SELECTOR, 'span[data-testid="chat-status-requested"]')
                        self.log(f"⏭️  Skipping '{profile_label}' - already messaged")
                        self.close_profile_popup()
                        continue
                    except Exception:
                        pass

                    try:
                        icebreaker_icon = wait.until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, 'span[data-testid="social-icebreaker-filled"]'))
                        )
                        icebreaker_icon.click()
                        self.random_wait(0.5, 0.5)

                        message_box = wait.until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, 'textarea[name="message"]'))
                        )

                        ActionChains(self.driver).move_to_element(message_box).click().perform()
                        self.random_wait(0.1, 0.2)

                        message_box.send_keys("H")
                        self.random_wait(0.1, 0.2)

                        self.driver.execute_script("""
                            arguments[0].value = arguments[1];
                            arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                            arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                            arguments[0].focus();
                        """, message_box, self.message)
                        self.random_wait(0.2, 0.3)

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
    """Modern GUI for SkoutZ Bot with tabbed interface"""

    # SKOUT.com Color Palette
    COLORS = {
        'primary': '#8B5CF6',
        'secondary': '#6366F1',
        'success': '#10B981',
        'danger': '#EF4444',
        'bg_dark': '#1F2937',
        'bg_light': '#374151',
        'text': '#F9FAFB',
        'text_muted': '#9CA3AF',
    }

    def __init__(self, root):
        self.root = root
        self.root.title("SkoutZ - Marketing Automation Pro")
        self.root.geometry("800x750")
        self.root.configure(bg=self.COLORS['bg_dark'])

        self.browse_bot = None
        self.match_bot = None
        self.bot_thread = None
        self.log_queue = queue.Queue()

        self.setup_styles()
        self.create_widgets()
        self.process_log_queue()

    def setup_styles(self):
        """Configure ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')

        style.configure('Dark.TFrame', background=self.COLORS['bg_dark'])
        style.configure('Light.TFrame', background=self.COLORS['bg_light'])

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

        # Notebook styling
        style.configure('TNotebook', background=self.COLORS['bg_dark'], borderwidth=0)
        style.configure('TNotebook.Tab',
                       background=self.COLORS['bg_light'],
                       foreground=self.COLORS['text'],
                       padding=[20, 10],
                       font=('Arial', 11, 'bold'))
        style.map('TNotebook.Tab',
                 background=[('selected', self.COLORS['primary'])],
                 foreground=[('selected', 'white')])

    def create_widgets(self):
        """Build GUI layout"""
        main_frame = ttk.Frame(self.root, style='Dark.TFrame', padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title = ttk.Label(main_frame, text="SkoutZ", style='Title.TLabel')
        title.pack(pady=(0, 5))

        subtitle = ttk.Label(main_frame, text="Marketing Automation Pro v2.0",
                           style='Normal.TLabel')
        subtitle.pack(pady=(0, 15))

        # Tabbed interface
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Create tabs
        self.create_browse_tab()
        self.create_match_tab()

        # Footer
        footer = ttk.Label(main_frame,
                         text="SkoutZ v2.0 | Browse Profiles & Match Game Automation",
                         style='Normal.TLabel',
                         foreground=self.COLORS['text_muted'])
        footer.pack(pady=10)

    def create_browse_tab(self):
        """Create Browse Profiles tab"""
        browse_frame = ttk.Frame(self.notebook, style='Dark.TFrame', padding=15)
        self.notebook.add(browse_frame, text='Browse Profiles')

        # Message section
        msg_frame = ttk.Frame(browse_frame, style='Dark.TFrame')
        msg_frame.pack(fill=tk.X, pady=10)

        ttk.Label(msg_frame, text="Message to Send:", style='Header.TLabel').pack(anchor=tk.W)

        self.browse_message_text = tk.Text(msg_frame, height=4, width=60,
                                   bg=self.COLORS['bg_light'],
                                   fg=self.COLORS['text'],
                                   font=('Arial', 11),
                                   insertbackground=self.COLORS['text'],
                                   relief=tk.FLAT,
                                   padx=10, pady=10)
        self.browse_message_text.pack(fill=tk.X, pady=5)
        self.browse_message_text.insert('1.0', 'Hi! How are you doing today? 😊')

        # Speed control
        speed_frame = ttk.Frame(browse_frame, style='Dark.TFrame')
        speed_frame.pack(fill=tk.X, pady=10)

        speed_label_frame = ttk.Frame(speed_frame, style='Dark.TFrame')
        speed_label_frame.pack(fill=tk.X)

        ttk.Label(speed_label_frame, text="Speed:", style='Header.TLabel').pack(side=tk.LEFT)
        self.browse_speed_value_label = ttk.Label(speed_label_frame, text="7",
                                          style='Header.TLabel',
                                          foreground=self.COLORS['primary'])
        self.browse_speed_value_label.pack(side=tk.LEFT, padx=10)

        ttk.Label(speed_label_frame, text="(1=Slow, 10=Fast)",
                 style='Normal.TLabel',
                 foreground=self.COLORS['text_muted']).pack(side=tk.LEFT)

        self.browse_speed_var = tk.IntVar(value=7)
        self.browse_speed_slider = tk.Scale(speed_frame, from_=1, to=10,
                                    orient=tk.HORIZONTAL,
                                    variable=self.browse_speed_var,
                                    command=lambda v: self.browse_speed_value_label.config(text=str(v)),
                                    bg=self.COLORS['bg_light'],
                                    fg=self.COLORS['text'],
                                    troughcolor=self.COLORS['bg_dark'],
                                    activebackground=self.COLORS['primary'],
                                    highlightthickness=0,
                                    length=400,
                                    width=20,
                                    relief=tk.FLAT)
        self.browse_speed_slider.pack(pady=5)

        # Control buttons
        btn_frame = ttk.Frame(browse_frame, style='Dark.TFrame')
        btn_frame.pack(pady=15)

        self.browse_start_btn = tk.Button(btn_frame, text="▶ START",
                                  command=lambda: self.start_bot('browse'),
                                  bg=self.COLORS['success'],
                                  fg='white',
                                  font=('Arial', 14, 'bold'),
                                  width=15,
                                  height=2,
                                  relief=tk.FLAT,
                                  cursor='hand2',
                                  activebackground='#059669')
        self.browse_start_btn.pack(side=tk.LEFT, padx=10)

        self.browse_stop_btn = tk.Button(btn_frame, text="⏹ STOP",
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
        self.browse_stop_btn.pack(side=tk.LEFT, padx=10)

        # Status
        status_frame = ttk.Frame(browse_frame, style='Dark.TFrame')
        status_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        ttk.Label(status_frame, text="Activity Log:", style='Header.TLabel').pack(anchor=tk.W)

        self.browse_log_viewer = scrolledtext.ScrolledText(status_frame,
                                                    height=12,
                                                    bg=self.COLORS['bg_light'],
                                                    fg=self.COLORS['text'],
                                                    font=('Courier', 9),
                                                    relief=tk.FLAT,
                                                    padx=10,
                                                    pady=10)
        self.browse_log_viewer.pack(fill=tk.BOTH, expand=True, pady=5)
        self.browse_log_viewer.config(state=tk.DISABLED)

    def create_match_tab(self):
        """Create Match Game tab"""
        match_frame = ttk.Frame(self.notebook, style='Dark.TFrame', padding=15)
        self.notebook.add(match_frame, text='Match Game')

        # Header
        ttk.Label(match_frame, text="🎮 Match Game Automation",
                 style='Header.TLabel',
                 foreground=self.COLORS['primary']).pack(pady=(0, 10))

        ttk.Label(match_frame, text="Automatically send messages in Match Game mode",
                 style='Normal.TLabel',
                 foreground=self.COLORS['text_muted']).pack(pady=(0, 15))

        # Message section
        msg_frame = ttk.Frame(match_frame, style='Dark.TFrame')
        msg_frame.pack(fill=tk.X, pady=10)

        ttk.Label(msg_frame, text="Message to Send:", style='Header.TLabel').pack(anchor=tk.W)

        self.match_message_text = tk.Text(msg_frame, height=4, width=60,
                                   bg=self.COLORS['bg_light'],
                                   fg=self.COLORS['text'],
                                   font=('Arial', 11),
                                   insertbackground=self.COLORS['text'],
                                   relief=tk.FLAT,
                                   padx=10, pady=10)
        self.match_message_text.pack(fill=tk.X, pady=5)
        self.match_message_text.insert('1.0', 'Hey! What are you up to? 😊')

        # Speed control
        speed_frame = ttk.Frame(match_frame, style='Dark.TFrame')
        speed_frame.pack(fill=tk.X, pady=10)

        speed_label_frame = ttk.Frame(speed_frame, style='Dark.TFrame')
        speed_label_frame.pack(fill=tk.X)

        ttk.Label(speed_label_frame, text="Speed:", style='Header.TLabel').pack(side=tk.LEFT)
        self.match_speed_value_label = ttk.Label(speed_label_frame, text="7",
                                          style='Header.TLabel',
                                          foreground=self.COLORS['primary'])
        self.match_speed_value_label.pack(side=tk.LEFT, padx=10)

        ttk.Label(speed_label_frame, text="(1=Slow, 10=Fast)",
                 style='Normal.TLabel',
                 foreground=self.COLORS['text_muted']).pack(side=tk.LEFT)

        self.match_speed_var = tk.IntVar(value=7)
        self.match_speed_slider = tk.Scale(speed_frame, from_=1, to=10,
                                    orient=tk.HORIZONTAL,
                                    variable=self.match_speed_var,
                                    command=lambda v: self.match_speed_value_label.config(text=str(v)),
                                    bg=self.COLORS['bg_light'],
                                    fg=self.COLORS['text'],
                                    troughcolor=self.COLORS['bg_dark'],
                                    activebackground=self.COLORS['primary'],
                                    highlightthickness=0,
                                    length=400,
                                    width=20,
                                    relief=tk.FLAT)
        self.match_speed_slider.pack(pady=5)

        # Control buttons
        btn_frame = ttk.Frame(match_frame, style='Dark.TFrame')
        btn_frame.pack(pady=15)

        self.match_start_btn = tk.Button(btn_frame, text="▶ START",
                                  command=lambda: self.start_bot('match'),
                                  bg=self.COLORS['success'],
                                  fg='white',
                                  font=('Arial', 14, 'bold'),
                                  width=15,
                                  height=2,
                                  relief=tk.FLAT,
                                  cursor='hand2',
                                  activebackground='#059669')
        self.match_start_btn.pack(side=tk.LEFT, padx=10)

        self.match_stop_btn = tk.Button(btn_frame, text="⏹ STOP",
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
        self.match_stop_btn.pack(side=tk.LEFT, padx=10)

        # Status
        status_frame = ttk.Frame(match_frame, style='Dark.TFrame')
        status_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        ttk.Label(status_frame, text="Activity Log:", style='Header.TLabel').pack(anchor=tk.W)

        self.match_log_viewer = scrolledtext.ScrolledText(status_frame,
                                                    height=12,
                                                    bg=self.COLORS['bg_light'],
                                                    fg=self.COLORS['text'],
                                                    font=('Courier', 9),
                                                    relief=tk.FLAT,
                                                    padx=10,
                                                    pady=10)
        self.match_log_viewer.pack(fill=tk.BOTH, expand=True, pady=5)
        self.match_log_viewer.config(state=tk.DISABLED)

    def log_message(self, message):
        """Queue log message"""
        self.log_queue.put(message)

    def process_log_queue(self):
        """Process queued log messages"""
        try:
            while True:
                message = self.log_queue.get_nowait()

                # Determine which log viewer to use based on current tab
                current_tab = self.notebook.index(self.notebook.select())
                log_viewer = self.browse_log_viewer if current_tab == 0 else self.match_log_viewer

                log_viewer.config(state=tk.NORMAL)
                log_viewer.insert(tk.END, message + '\n')
                log_viewer.see(tk.END)
                log_viewer.config(state=tk.DISABLED)
        except queue.Empty:
            pass

        self.root.after(100, self.process_log_queue)

    def start_bot(self, mode):
        """Start the bot in specified mode"""
        if mode == 'browse':
            message = self.browse_message_text.get('1.0', tk.END).strip()
            speed = self.browse_speed_var.get()

            if not message:
                messagebox.showerror("Error", "Please enter a message to send!")
                return

            # Disable controls
            self.browse_start_btn.config(state=tk.DISABLED)
            self.browse_stop_btn.config(state=tk.NORMAL)
            self.browse_message_text.config(state=tk.DISABLED)
            self.browse_speed_slider.config(state=tk.DISABLED)

            # Clear log
            self.browse_log_viewer.config(state=tk.NORMAL)
            self.browse_log_viewer.delete('1.0', tk.END)
            self.browse_log_viewer.config(state=tk.DISABLED)

            # Start bot
            self.browse_bot = SkoutZBot(message, speed, self.log_message)
            self.bot_thread = threading.Thread(target=self.browse_bot.run, daemon=True)
            self.bot_thread.start()

        else:  # match
            message = self.match_message_text.get('1.0', tk.END).strip()
            speed = self.match_speed_var.get()

            if not message:
                messagebox.showerror("Error", "Please enter a message to send!")
                return

            # Disable controls
            self.match_start_btn.config(state=tk.DISABLED)
            self.match_stop_btn.config(state=tk.NORMAL)
            self.match_message_text.config(state=tk.DISABLED)
            self.match_speed_slider.config(state=tk.DISABLED)

            # Clear log
            self.match_log_viewer.config(state=tk.NORMAL)
            self.match_log_viewer.delete('1.0', tk.END)
            self.match_log_viewer.config(state=tk.DISABLED)

            # Start bot
            self.match_bot = MatchGameBot(message, speed, self.log_message)
            self.bot_thread = threading.Thread(target=self.match_bot.run, daemon=True)
            self.bot_thread.start()

    def stop_bot(self):
        """Stop the running bot"""
        if self.browse_bot:
            self.log_message("⏹️  Stopping Browse bot...")
            self.browse_bot.stop()
            self.browse_start_btn.config(state=tk.NORMAL)
            self.browse_stop_btn.config(state=tk.DISABLED)
            self.browse_message_text.config(state=tk.NORMAL)
            self.browse_speed_slider.config(state=tk.NORMAL)

        if self.match_bot:
            self.log_message("⏹️  Stopping Match bot...")
            self.match_bot.stop()
            self.match_start_btn.config(state=tk.NORMAL)
            self.match_stop_btn.config(state=tk.DISABLED)
            self.match_message_text.config(state=tk.NORMAL)
            self.match_speed_slider.config(state=tk.NORMAL)


def main():
    """Application entry point"""
    logging.basicConfig(
        filename="skout_bot_log.txt",
        level=logging.INFO,
        format="%(asctime)s - %(message)s"
    )

    root = tk.Tk()
    app = SkoutZGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
