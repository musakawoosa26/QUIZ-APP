"""
╔══════════════════════════════════════════════════════════════════════╗
║                   QUIZ MASTER PRO v3.0 ULTRA                         ║
║        Next-Generation AI-Powered Adaptive Quiz Platform             ║
║                                                                      ║
║  Designed with a stunning modern Glassmorphic & Neo-Sleek UI         ║
║  Powered by CustomTkinter, Google Gemini AI & Procedural Generators  ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import json
import time
import math
import random
import sqlite3
import threading
import ssl
import urllib.request
import urllib.error
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

# ── SSL Context Helper for macOS ──────────────────────────────
def get_ssl_context():
    """Create a verified SSL context using certifi or unverified fallback on macOS."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        pass
    try:
        return ssl._create_unverified_context()
    except Exception:
        return None


# ── Optional Google Generative AI SDK ─────────────────────────
try:
    import google.generativeai as genai
    GEMINI_SDK_AVAILABLE = True
except ImportError:
    GEMINI_SDK_AVAILABLE = False


# ================================================================
#  GLOBAL CONFIGURATION & PALETTES
# ================================================================

APP_TITLE = "Quiz Master Pro"
APP_VERSION = "v3.0 Ultra"

# Modern Color Palette
PALETTE = {
    # Theme backgrounds & surfaces (Light, Dark)
    "bg_main":        ("#F8FAFC", "#0B0F19"),
    "header_bg":      ("#FFFFFF", "#111827"),
    "card_bg":        ("#FFFFFF", "#141D2F"),
    "card_bg_alt":    ("#F1F5F9", "#1B253B"),
    "card_border":    ("#E2E8F0", "#24324D"),
    "card_hover":     ("#F8FAFC", "#1E2B45"),
    
    # Text colors
    "text_primary":   ("#0F172A", "#F8FAFC"),
    "text_secondary": ("#475569", "#94A3B8"),
    "text_muted":     ("#94A3B8", "#64748B"),
    
    # Accent & Status Colors
    "primary":        "#6366F1",  # Indigo
    "primary_hover":  "#4F46E5",
    "primary_light":  ("#EEF2FF", "#1E1E38"),
    
    "success":        "#10B981",  # Emerald
    "success_hover":  "#059669",
    "success_light":  ("#ECFDF5", "#064E3B"),
    
    "danger":         "#EF4444",  # Crimson
    "danger_hover":   "#DC2626",
    "danger_light":   ("#FEF2F2", "#450A0A"),
    
    "warning":        "#F59E0B",  # Amber/Gold
    "warning_hover":  "#D97706",
    "warning_light":  ("#FFFBEB", "#451A03"),
    
    "accent_cyan":    "#06B6D4",
    "accent_cyan_hov": "#0891B2",
    "accent_purple":  "#8B5CF6",
    "accent_pink":    "#EC4899",
}

# Categories Definition with Rich Icon & Color Theme
CATEGORIES_DATA = [
    {
        "id": "General Knowledge",
        "name": "General Knowledge",
        "icon": "🌎",
        "desc": "World capitals, currencies, cultures & famous facts",
        "color": "#3B82F6",
        "hover": "#2563EB",
    },
    {
        "id": "Mathematics",
        "name": "Mathematics",
        "icon": "🔢",
        "desc": "Arithmetic, algebra, mental calculations & equations",
        "color": "#8B5CF6",
        "hover": "#7C3AED",
    },
    {
        "id": "Science",
        "name": "Science & Nature",
        "icon": "🔬",
        "desc": "Biology, chemistry, physics, astronomy & the human body",
        "color": "#10B981",
        "hover": "#059669",
    },
    {
        "id": "Computer Science",
        "name": "Computer Science",
        "icon": "💻",
        "desc": "Hardware, algorithms, binary logic & networking fundamentals",
        "color": "#F59E0B",
        "hover": "#D97706",
    },
    {
        "id": "Programming",
        "name": "Programming & Code",
        "icon": "👨‍💻",
        "desc": "Python, data structures, syntax, methods & OOP concepts",
        "color": "#EC4899",
        "hover": "#DB2777",
    },
    {
        "id": "History",
        "name": "World History",
        "icon": "📜",
        "desc": "Historic revolutions, civilizations, leaders & key milestones",
        "color": "#EAB308",
        "hover": "#CA8A04",
    },
    {
        "id": "Geography",
        "name": "Earth & Geography",
        "icon": "🌍",
        "desc": "Oceans, continents, mountain ranges, rivers & landscapes",
        "color": "#06B6D4",
        "hover": "#0891B2",
    },
]


# ================================================================
#  DATABASE MANAGER
# ================================================================

class DatabaseManager:
    """Manages SQLite storage for quiz records, analytics, and user preferences."""
    def __init__(self, db_filename="quiz_results.db"):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(base_dir, db_filename)
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS results (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    name        TEXT,
                    category    TEXT,
                    difficulty  TEXT DEFAULT 'Medium',
                    score       INTEGER,
                    total       INTEGER,
                    percentage  REAL,
                    streak_max  INTEGER DEFAULT 0,
                    time_taken  REAL DEFAULT 0,
                    date        TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key   TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            conn.commit()

    def get_setting(self, key, default=None):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
                row = cursor.fetchone()
                return row[0] if row else default
        except Exception:
            return default

    def set_setting(self, key, value):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
                conn.commit()
        except Exception as e:
            print(f"Error saving setting {key}: {e}")

    def save_quiz_result(self, name, category, difficulty, score, total, percentage, streak_max, time_taken):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO results (name, category, difficulty, score, total, percentage, streak_max, time_taken)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (name, category, difficulty, score, total, round(percentage, 2), streak_max, round(time_taken, 1)))
                conn.commit()
        except Exception as e:
            print(f"Error saving result: {e}")

    def get_recent_results(self, limit=50, name_filter=None):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if name_filter:
                    cursor.execute("""
                        SELECT id, name, category, difficulty, score, total, percentage, streak_max, time_taken, date
                        FROM results WHERE name = ? ORDER BY id DESC LIMIT ?
                    """, (name_filter, limit))
                else:
                    cursor.execute("""
                        SELECT id, name, category, difficulty, score, total, percentage, streak_max, time_taken, date
                        FROM results ORDER BY id DESC LIMIT ?
                    """, (limit,))
                return cursor.fetchall()
        except Exception:
            return []

    def get_user_stats(self, student_name=None):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if student_name:
                    cursor.execute("""
                        SELECT COUNT(*), AVG(percentage), MAX(percentage), SUM(score), SUM(total), MAX(streak_max), AVG(time_taken)
                        FROM results WHERE name = ?
                    """, (student_name,))
                else:
                    cursor.execute("""
                        SELECT COUNT(*), AVG(percentage), MAX(percentage), SUM(score), SUM(total), MAX(streak_max), AVG(time_taken)
                        FROM results
                    """)
                row = cursor.fetchone()
                return {
                    "total_quizzes": row[0] or 0,
                    "avg_pct": row[1] or 0.0,
                    "best_pct": row[2] or 0.0,
                    "total_score": row[3] or 0,
                    "total_questions": row[4] or 0,
                    "max_streak": row[5] or 0,
                    "avg_time": row[6] or 0.0
                }
        except Exception:
            return {
                "total_quizzes": 0, "avg_pct": 0.0, "best_pct": 0.0,
                "total_score": 0, "total_questions": 0, "max_streak": 0, "avg_time": 0.0
            }

    def get_category_breakdown(self, student_name=None):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if student_name:
                    cursor.execute("""
                        SELECT category, COUNT(*), AVG(percentage), MAX(percentage)
                        FROM results WHERE name = ? GROUP BY category ORDER BY AVG(percentage) DESC
                    """, (student_name,))
                else:
                    cursor.execute("""
                        SELECT category, COUNT(*), AVG(percentage), MAX(percentage)
                        FROM results GROUP BY category ORDER BY AVG(percentage) DESC
                    """)
                return cursor.fetchall()
        except Exception:
            return []

    def clear_all_history(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM results")
                conn.commit()
                return True
        except Exception:
            return False


# ================================================================
#  OFFLINE PROCEDURAL QUESTION GENERATORS
# ================================================================

def _wrong_options(correct, pool, n=3):
    wrong = [x for x in pool if x != correct]
    random.shuffle(wrong)
    return wrong[:n]

def gen_gk_questions(count, difficulty):
    capitals = {
        "France": "Paris", "Japan": "Tokyo", "Brazil": "Brasília", "Canada": "Ottawa",
        "Australia": "Canberra", "Germany": "Berlin", "Italy": "Rome", "Egypt": "Cairo",
        "Mexico": "Mexico City", "Argentina": "Buenos Aires", "China": "Beijing",
        "South Korea": "Seoul", "Spain": "Madrid", "Norway": "Oslo", "Greece": "Athens",
        "Netherlands": "Amsterdam", "Switzerland": "Bern", "New Zealand": "Wellington",
        "Portugal": "Lisbon", "India": "New Delhi", "Sweden": "Stockholm", "Finland": "Helsinki"
    }
    currencies = {
        "Japan": "Yen", "India": "Rupee", "United States": "Dollar",
        "United Kingdom": "Pound Sterling", "European Union": "Euro", "Switzerland": "Franc",
        "China": "Yuan", "Brazil": "Real", "South Korea": "Won", "Turkey": "Lira"
    }
    landmarks = [
        ("The Colosseum is located in which city?", "Rome", ["Athens", "Paris", "Barcelona"], "The ancient Colosseum stands in Rome, Italy."),
        ("The Taj Mahal was constructed primarily in which stone?", "White Marble", ["Red Sandstone", "Granite", "Limestone"], "Built with ivory-white marble by Shah Jahan."),
        ("Machu Picchu is an ancient citadel located in which country?", "Peru", ["Chile", "Bolivia", "Colombia"], "Machu Picchu is an Incan citadel in the Andes of Peru."),
        ("The Great Barrier Reef is situated off the coast of which nation?", "Australia", ["Indonesia", "Fiji", "New Zealand"], "It is the world's largest coral reef system in Australia."),
        ("The Statue of Liberty was a gift to the USA from which country?", "France", ["United Kingdom", "Spain", "Germany"], "Gifted by France in 1886 to commemorate freedom.")
    ]
    
    questions = []
    # Cap selection
    sampled_caps = random.sample(list(capitals.items()), min(count, len(capitals)))
    all_caps = list(capitals.values())
    for country, cap in sampled_caps:
        wrong = _wrong_options(cap, all_caps)
        questions.append({
            "question": f"What is the official capital city of {country}?",
            "options": [cap] + wrong,
            "answer": cap,
            "explanation": f"The capital city of {country} is {cap}."
        })
        
    for q, a, w, exp in landmarks:
        questions.append({"question": q, "options": [a] + w, "answer": a, "explanation": exp})
        
    random.shuffle(questions)
    return questions[:count]

def gen_math_questions(count, difficulty):
    questions = []
    for _ in range(count):
        if difficulty == "Easy":
            a, b = random.randint(3, 25), random.randint(3, 25)
            op = random.choice(["+", "-"])
            ans = a + b if op == "+" else a - b
            q_text = f"Calculate: {a} {op} {b}"
        elif difficulty == "Medium":
            a, b = random.randint(3, 14), random.randint(3, 12)
            op = random.choice(["×", "+", "-"])
            if op == "×":
                ans = a * b
            elif op == "+":
                ans = a + b
            else:
                ans = a - b
            q_text = f"Calculate: {a} {op} {b}"
        else:  # Hard
            kind = random.choice(["sqrt", "power", "mod", "order_of_ops"])
            if kind == "sqrt":
                root_val = random.randint(3, 20)
                sq = root_val * root_val
                ans = root_val
                q_text = f"What is the square root of {sq} (√{sq})?"
            elif kind == "power":
                base = random.randint(2, 6)
                exp = random.choice([2, 3])
                ans = base ** exp
                q_text = f"Compute {base} raised to the power of {exp} ({base}^{exp}):"
            elif kind == "mod":
                num = random.randint(15, 99)
                div = random.randint(3, 9)
                ans = num % div
                q_text = f"What is the remainder of {num} ÷ {div} ({num} mod {div})?"
            else:
                x, y, z = random.randint(2, 9), random.randint(2, 9), random.randint(1, 10)
                ans = (x * y) + z
                q_text = f"Solve according to order of operations: {x} × {y} + {z}"

        wrong = set()
        while len(wrong) < 3:
            offset = random.choice([-6, -4, -3, -2, -1, 1, 2, 3, 4, 6, 10])
            w = ans + offset
            if w != ans and w >= 0:
                wrong.add(w)
        opts = [str(ans)] + [str(w) for w in wrong]
        random.shuffle(opts)
        questions.append({
            "question": q_text,
            "options": opts,
            "answer": str(ans),
            "explanation": f"Evaluating the mathematical expression correctly yields {ans}."
        })
    return questions

def gen_science_questions(count, difficulty):
    pool = [
        ("What chemical element has the symbol 'Fe'?", "Iron", ["Gold", "Silver", "Lead"], "Fe originates from the Latin name 'Ferrum', meaning Iron."),
        ("What gas do photosynthetic plants primarily absorb?", "Carbon Dioxide", ["Oxygen", "Nitrogen", "Hydrogen"], "Plants convert CO₂ and water into glucose using sunlight."),
        ("Which planet in our solar system is nicknamed the 'Red Planet'?", "Mars", ["Venus", "Jupiter", "Saturn"], "Mars has an iron-oxide rich surface that imparts a reddish hue."),
        ("What is the speed of light in a vacuum (approximate)?", "300,000 km/s", ["150,000 km/s", "500,000 km/s", "1,000,000 km/s"], "Light travels at roughly 299,792 kilometers per second in a vacuum."),
        ("What is the fundamental unit of heredity in living organisms?", "Gene", ["Cell", "Protein", "Chromosome"], "Genes composed of DNA carry encoded instructions for traits."),
        ("What is the pH level of pure neutral distilled water?", "7.0", ["0.0", "5.5", "14.0"], "On the logarithmic pH scale, 7.0 indicates a neutral chemical solution."),
        ("Which organ produces insulin in the human body?", "Pancreas", ["Liver", "Kidney", "Gallbladder"], "The pancreas produces insulin to regulate glucose in the blood."),
        ("What is the hardest known natural mineral on Earth?", "Diamond", ["Quartz", "Topaz", "Corundum"], "Diamond ranks highest at 10 on the Mohs scale of mineral hardness."),
        ("How many chambers does a normal human heart possess?", "4", ["2", "3", "6"], "The human heart has 4 chambers: two atria and two ventricles."),
        ("What type of galaxy is the Milky Way?", "Barred Spiral", ["Elliptical", "Irregular", "Lenticular"], "Astronomers classify our Milky Way as a barred spiral galaxy."),
        ("What subatomic particle carries a negative electric charge?", "Electron", ["Proton", "Neutron", "Positron"], "Electrons orbit the nucleus and have an elementary charge of -1.")
    ]
    sampled = random.sample(pool, min(count, len(pool)))
    out = []
    for q, a, w, exp in sampled:
        opts = [a] + w
        random.shuffle(opts)
        out.append({"question": q, "options": opts, "answer": a, "explanation": exp})
    return out

def gen_cs_questions(count, difficulty):
    pool = [
        ("What does CPU stand for in computer hardware?", "Central Processing Unit", ["Central Process Utility", "Core Program Unit", "Computer Processing Unit"], "The CPU executes instructions and controls computational flow."),
        ("Which data structure strictly follows First-In, First-Out (FIFO)?", "Queue", ["Stack", "Binary Tree", "Hash Map"], "Queues process items in the order they arrive (FIFO)."),
        ("What is the average time complexity of Binary Search?", "O(log n)", ["O(n)", "O(n²)", "O(1)"], "Binary search eliminates half the remaining elements at each step."),
        ("What does HTTPS stand for?", "Hypertext Transfer Protocol Secure", ["High Text Transfer Protocol Secure", "Hyperlink Transit Protected System", "Host Transmission Protocol Standard"], "HTTPS encrypts communications using modern TLS/SSL security."),
        ("How many bits are in a single standard byte?", "8", ["4", "16", "32"], "A byte consists of exactly 8 binary digits (bits)."),
        ("Which protocol is universally used to assign dynamic IP addresses?", "DHCP", ["DNS", "FTP", "SNMP"], "DHCP (Dynamic Host Configuration Protocol) assigns network IPs automatically."),
        ("Which data structure operates on a Last-In, First-Out (LIFO) basis?", "Stack", ["Queue", "Linked List", "Heap"], "Stacks pop the most recently pushed item first (LIFO)."),
        ("What is the primary function of an operating system's kernel?", "Manage hardware resources & core processes", ["Render user web pages", "Compile high-level source code", "Manage database queries"], "The kernel is the core bridge between software applications and physical hardware.")
    ]
    sampled = random.sample(pool, min(count, len(pool)))
    out = []
    for q, a, w, exp in sampled:
        opts = [a] + w
        random.shuffle(opts)
        out.append({"question": q, "options": opts, "answer": a, "explanation": exp})
    return out

def gen_prog_questions(count, difficulty):
    pool = [
        ("Which keyword is used to declare a function in Python?", "def", ["function", "fun", "lambda"], "Python uses the 'def' keyword to define reusable functions."),
        ("Which Python data structure is strictly immutable once created?", "tuple", ["list", "set", "dictionary"], "Tuples cannot have elements added, deleted, or changed in-place."),
        ("What symbol begins a single-line comment in Python?", "#", ["//", "/*", "--"], "The '#' symbol begins comments in Python code."),
        ("Which method removes and returns the last element of a Python list?", "pop()", ["remove()", "delete()", "shift()"], "list.pop() removes and returns the item at index -1 by default."),
        ("What does OOP stand for in software engineering?", "Object-Oriented Programming", ["Operational Order Paradigm", "Output Oriented Protocol", "Open Object Platform"], "OOP models software around data entities and classes."),
        ("Which built-in Python function returns the count of items in a collection?", "len()", ["count()", "size()", "length()"], "len() returns the length/size of any sequence or mapping."),
        ("What is the floor division operator in Python?", "//", ["/", "%", "**"], "Double slash (//) computes integer floor division."),
        ("What exception is raised when looking up a nonexistent key in a dict?", "KeyError", ["IndexError", "ValueError", "LookupFailure"], "Accessing dict[missing_key] raises a KeyError exception.")
    ]
    sampled = random.sample(pool, min(count, len(pool)))
    out = []
    for q, a, w, exp in sampled:
        opts = [a] + w
        random.shuffle(opts)
        out.append({"question": q, "options": opts, "answer": a, "explanation": exp})
    return out

def gen_history_questions(count, difficulty):
    pool = [
        ("In which year did World War II formally conclude?", "1945", ["1939", "1942", "1950"], "World War II ended in 1945 with the unconditional surrender of the Axis powers."),
        ("Who served as the very first President of the United States?", "George Washington", ["Thomas Jefferson", "Abraham Lincoln", "John Adams"], "Washington served as president from 1789 until 1797."),
        ("The historic storming of the Bastille in 1789 occurred in which country?", "France", ["Great Britain", "Austria", "Russia"], "The Bastille was stormed in Paris at the start of the French Revolution."),
        ("In which year did the Apollo 11 mission first land humans on the Moon?", "1969", ["1965", "1972", "1959"], "Neil Armstrong and Buzz Aldrin walked on the Moon on July 20, 1969."),
        ("The ancient city-states of Athens and Sparta fought in which conflict?", "Peloponnesian War", ["Punic Wars", "Trojan War", "Persian War"], "The Peloponnesian War (431–404 BC) reshaped ancient Greece."),
        ("The fall of the Berlin Wall occurred in which landmark year?", "1989", ["1979", "1991", "1985"], "The Berlin Wall fell on November 9, 1989, paving the way for German reunification.")
    ]
    sampled = random.sample(pool, min(count, len(pool)))
    out = []
    for q, a, w, exp in sampled:
        opts = [a] + w
        random.shuffle(opts)
        out.append({"question": q, "options": opts, "answer": a, "explanation": exp})
    return out

def gen_geo_questions(count, difficulty):
    pool = [
        ("Which is the largest ocean on planet Earth by surface area?", "Pacific Ocean", ["Atlantic Ocean", "Indian Ocean", "Arctic Ocean"], "The Pacific Ocean covers over 30% of the entire Earth's surface."),
        ("Which is widely recognized as the longest river in the world?", "Nile River", ["Amazon River", "Yangtze River", "Mississippi River"], "The Nile flows for approximately 6,650 kilometers across northeastern Africa."),
        ("Which continent is the smallest by total land area?", "Australia", ["Europe", "Antarctica", "South America"], "Australia is the smallest geographical continent on Earth."),
        ("Which is the largest hot desert on Earth?", "Sahara Desert", ["Gobi Desert", "Kalahari Desert", "Arabian Desert"], "The Sahara spans roughly 9.2 million square kilometers across North Africa."),
        ("Mount Everest is situated in which majestic mountain range?", "Himalayas", ["Andes", "Alps", "Rocky Mountains"], "Mount Everest stands at 8,848.86m within the Mahalangur Himal sub-range.")
    ]
    sampled = random.sample(pool, min(count, len(pool)))
    out = []
    for q, a, w, exp in sampled:
        opts = [a] + w
        random.shuffle(opts)
        out.append({"question": q, "options": opts, "answer": a, "explanation": exp})
    return out

def get_procedural_questions(category, difficulty="Medium", count=10):
    generators = {
        "General Knowledge": gen_gk_questions,
        "Mathematics":       gen_math_questions,
        "Science":           gen_science_questions,
        "Computer Science":  gen_cs_questions,
        "Programming":       gen_prog_questions,
        "History":           gen_history_questions,
        "Geography":         gen_geo_questions,
    }
    gen = generators.get(category, gen_gk_questions)
    questions = gen(count, difficulty)
    for q in questions:
        random.shuffle(q["options"])
    return questions


# ================================================================
#  GOOGLE GEMINI AI INTEGRATION (REST & SDK)
# ================================================================

def sanitize_api_key(key):
    k = key.strip()
    if k.startswith(("'", '"')) and k.endswith(("'", '"')):
        k = k[1:-1].strip()
    if k.lower().startswith("bearer "):
        k = k[7:].strip()
    if k.startswith("API_KEY="):
        k = k.split("=", 1)[1].strip()
    return k


class GeminiClient:
    """Seamlessly talks to Google Gemini via REST or Generative AI SDK."""
    def __init__(self, api_key=""):
        self.api_key = sanitize_api_key(api_key)
        self.active_model_name = "gemini-1.5-flash"
        self.sdk_ready = False
        self._init_sdk()

    def update_key(self, api_key):
        self.api_key = sanitize_api_key(api_key)
        self._init_sdk()

    def _init_sdk(self):
        if self.api_key and GEMINI_SDK_AVAILABLE:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel("gemini-1.5-flash")
                self.sdk_ready = True
            except Exception:
                self.sdk_ready = False

    def is_configured(self):
        return bool(self.api_key)

    def test_connection(self):
        clean_key = sanitize_api_key(self.api_key)
        if not clean_key:
            return False, "API key cannot be empty."
        self.api_key = clean_key
        ctx = get_ssl_context()
        kwargs = {"context": ctx} if ctx is not None else {}

        # 1. Verify key validity and discover available models via canonical endpoint
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={clean_key}"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=10, **kwargs) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    models = [m.get("name", "").replace("models/", "") for m in data.get("models", [])]
                    for candidate in ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.0-pro"]:
                        if candidate in models:
                            self.active_model_name = candidate
                            break
                    else:
                        self.active_model_name = models[0] if models else "gemini-1.5-flash"
                    return True, f"Connected to Google AI! Active Model: {self.active_model_name}"
        except urllib.error.HTTPError as e:
            try:
                body = json.loads(e.read().decode("utf-8"))
                msg = body.get("error", {}).get("message", "")
                if msg:
                    return False, f"Google AI error ({e.code}): {msg}"
            except Exception:
                pass
            if e.code == 400:
                return False, "Invalid API key. Please check your key from Google AI Studio."
            elif e.code == 403:
                return False, "Permission denied (403). Ensure Generative Language API is enabled."
            elif e.code == 404:
                return False, "Endpoint not found (404). Verify that your key is from Google AI Studio (ai.google.dev)."
            elif e.code == 429:
                return False, "Rate limit / Quota exceeded (429). Please wait a few moments."
            return False, f"HTTP Error {e.code}: Check your API key or quota."
        except Exception as e:
            return False, f"Connection error: {str(e)[:60]}"
        return False, "Failed to connect to Google AI endpoint."

    def generate_questions(self, category, difficulty="Medium", count=10, timeout=15):
        if not self.api_key:
            raise RuntimeError("Gemini API key not configured")
        
        prompt = f"""You are an elite quiz question generator. Generate exactly {count} multiple-choice questions for the category "{category}" at "{difficulty}" difficulty.
Rules:
- Exactly 4 distinct options per question.
- Exactly 1 option must be the correct answer.
- Provide a brief 1-sentence educational explanation.
- Return ONLY valid raw JSON array of objects without markdown formatting:
[
  {{
    "question": "Question text here?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "answer": "Exact matching option text",
    "explanation": "Why this answer is correct."
  }}
]"""

        raw_text = ""
        if self.sdk_ready:
            try:
                response = self.model.generate_content(prompt)
                raw_text = response.text.strip()
            except Exception:
                raw_text = ""

        if not raw_text:
            active_model = getattr(self, "active_model_name", "gemini-1.5-flash")
            candidates = [active_model, "gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]
            seen = set()
            model_list = [x for x in candidates if not (x in seen or seen.add(x))]

            ctx = get_ssl_context()
            kwargs = {"context": ctx} if ctx is not None else {}
            last_err = None

            for m_name in model_list:
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{m_name}:generateContent?key={self.api_key}"
                    payload = json.dumps({
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"temperature": 0.7, "responseMimeType": "application/json"}
                    }).encode("utf-8")
                    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
                    with urllib.request.urlopen(req, timeout=timeout, **kwargs) as resp:
                        data = json.loads(resp.read().decode("utf-8"))
                        raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    if raw_text:
                        self.active_model_name = m_name
                        break
                except Exception as e:
                    last_err = e
                    continue
            
            if not raw_text and last_err:
                raise last_err

        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[1]
            if raw_text.endswith("```"):
                raw_text = raw_text.rsplit("```", 1)[0]

        parsed = json.loads(raw_text)
        validated = []
        for q in parsed:
            if all(k in q for k in ("question", "options", "answer")):
                if len(q["options"]) == 4 and q["answer"] in q["options"]:
                    validated.append(q)
        if len(validated) < 3:
            raise ValueError("Too few valid questions returned from AI")
        return validated[:count]


# ================================================================
#  CUSTOM HIGH-DEFINITION CIRCULAR GAUGE WIDGET
# ================================================================

class HDCircularGauge(ctk.CTkFrame):
    """Modern smooth circular gauge for accuracy & results display."""
    def __init__(self, parent, percentage=0, size=180, thickness=14, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.size = size
        self.thickness = thickness
        self.percentage = max(0.0, min(100.0, float(percentage)))
        
        self.canvas = tk.Canvas(
            self, width=size, height=size,
            bg=self._detect_bg(), highlightthickness=0
        )
        self.canvas.pack()
        self.draw_gauge()

    def _detect_bg(self):
        mode = ctk.get_appearance_mode()
        return "#141D2F" if mode == "Dark" else "#FFFFFF"

    def set_percentage(self, percentage):
        self.percentage = max(0.0, min(100.0, float(percentage)))
        self.draw_gauge()

    def draw_gauge(self):
        self.canvas.delete("all")
        pad = self.thickness + 4
        s = self.size
        
        # Color based on percentage
        if self.percentage >= 80:
            arc_color = "#10B981"  # Emerald
            grade = "A+" if self.percentage == 100 else "A"
        elif self.percentage >= 60:
            arc_color = "#6366F1"  # Indigo
            grade = "B"
        elif self.percentage >= 40:
            arc_color = "#F59E0B"  # Amber
            grade = "C"
        else:
            arc_color = "#EF4444"  # Crimson
            grade = "D"

        mode = ctk.get_appearance_mode()
        track_color = "#24324D" if mode == "Dark" else "#E2E8F0"
        text_color = "#F8FAFC" if mode == "Dark" else "#0F172A"
        sub_color = "#94A3B8" if mode == "Dark" else "#64748B"

        # Background track circle
        self.canvas.create_arc(
            pad, pad, s - pad, s - pad,
            start=90, extent=-360,
            outline=track_color, width=self.thickness, style="arc"
        )
        
        # Active progress arc
        extent = -3.6 * self.percentage
        if abs(extent) > 0:
            self.canvas.create_arc(
                pad, pad, s - pad, s - pad,
                start=90, extent=extent,
                outline=arc_color, width=self.thickness, style="arc"
            )

        # Center Text - Percentage
        self.canvas.create_text(
            s // 2, (s // 2) - 10,
            text=f"{self.percentage:.0f}%",
            fill=text_color, font=("Helvetica Neue", 28, "bold")
        )
        
        # Center Subtext - Grade badge
        self.canvas.create_text(
            s // 2, (s // 2) + 22,
            text=f"RANK {grade}",
            fill=arc_color, font=("Helvetica Neue", 12, "bold")
        )


# ================================================================
#  MAIN APPLICATION ARCHITECTURE
# ================================================================

class QuizMasterProApp(ctk.CTk):
    """Ultra-modern, multi-screen adaptive quiz application."""
    def __init__(self):
        super().__init__()

        # Database and Storage
        self.db = DatabaseManager()
        
        # Persistent state
        self.student_name = self.db.get_setting("student_name", "Explorer")
        saved_theme = self.db.get_setting("theme", "Dark")
        self.current_theme = saved_theme
        ctk.set_appearance_mode(self.current_theme)
        
        # Saved preferences
        self.timer_seconds = int(self.db.get_setting("timer_seconds", 15))
        self.questions_per_quiz = int(self.db.get_setting("questions_per_quiz", 10))
        self.selected_difficulty = self.db.get_setting("selected_difficulty", "Medium")
        
        # Gemini Client
        saved_key = self.db.get_setting("gemini_api_key", "")
        self.gemini = GeminiClient(saved_key)

        # Active Session Variables
        self.selected_category = "General Knowledge"
        self.quiz_questions = []
        self.current_q_idx = 0
        self.score = 0
        self.correct_count = 0
        self.wrong_count = 0
        self.streak = 0
        self.max_streak = 0
        self.total_points = 0
        self.user_answers = []
        self.time_left = self.timer_seconds
        self.timer_after_id = None
        self.answering_locked = False
        self.lifeline_5050_used = False
        self.session_start_time = 0
        self.result_saved_flag = False

        # Window Setup
        self.title(f"{APP_TITLE} {APP_VERSION}")
        self.geometry("1240x820")
        self.minsize(1050, 720)
        self.configure(fg_color=PALETTE["bg_main"])
        
        # Intercept close
        self.protocol("WM_DELETE_WINDOW", self.on_exit)

        # Build Global Frame Architecture
        self._build_top_navbar()
        
        # Main dynamic content container
        self.content_area = ctk.CTkFrame(self, fg_color="transparent")
        self.content_area.pack(fill="both", expand=True, padx=25, pady=(10, 20))

        # Launch default Hub View
        self.show_hub_view()

    # ── Top Navigation Bar ──────────────────────────────────────
    def _build_top_navbar(self):
        """Constructs an elegant, modern top application bar."""
        self.nav_bar = ctk.CTkFrame(
            self, height=65, corner_radius=0,
            fg_color=PALETTE["header_bg"],
            border_width=1, border_color=PALETTE["card_border"]
        )
        self.nav_bar.pack(fill="x", side="top")
        self.nav_bar.pack_propagate(False)

        # Left: Brand Logo & Version
        brand_frame = ctk.CTkFrame(self.nav_bar, fg_color="transparent")
        brand_frame.pack(side="left", padx=(16, 8), pady=10)
        
        logo_icon = ctk.CTkLabel(brand_frame, text="🧠", font=("Helvetica Neue", 24))
        logo_icon.pack(side="left", padx=(0, 6))
        
        title_lbl = ctk.CTkLabel(
            brand_frame, text="QUIZ MASTER",
            font=("Helvetica Neue", 17, "bold"),
            text_color=PALETTE["text_primary"]
        )
        title_lbl.pack(side="left")
        
        pro_badge = ctk.CTkFrame(brand_frame, fg_color=PALETTE["primary"], corner_radius=6)
        pro_badge.pack(side="left", padx=6)
        pro_lbl = ctk.CTkLabel(pro_badge, text="PRO ULTRA", font=("Helvetica Neue", 10, "bold"), text_color="#FFFFFF")
        pro_lbl.pack(padx=5, pady=2)

        # Right: Player Chip & Theme Toggle (PACKED FIRST so it never gets clipped)
        right_frame = ctk.CTkFrame(self.nav_bar, fg_color="transparent")
        right_frame.pack(side="right", padx=(6, 16), pady=10)

        # Theme toggle button
        theme_icon = "☀️" if self.current_theme == "Light" else "🌙"
        self.theme_btn = ctk.CTkButton(
            right_frame, text=theme_icon,
            command=self.toggle_theme,
            width=34, height=34, corner_radius=17,
            font=("Helvetica Neue", 15),
            fg_color=PALETTE["card_bg_alt"],
            hover_color=PALETTE["card_hover"]
        )
        self.theme_btn.pack(side="right")

        # Player profile chip
        self.player_chip = ctk.CTkButton(
            right_frame,
            text=f"👤 {self.student_name}",
            command=self._prompt_name_change,
            width=110, height=34, corner_radius=17,
            font=("Helvetica Neue", 11, "bold"),
            fg_color=PALETTE["card_bg_alt"],
            hover_color=PALETTE["card_hover"],
            text_color=PALETTE["text_primary"]
        )
        self.player_chip.pack(side="right", padx=(0, 8))

        # Center: Navigation Action Pills (fill remaining space)
        self.nav_buttons_frame = ctk.CTkFrame(self.nav_bar, fg_color="transparent")
        self.nav_buttons_frame.pack(side="left", fill="x", expand=True, pady=10)

        nav_items = [
            ("🏠 Hub", self.show_hub_view),
            ("📚 Categories", self.show_category_view),
            ("📊 Analytics", self.show_analytics_view),
            ("🏆 Badges", self.show_achievements_view),
            ("📜 History", self.show_history_view),
            ("🤖 AI Setup", self.show_ai_setup_view),
            ("⚙️ Settings", self.show_settings_view),
        ]
        
        self.nav_btns = {}
        for text, cmd in nav_items:
            btn = ctk.CTkButton(
                self.nav_buttons_frame, text=text,
                command=cmd, width=88, height=34,
                corner_radius=10,
                font=("Helvetica Neue", 11, "bold"),
                fg_color="transparent",
                hover_color=PALETTE["card_bg_alt"],
                text_color=PALETTE["text_secondary"]
            )
            btn.pack(side="left", padx=2)
            self.nav_btns[text] = btn

    def _clear_content(self):
        """Cleans current view and resets timer safely."""
        self._stop_timer()
        for widget in self.content_area.winfo_children():
            widget.destroy()

    def _highlight_nav(self, active_title):
        for name, btn in self.nav_btns.items():
            if active_title in name:
                btn.configure(fg_color=PALETTE["primary"], text_color="#FFFFFF")
            else:
                btn.configure(fg_color="transparent", text_color=PALETTE["text_secondary"])

    def toggle_theme(self):
        new_theme = "Light" if self.current_theme == "Dark" else "Dark"
        self.current_theme = new_theme
        ctk.set_appearance_mode(new_theme)
        self.theme_btn.configure(text="☀️" if new_theme == "Light" else "🌙")
        self.db.set_setting("theme", new_theme)

    def _prompt_name_change(self):
        dialog = ctk.CTkInputDialog(text="Enter your student or player name:", title="Player Profile")
        new_name = dialog.get_input()
        if new_name and new_name.strip():
            self.student_name = new_name.strip()
            self.db.set_setting("student_name", self.student_name)
            self.player_chip.configure(text=f"👤 {self.student_name}")
            self.show_hub_view()

    # ============================================================
    #  VIEW 1: HUB / HOME DASHBOARD
    # ============================================================
    def show_hub_view(self):
        self._clear_content()
        self._highlight_nav("Hub")

        # Scrollable container for fluid responsiveness
        scroll = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # ── Hero Banner Card ──
        hero_card = ctk.CTkFrame(
            scroll, corner_radius=20,
            fg_color=PALETTE["card_bg"],
            border_width=1, border_color=PALETTE["card_border"]
        )
        hero_card.pack(fill="x", pady=(5, 18), ipady=12)

        hero_content = ctk.CTkFrame(hero_card, fg_color="transparent")
        hero_content.pack(fill="x", padx=30, pady=16)

        left_hero = ctk.CTkFrame(hero_content, fg_color="transparent")
        left_hero.pack(side="left", fill="both", expand=True)

        stats = self.db.get_user_stats(self.student_name)
        greeting = f"Welcome back, {self.student_name}! 🚀" if stats["total_quizzes"] > 0 else f"Welcome to Quiz Master Pro, {self.student_name}!"
        
        ctk.CTkLabel(
            left_hero, text=greeting,
            font=("Helvetica Neue", 26, "bold"),
            text_color=PALETTE["text_primary"],
            anchor="w"
        ).pack(anchor="w")

        ctk.CTkLabel(
            left_hero, text="Test your knowledge across diverse subjects with real-time feedback & AI adaptation.",
            font=("Helvetica Neue", 13),
            text_color=PALETTE["text_secondary"],
            anchor="w"
        ).pack(anchor="w", pady=(4, 16))

        # Quick stats chips
        stats_ribbon = ctk.CTkFrame(left_hero, fg_color="transparent")
        stats_ribbon.pack(anchor="w")

        chips = [
            ("🎯 Quizzes", f"{stats['total_quizzes']}"),
            ("📈 Avg Accuracy", f"{stats['avg_pct']:.0f}%"),
            ("🏆 Best Score", f"{stats['best_pct']:.0f}%"),
            ("🔥 Max Streak", f"{stats['max_streak']}"),
        ]
        for label, val in chips:
            chip = ctk.CTkFrame(stats_ribbon, fg_color=PALETTE["card_bg_alt"], corner_radius=10)
            chip.pack(side="left", padx=(0, 10))
            ctk.CTkLabel(chip, text=f"{label}: ", font=("Helvetica Neue", 11, "bold"), text_color=PALETTE["text_secondary"]).pack(side="left", padx=(10, 2), pady=6)
            ctk.CTkLabel(chip, text=val, font=("Helvetica Neue", 11, "bold"), text_color=PALETTE["primary"]).pack(side="left", padx=(0, 10), pady=6)

        # Right Hero Action: Quick start
        right_hero = ctk.CTkFrame(hero_content, fg_color="transparent")
        right_hero.pack(side="right", padx=10)

        quick_play_btn = ctk.CTkButton(
            right_hero, text="⚡ Quick Challenge",
            command=lambda: self.start_quiz_session(random.choice(CATEGORIES_DATA)["id"]),
            width=180, height=48, corner_radius=14,
            font=("Helvetica Neue", 14, "bold"),
            fg_color=PALETTE["primary"], hover_color=PALETTE["primary_hover"]
        )
        quick_play_btn.pack()

        # ── Category Grid Header ──
        sec_header = ctk.CTkFrame(scroll, fg_color="transparent")
        sec_header.pack(fill="x", pady=(5, 10))
        
        ctk.CTkLabel(
            sec_header, text="Explore Quiz Categories",
            font=("Helvetica Neue", 18, "bold"),
            text_color=PALETTE["text_primary"]
        ).pack(side="left")

        ai_badge_text = "🟢 Gemini AI Active" if self.gemini.is_configured() else "⚡ Procedural Engine"
        ai_badge_color = PALETTE["success"] if self.gemini.is_configured() else PALETTE["accent_cyan"]
        ctk.CTkLabel(
            sec_header, text=ai_badge_text,
            font=("Helvetica Neue", 12, "bold"),
            text_color=ai_badge_color
        ).pack(side="right")

        # ── 7 Category Cards Grid ──
        grid_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        grid_frame.pack(fill="x", pady=5)
        grid_frame.columnconfigure((0, 1, 2), weight=1, uniform="col")

        for idx, cat in enumerate(CATEGORIES_DATA):
            row = idx // 3
            col = idx % 3

            card = ctk.CTkFrame(
                grid_frame, corner_radius=16,
                fg_color=PALETTE["card_bg"],
                border_width=1, border_color=PALETTE["card_border"]
            )
            card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

            card_inner = ctk.CTkFrame(card, fg_color="transparent")
            card_inner.pack(fill="both", expand=True, padx=18, pady=16)

            # Icon & Title Row
            top_row = ctk.CTkFrame(card_inner, fg_color="transparent")
            top_row.pack(fill="x", pady=(0, 6))

            icon_box = ctk.CTkFrame(top_row, width=44, height=44, corner_radius=12, fg_color=cat["color"])
            icon_box.pack(side="left")
            icon_box.pack_propagate(False)
            ctk.CTkLabel(icon_box, text=cat["icon"], font=("Helvetica Neue", 22)).place(relx=0.5, rely=0.5, anchor="center")

            title_box = ctk.CTkFrame(top_row, fg_color="transparent")
            title_box.pack(side="left", padx=12)
            ctk.CTkLabel(
                title_box, text=cat["name"],
                font=("Helvetica Neue", 15, "bold"),
                text_color=PALETTE["text_primary"], anchor="w"
            ).pack(anchor="w")
            ctk.CTkLabel(
                title_box, text=f"{self.questions_per_quiz} Questions",
                font=("Helvetica Neue", 11),
                text_color=PALETTE["text_muted"], anchor="w"
            ).pack(anchor="w")

            # Description
            ctk.CTkLabel(
                card_inner, text=cat["desc"],
                font=("Helvetica Neue", 12),
                text_color=PALETTE["text_secondary"],
                wraplength=280, justify="left", anchor="w"
            ).pack(anchor="w", pady=(4, 14))

            # Action button
            play_btn = ctk.CTkButton(
                card_inner, text="Launch Quiz →",
                command=lambda c=cat["id"]: self.start_quiz_session(c),
                corner_radius=10, height=36,
                font=("Helvetica Neue", 12, "bold"),
                fg_color=PALETTE["card_bg_alt"],
                hover_color=cat["color"],
                text_color=PALETTE["text_primary"]
            )
            play_btn.pack(fill="x")

    # ============================================================
    #  VIEW 2: CATEGORY & DIFFICULTY SELECTOR
    # ============================================================
    def show_category_view(self):
        self._clear_content()
        self._highlight_nav("Categories")

        scroll = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        header = ctk.CTkFrame(scroll, fg_color="transparent")
        header.pack(fill="x", pady=(5, 15))

        ctk.CTkLabel(
            header, text="Choose Your Quiz Parameters",
            font=("Helvetica Neue", 24, "bold"),
            text_color=PALETTE["text_primary"]
        ).pack(anchor="w")
        ctk.CTkLabel(
            header, text="Select topic, difficulty level, and session preferences.",
            font=("Helvetica Neue", 13),
            text_color=PALETTE["text_secondary"]
        ).pack(anchor="w", pady=(2, 0))

        # ── Controls Frame ──
        controls_card = ctk.CTkFrame(
            scroll, corner_radius=16,
            fg_color=PALETTE["card_bg"],
            border_width=1, border_color=PALETTE["card_border"]
        )
        controls_card.pack(fill="x", pady=(0, 20), ipady=10)
        c_inner = ctk.CTkFrame(controls_card, fg_color="transparent")
        c_inner.pack(fill="x", padx=24, pady=16)

        # Difficulty Selector
        ctk.CTkLabel(c_inner, text="Select Difficulty:", font=("Helvetica Neue", 13, "bold"), text_color=PALETTE["text_primary"]).pack(anchor="w", pady=(0, 6))
        
        diff_frame = ctk.CTkFrame(c_inner, fg_color="transparent")
        diff_frame.pack(anchor="w", pady=(0, 16))

        self.diff_var = ctk.StringVar(value=self.selected_difficulty)
        diff_options = [
            ("🟢 Easy (1.0x)", "Easy"),
            ("🟡 Medium (1.5x)", "Medium"),
            ("🔴 Hard (2.0x)", "Hard"),
        ]
        for label, val in diff_options:
            rb = ctk.CTkRadioButton(
                diff_frame, text=label, value=val,
                variable=self.diff_var,
                command=lambda: self._update_diff(self.diff_var.get()),
                font=("Helvetica Neue", 13, "bold"),
                fg_color=PALETTE["primary"],
                hover_color=PALETTE["primary_hover"]
            )
            rb.pack(side="left", padx=(0, 20))

        # Question count and timer
        row_params = ctk.CTkFrame(c_inner, fg_color="transparent")
        row_params.pack(fill="x")

        # Questions per quiz
        q_box = ctk.CTkFrame(row_params, fg_color="transparent")
        q_box.pack(side="left", padx=(0, 40))
        ctk.CTkLabel(q_box, text="Questions Count:", font=("Helvetica Neue", 12, "bold"), text_color=PALETTE["text_secondary"]).pack(anchor="w", pady=(0, 4))
        
        q_seg = ctk.CTkSegmentedButton(
            q_box, values=["5", "10", "15", "20"],
            command=self._on_q_count_change,
            selected_color=PALETTE["primary"]
        )
        q_seg.set(str(self.questions_per_quiz))
        q_seg.pack()

        # Timer duration
        t_box = ctk.CTkFrame(row_params, fg_color="transparent")
        t_box.pack(side="left")
        ctk.CTkLabel(t_box, text="Time Per Question:", font=("Helvetica Neue", 12, "bold"), text_color=PALETTE["text_secondary"]).pack(anchor="w", pady=(0, 4))
        
        t_seg = ctk.CTkSegmentedButton(
            t_box, values=["10s", "15s", "20s", "30s"],
            command=self._on_timer_change,
            selected_color=PALETTE["primary"]
        )
        t_seg.set(f"{self.timer_seconds}s")
        t_seg.pack()

        # ── Category Grid ──
        grid = ctk.CTkFrame(scroll, fg_color="transparent")
        grid.pack(fill="x")
        grid.columnconfigure((0, 1), weight=1, uniform="cgrid")

        for idx, cat in enumerate(CATEGORIES_DATA):
            r = idx // 2
            c = idx % 2

            card = ctk.CTkFrame(
                grid, corner_radius=16,
                fg_color=PALETTE["card_bg"],
                border_width=1, border_color=PALETTE["card_border"]
            )
            card.grid(row=r, column=c, padx=8, pady=8, sticky="nsew")

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=20, pady=16)

            left = ctk.CTkFrame(inner, fg_color="transparent")
            left.pack(side="left", fill="both", expand=True)

            ctk.CTkLabel(left, text=f"{cat['icon']}  {cat['name']}", font=("Helvetica Neue", 16, "bold"), text_color=PALETTE["text_primary"], anchor="w").pack(anchor="w")
            ctk.CTkLabel(left, text=cat["desc"], font=("Helvetica Neue", 12), text_color=PALETTE["text_secondary"], anchor="w", wraplength=340).pack(anchor="w", pady=(4, 0))

            btn = ctk.CTkButton(
                inner, text="Start Quiz",
                command=lambda cat_id=cat["id"]: self.start_quiz_session(cat_id),
                width=110, height=38, corner_radius=10,
                font=("Helvetica Neue", 12, "bold"),
                fg_color=cat["color"], hover_color=cat["hover"]
            )
            btn.pack(side="right", padx=(10, 0))

    def _update_diff(self, val):
        self.selected_difficulty = val
        self.db.set_setting("selected_difficulty", val)

    def _on_q_count_change(self, val):
        self.questions_per_quiz = int(val)
        self.db.set_setting("questions_per_quiz", self.questions_per_quiz)

    def _on_timer_change(self, val):
        self.timer_seconds = int(val.replace("s", ""))
        self.db.set_setting("timer_seconds", self.timer_seconds)

    # ============================================================
    #  VIEW 3: QUIZ SESSION & LOADING
    # ============================================================
    def start_quiz_session(self, category_id):
        self.selected_category = category_id
        self.current_q_idx = 0
        self.score = 0
        self.correct_count = 0
        self.wrong_count = 0
        self.streak = 0
        self.max_streak = 0
        self.total_points = 0
        self.user_answers = []
        self.lifeline_5050_used = False
        self.result_saved_flag = False
        self.session_start_time = time.time()

        self._show_loading_screen(category_id)

    def _show_loading_screen(self, category_id):
        self._clear_content()

        container = ctk.CTkFrame(
            self.content_area, corner_radius=20,
            fg_color=PALETTE["card_bg"],
            border_width=1, border_color=PALETTE["card_border"]
        )
        container.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.6, relheight=0.55)

        inner = ctk.CTkFrame(container, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(inner, text="🧠", font=("Helvetica Neue", 64)).pack(pady=(0, 10))
        
        status_lbl = ctk.CTkLabel(
            inner, text="Preparing Quiz Questions...",
            font=("Helvetica Neue", 22, "bold"),
            text_color=PALETTE["text_primary"]
        )
        status_lbl.pack(pady=4)

        source_text = "🤖 Generating fresh questions with Google Gemini AI..." if self.gemini.is_configured() else "⚡ Synthesizing questions with Smart Procedural Engine..."
        ctk.CTkLabel(
            inner, text=source_text,
            font=("Helvetica Neue", 13),
            text_color=PALETTE["text_secondary"]
        ).pack(pady=(0, 15))

        prog_bar = ctk.CTkProgressBar(inner, width=320, height=8, corner_radius=4, progress_color=PALETTE["primary"])
        prog_bar.pack(pady=10)
        prog_bar.configure(mode="indeterminate")
        prog_bar.start()

        def fetch_worker():
            questions = []
            if self.gemini.is_configured():
                try:
                    questions = self.gemini.generate_questions(
                        category=category_id,
                        difficulty=self.selected_difficulty,
                        count=self.questions_per_quiz
                    )
                except Exception as e:
                    print(f"Gemini fallback triggered: {e}")
                    questions = get_procedural_questions(category_id, self.selected_difficulty, self.questions_per_quiz)
            else:
                time.sleep(0.5)  # Smooth transition effect
                questions = get_procedural_questions(category_id, self.selected_difficulty, self.questions_per_quiz)

            self.after(0, lambda: self._on_questions_loaded(questions))

        threading.Thread(target=fetch_worker, daemon=True).start()

    def _on_questions_loaded(self, questions):
        self.quiz_questions = questions
        random.shuffle(self.quiz_questions)
        self.show_question_view()

    # ============================================================
    #  VIEW 4: INTERACTIVE QUESTION HUD & CARD
    # ============================================================
    def show_question_view(self):
        self._clear_content()
        self.answering_locked = False

        if self.current_q_idx >= len(self.quiz_questions):
            self.show_results_view()
            return

        q_data = self.quiz_questions[self.current_q_idx]
        total_q = len(self.quiz_questions)
        q_num = self.current_q_idx + 1

        # ── Top HUD Strip ──
        hud = ctk.CTkFrame(
            self.content_area, corner_radius=16,
            fg_color=PALETTE["card_bg"],
            border_width=1, border_color=PALETTE["card_border"],
            height=60
        )
        hud.pack(fill="x", pady=(0, 12))
        hud.pack_propagate(False)

        hud_inner = ctk.CTkFrame(hud, fg_color="transparent")
        hud_inner.pack(fill="both", expand=True, padx=20)

        # Left: Category badge & Question count
        left_hud = ctk.CTkFrame(hud_inner, fg_color="transparent")
        left_hud.pack(side="left")

        cat_badge = ctk.CTkFrame(left_hud, fg_color=PALETTE["primary_light"], corner_radius=8)
        cat_badge.pack(side="left", padx=(0, 12))
        ctk.CTkLabel(
            cat_badge, text=f"{self.selected_category} • {self.selected_difficulty}",
            font=("Helvetica Neue", 11, "bold"), text_color=PALETTE["primary"]
        ).pack(padx=10, pady=4)

        ctk.CTkLabel(
            left_hud, text=f"Question {q_num} of {total_q}",
            font=("Helvetica Neue", 13, "bold"), text_color=PALETTE["text_primary"]
        ).pack(side="left")

        # Center: Streak & Multiplier
        center_hud = ctk.CTkFrame(hud_inner, fg_color="transparent")
        center_hud.pack(side="left", expand=True)

        if self.streak >= 2:
            streak_color = PALETTE["warning"] if self.streak < 5 else PALETTE["danger"]
            multiplier = 1.0 + (self.streak - 1) * 0.25
            flame_text = f"🔥 Streak: {self.streak}  ({multiplier:.2f}x Points)"
            flame_chip = ctk.CTkFrame(center_hud, fg_color=streak_color, corner_radius=8)
            flame_chip.pack()
            ctk.CTkLabel(
                flame_chip, text=flame_text,
                font=("Helvetica Neue", 11, "bold"), text_color="#FFFFFF"
            ).pack(padx=10, pady=3)

        # Right: Live Score & Timer
        right_hud = ctk.CTkFrame(hud_inner, fg_color="transparent")
        right_hud.pack(side="right")

        score_chip = ctk.CTkFrame(right_hud, fg_color=PALETTE["card_bg_alt"], corner_radius=8)
        score_chip.pack(side="left", padx=(0, 12))
        ctk.CTkLabel(
            score_chip, text=f"⭐ {self.total_points} pts",
            font=("Helvetica Neue", 12, "bold"), text_color=PALETTE["primary"]
        ).pack(padx=10, pady=4)

        self.timer_label = ctk.CTkLabel(
            right_hud, text=f"⏱ {self.timer_seconds}s",
            font=("Helvetica Neue", 14, "bold"),
            text_color=PALETTE["success"]
        )
        self.timer_label.pack(side="left")

        # ── Smooth Progress Bar ──
        prog_val = (self.current_q_idx) / total_q
        self.prog_bar = ctk.CTkProgressBar(
            self.content_area, height=6, corner_radius=3,
            progress_color=PALETTE["primary"], fg_color=PALETTE["card_border"]
        )
        self.prog_bar.pack(fill="x", pady=(0, 14))
        self.prog_bar.set(prog_val)

        # ── Main Question Card ──
        q_card = ctk.CTkFrame(
            self.content_area, corner_radius=20,
            fg_color=PALETTE["card_bg"],
            border_width=1, border_color=PALETTE["card_border"]
        )
        q_card.pack(fill="both", expand=True)

        card_inner = ctk.CTkFrame(q_card, fg_color="transparent")
        card_inner.pack(fill="both", expand=True, padx=40, pady=25)

        # Question prompt
        ctk.CTkLabel(
            card_inner, text=f"QUESTION #{q_num}",
            font=("Helvetica Neue", 12, "bold"),
            text_color=PALETTE["text_muted"]
        ).pack(anchor="w", pady=(0, 6))

        q_label = ctk.CTkLabel(
            card_inner, text=q_data["question"],
            font=("Helvetica Neue", 20, "bold"),
            text_color=PALETTE["text_primary"],
            wraplength=920, justify="left", anchor="w"
        )
        q_label.pack(fill="x", anchor="w", pady=(0, 20))

        # ── 4 Option Buttons Grid ──
        self.option_buttons = []
        options_frame = ctk.CTkFrame(card_inner, fg_color="transparent")
        options_frame.pack(fill="both", expand=True)
        options_frame.columnconfigure((0, 1), weight=1, uniform="opt")

        opt_letters = ["A", "B", "C", "D"]
        for i, option_text in enumerate(q_data["options"]):
            row = i // 2
            col = i % 2

            btn = ctk.CTkButton(
                options_frame,
                text=f"  {opt_letters[i]}.   {option_text}",
                command=lambda opt=option_text, idx=i: self._on_select_option(opt, idx),
                font=("Helvetica Neue", 14),
                height=56, corner_radius=14,
                fg_color=PALETTE["card_bg_alt"],
                hover_color=PALETTE["primary_hover"],
                text_color=PALETTE["text_primary"],
                anchor="w",
                border_width=1, border_color=PALETTE["card_border"]
            )
            btn.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
            self.option_buttons.append(btn)

        # ── Explanation / Feedback Banner (Hidden initially) ──
        self.feedback_banner = ctk.CTkFrame(card_inner, corner_radius=12, fg_color="transparent")
        self.feedback_banner.pack(fill="x", pady=(10, 0))

        # ── Bottom Action Toolbar ──
        toolbar = ctk.CTkFrame(card_inner, fg_color="transparent")
        toolbar.pack(fill="x", side="bottom", pady=(10, 0))

        # Lifeline: 50-50
        lifeline_state = "disabled" if self.lifeline_5050_used else "normal"
        lifeline_txt = "💡 50:50 Used" if self.lifeline_5050_used else "💡 50:50 Lifeline"
        self.lifeline_btn = ctk.CTkButton(
            toolbar, text=lifeline_txt,
            command=self._use_5050_lifeline,
            state=lifeline_state,
            width=130, height=36, corner_radius=10,
            font=("Helvetica Neue", 12, "bold"),
            fg_color=PALETTE["card_bg_alt"], hover_color=PALETTE["warning_hover"]
        )
        self.lifeline_btn.pack(side="left", padx=(0, 10))

        # Skip question
        skip_btn = ctk.CTkButton(
            toolbar, text="⏭ Skip",
            command=lambda: self._on_select_option("Skipped", -1),
            width=90, height=36, corner_radius=10,
            font=("Helvetica Neue", 12, "bold"),
            fg_color=PALETTE["card_bg_alt"], hover_color=PALETTE["card_hover"]
        )
        skip_btn.pack(side="left")

        # Next button (revealed after answer)
        self.next_btn = ctk.CTkButton(
            toolbar, text="Next Question →",
            command=self._advance_question,
            width=160, height=38, corner_radius=12,
            font=("Helvetica Neue", 13, "bold"),
            fg_color=PALETTE["primary"], hover_color=PALETTE["primary_hover"]
        )

        # Start countdown
        self.time_left = self.timer_seconds
        self._start_timer()

    # ── Quiz Mechanics ──────────────────────────────────────────
    def _use_5050_lifeline(self):
        """Eliminates two incorrect options from the current question."""
        if self.lifeline_5050_used or self.answering_locked:
            return
        self.lifeline_5050_used = True
        self.lifeline_btn.configure(state="disabled", text="💡 50:50 Used")

        correct_ans = self.quiz_questions[self.current_q_idx]["answer"]
        options = self.quiz_questions[self.current_q_idx]["options"]
        
        wrong_indices = [i for i, opt in enumerate(options) if opt != correct_ans]
        to_eliminate = random.sample(wrong_indices, min(2, len(wrong_indices)))
        
        for idx in to_eliminate:
            self.option_buttons[idx].configure(
                state="disabled",
                text="  —  [Eliminated]",
                fg_color=PALETTE["card_border"],
                text_color=PALETTE["text_muted"]
            )

    def _start_timer(self):
        self._stop_timer()

        def tick():
            if not hasattr(self, "timer_label") or not self.timer_label.winfo_exists():
                return
            self.timer_label.configure(text=f"⏱ {self.time_left}s")
            
            # Dynamic color alert
            if self.time_left <= 5:
                self.timer_label.configure(text_color=PALETTE["danger"])
            elif self.time_left <= 10:
                self.timer_label.configure(text_color=PALETTE["warning"])
            else:
                self.timer_label.configure(text_color=PALETTE["success"])

            if self.time_left <= 0:
                self._stop_timer()
                self._on_select_option("⏰ Time Expired", -1)
            else:
                self.time_left -= 1
                self.timer_after_id = self.after(1000, tick)

        tick()

    def _stop_timer(self):
        if self.timer_after_id is not None:
            try:
                self.after_cancel(self.timer_after_id)
            except Exception:
                pass
            self.timer_after_id = None

    def _on_select_option(self, selected_text, selected_idx):
        if self.answering_locked:
            return
        self.answering_locked = True
        self._stop_timer()

        q_data = self.quiz_questions[self.current_q_idx]
        correct_text = q_data["answer"]
        explanation = q_data.get("explanation", "")
        is_correct = (selected_text == correct_text)

        # Record answer
        self.user_answers.append({
            "question": q_data["question"],
            "selected": selected_text,
            "correct": correct_text,
            "is_correct": is_correct,
            "explanation": explanation,
            "time_remaining": self.time_left
        })

        # Calculate scoring & streak multiplier
        if is_correct:
            self.score += 1
            self.correct_count += 1
            self.streak += 1
            self.max_streak = max(self.max_streak, self.streak)
            
            multiplier = 1.0 + max(0, (self.streak - 1)) * 0.25
            diff_factor = 2.0 if self.selected_difficulty == "Hard" else 1.5 if self.selected_difficulty == "Medium" else 1.0
            time_bonus = self.time_left * 5
            points_earned = int((100 + time_bonus) * multiplier * diff_factor)
            self.total_points += points_earned
        else:
            self.wrong_count += 1
            self.streak = 0

        # Visual Feedback on Option Buttons
        for i, btn in enumerate(self.option_buttons):
            btn.configure(state="disabled")
            btn_opt = q_data["options"][i]
            
            if btn_opt == correct_text:
                btn.configure(fg_color=PALETTE["success"], text_color="#FFFFFF")
            elif i == selected_idx and not is_correct:
                btn.configure(fg_color=PALETTE["danger"], text_color="#FFFFFF")
            else:
                btn.configure(fg_color=PALETTE["card_border"], text_color=PALETTE["text_muted"])

        # Display Explanation Callout Banner
        banner_bg = PALETTE["success_light"] if is_correct else PALETTE["danger_light"]
        status_text = "✅ Correct! Well done!" if is_correct else f"❌ Incorrect. The right answer was: {correct_text}"
        status_color = PALETTE["success"] if is_correct else PALETTE["danger"]

        self.feedback_banner.configure(fg_color=banner_bg)
        for w in self.feedback_banner.winfo_children():
            w.destroy()

        ctk.CTkLabel(
            self.feedback_banner, text=status_text,
            font=("Helvetica Neue", 13, "bold"), text_color=status_color
        ).pack(anchor="w", padx=16, pady=(10, 2))

        if explanation:
            ctk.CTkLabel(
                self.feedback_banner, text=f"💡 {explanation}",
                font=("Helvetica Neue", 11), text_color=PALETTE["text_primary"],
                wraplength=880, justify="left"
            ).pack(anchor="w", padx=16, pady=(0, 10))

        # Show Next Question Button
        self.next_btn.pack(side="right")

    def _advance_question(self):
        self.current_q_idx += 1
        if self.current_q_idx >= len(self.quiz_questions):
            self.show_results_view()
        else:
            self.show_question_view()

    # ============================================================
    #  VIEW 5: RESULTS & VICTORY CELEBRATION
    # ============================================================
    def show_results_view(self):
        self._clear_content()

        total = len(self.quiz_questions)
        pct = (self.score / total * 100) if total else 0.0
        elapsed_sec = time.time() - self.session_start_time

        # Save to database once
        if not self.result_saved_flag:
            self.db.save_quiz_result(
                name=self.student_name,
                category=self.selected_category,
                difficulty=self.selected_difficulty,
                score=self.score,
                total=total,
                percentage=pct,
                streak_max=self.max_streak,
                time_taken=elapsed_sec
            )
            self.result_saved_flag = True

        scroll = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # ── Victory Hero Card ──
        v_card = ctk.CTkFrame(
            scroll, corner_radius=20,
            fg_color=PALETTE["card_bg"],
            border_width=1, border_color=PALETTE["card_border"]
        )
        v_card.pack(fill="x", pady=(5, 18), ipady=12)

        v_inner = ctk.CTkFrame(v_card, fg_color="transparent")
        v_inner.pack(fill="x", padx=40, pady=20)

        # Left: Smooth Circular Gauge
        gauge = HDCircularGauge(v_inner, percentage=pct, size=160, thickness=14)
        gauge.pack(side="left", padx=(0, 40))

        # Center/Right: Victory Summary Text
        sum_box = ctk.CTkFrame(v_inner, fg_color="transparent")
        sum_box.pack(side="left", fill="both", expand=True)

        if pct == 100:
            headline, color = "🌟 FLAWLESS VICTORY!", PALETTE["warning"]
            sub = "Spectacular mastery! You answered every single question correctly."
        elif pct >= 80:
            headline, color = "🏆 OUTSTANDING ACHIEVEMENT!", PALETTE["success"]
            sub = "Exceptional performance! You demonstrated deep knowledge."
        elif pct >= 60:
            headline, color = "👍 GREAT EFFORT!", PALETTE["primary"]
            sub = "Well played! You have a solid grasp of this topic."
        elif pct >= 40:
            headline, color = "📚 GOOD TRY!", PALETTE["warning"]
            sub = "Practice makes perfect! Review your answers to level up."
        else:
            headline, color = "💪 NEVER GIVE UP!", PALETTE["danger"]
            sub = "Every quiz is a stepping stone. Try again to boost your score!"

        ctk.CTkLabel(sum_box, text=headline, font=("Helvetica Neue", 24, "bold"), text_color=color).pack(anchor="w")
        ctk.CTkLabel(sum_box, text=sub, font=("Helvetica Neue", 13), text_color=PALETTE["text_secondary"]).pack(anchor="w", pady=(4, 14))

        # Metrics grid
        m_grid = ctk.CTkFrame(sum_box, fg_color="transparent")
        m_grid.pack(anchor="w")

        metrics = [
            ("⭐ Points", f"{self.total_points}"),
            ("🎯 Accuracy", f"{self.score}/{total} ({pct:.0f}%)"),
            ("🔥 Max Streak", f"{self.max_streak}"),
            ("⏱ Duration", f"{elapsed_sec:.0f}s"),
        ]
        for lbl, val in metrics:
            f = ctk.CTkFrame(m_grid, fg_color=PALETTE["card_bg_alt"], corner_radius=10)
            f.pack(side="left", padx=(0, 10))
            ctk.CTkLabel(f, text=f"{lbl}: ", font=("Helvetica Neue", 11, "bold"), text_color=PALETTE["text_secondary"]).pack(side="left", padx=(10, 2), pady=6)
            ctk.CTkLabel(f, text=val, font=("Helvetica Neue", 11, "bold"), text_color=PALETTE["text_primary"]).pack(side="left", padx=(0, 10), pady=6)

        # ── Action Buttons Ribbon ──
        actions_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        actions_frame.pack(fill="x", pady=10)

        ctk.CTkButton(
            actions_frame, text="📝 Review Answers",
            command=self.show_review_view,
            width=170, height=44, corner_radius=12,
            font=("Helvetica Neue", 13, "bold"),
            fg_color=PALETTE["primary"], hover_color=PALETTE["primary_hover"]
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            actions_frame, text="🔄 Play Again",
            command=lambda: self.start_quiz_session(self.selected_category),
            width=150, height=44, corner_radius=12,
            font=("Helvetica Neue", 13, "bold"),
            fg_color=PALETTE["success"], hover_color=PALETTE["success_hover"]
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            actions_frame, text="📚 New Category",
            command=self.show_category_view,
            width=160, height=44, corner_radius=12,
            font=("Helvetica Neue", 13, "bold"),
            fg_color=PALETTE["card_bg_alt"], hover_color=PALETTE["card_hover"],
            text_color=PALETTE["text_primary"]
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            actions_frame, text="🏠 Home Hub",
            command=self.show_hub_view,
            width=130, height=44, corner_radius=12,
            font=("Helvetica Neue", 13, "bold"),
            fg_color=PALETTE["card_bg_alt"], hover_color=PALETTE["card_hover"],
            text_color=PALETTE["text_primary"]
        ).pack(side="left")

    # ============================================================
    #  VIEW 6: ANSWER REVIEW
    # ============================================================
    def show_review_view(self):
        self._clear_content()

        scroll = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        header = ctk.CTkFrame(scroll, fg_color="transparent")
        header.pack(fill="x", pady=(5, 15))

        ctk.CTkLabel(
            header, text="Detailed Question Breakdown",
            font=("Helvetica Neue", 24, "bold"),
            text_color=PALETTE["text_primary"]
        ).pack(anchor="w")

        ctk.CTkLabel(
            header, text=f"Review your answers and explanations for {self.selected_category}.",
            font=("Helvetica Neue", 13),
            text_color=PALETTE["text_secondary"]
        ).pack(anchor="w", pady=(2, 0))

        for idx, item in enumerate(self.user_answers):
            is_corr = item["is_correct"]
            border_c = PALETTE["success"] if is_corr else PALETTE["danger"]

            card = ctk.CTkFrame(
                scroll, corner_radius=16,
                fg_color=PALETTE["card_bg"],
                border_width=1, border_color=border_c
            )
            card.pack(fill="x", pady=6)

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=22, pady=16)

            # Top: Question
            status_icon = "✅" if is_corr else "❌"
            ctk.CTkLabel(
                inner, text=f"{status_icon}  Question {idx+1}: {item['question']}",
                font=("Helvetica Neue", 14, "bold"),
                text_color=PALETTE["text_primary"],
                wraplength=960, justify="left", anchor="w"
            ).pack(anchor="w", pady=(0, 6))

            # User vs Correct
            ans_row = ctk.CTkFrame(inner, fg_color="transparent")
            ans_row.pack(fill="x", pady=(0, 6))

            your_color = PALETTE["success"] if is_corr else PALETTE["danger"]
            ctk.CTkLabel(ans_row, text=f"Your Answer: {item['selected']}", font=("Helvetica Neue", 12, "bold"), text_color=your_color).pack(side="left", padx=(0, 20))

            if not is_corr:
                ctk.CTkLabel(ans_row, text=f"Correct Answer: {item['correct']}", font=("Helvetica Neue", 12, "bold"), text_color=PALETTE["success"]).pack(side="left")

            # Explanation
            if item.get("explanation"):
                ctk.CTkLabel(
                    inner, text=f"💡 {item['explanation']}",
                    font=("Helvetica Neue", 11),
                    text_color=PALETTE["text_secondary"],
                    wraplength=960, justify="left", anchor="w"
                ).pack(anchor="w")

        # Back button
        back_btn = ctk.CTkButton(
            scroll, text="← Back to Results",
            command=self.show_results_view,
            width=160, height=42, corner_radius=12,
            font=("Helvetica Neue", 13, "bold"),
            fg_color=PALETTE["primary"], hover_color=PALETTE["primary_hover"]
        )
        back_btn.pack(anchor="w", pady=15)

    # ============================================================
    #  VIEW 7: ANALYTICS & STATISTICS
    # ============================================================
    def show_analytics_view(self):
        self._clear_content()
        self._highlight_nav("Analytics")

        scroll = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        header = ctk.CTkFrame(scroll, fg_color="transparent")
        header.pack(fill="x", pady=(5, 15))

        ctk.CTkLabel(
            header, text="Performance Analytics & Insights",
            font=("Helvetica Neue", 24, "bold"),
            text_color=PALETTE["text_primary"]
        ).pack(anchor="w")
        ctk.CTkLabel(
            header, text=f"Lifetime statistics and category proficiencies for {self.student_name}.",
            font=("Helvetica Neue", 13),
            text_color=PALETTE["text_secondary"]
        ).pack(anchor="w", pady=(2, 0))

        stats = self.db.get_user_stats(self.student_name)

        # ── KPI Cards Grid ──
        kpi_grid = ctk.CTkFrame(scroll, fg_color="transparent")
        kpi_grid.pack(fill="x", pady=(0, 20))
        kpi_grid.columnconfigure((0, 1, 2, 3), weight=1, uniform="kpi")

        kpi_items = [
            ("🎯", "Total Quizzes", f"{stats['total_quizzes']}", PALETTE["primary"]),
            ("📈", "Average Score", f"{stats['avg_pct']:.1f}%", PALETTE["success"]),
            ("🏆", "All-Time Best", f"{stats['best_pct']:.0f}%", PALETTE["warning"]),
            ("🔥", "Peak Streak", f"{stats['max_streak']}", PALETTE["danger"]),
        ]

        for i, (icon, title, val, color) in enumerate(kpi_items):
            card = ctk.CTkFrame(
                kpi_grid, corner_radius=16,
                fg_color=PALETTE["card_bg"],
                border_width=1, border_color=PALETTE["card_border"]
            )
            card.grid(row=0, column=i, padx=6, pady=6, sticky="nsew")

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=20, pady=18)

            ctk.CTkLabel(inner, text=icon, font=("Helvetica Neue", 28)).pack(anchor="w")
            ctk.CTkLabel(inner, text=title, font=("Helvetica Neue", 12), text_color=PALETTE["text_secondary"]).pack(anchor="w", pady=(6, 2))
            ctk.CTkLabel(inner, text=val, font=("Helvetica Neue", 24, "bold"), text_color=color).pack(anchor="w")

        # ── Category Breakdown Card ──
        breakdown_card = ctk.CTkFrame(
            scroll, corner_radius=16,
            fg_color=PALETTE["card_bg"],
            border_width=1, border_color=PALETTE["card_border"]
        )
        breakdown_card.pack(fill="x", pady=(0, 20))

        b_inner = ctk.CTkFrame(breakdown_card, fg_color="transparent")
        b_inner.pack(fill="both", expand=True, padx=24, pady=20)

        ctk.CTkLabel(
            b_inner, text="Category Proficiency Breakdown",
            font=("Helvetica Neue", 16, "bold"),
            text_color=PALETTE["text_primary"]
        ).pack(anchor="w", pady=(0, 14))

        cat_data = self.db.get_category_breakdown(self.student_name)
        if not cat_data:
            ctk.CTkLabel(
                b_inner, text="No quiz history yet. Take your first quiz to unlock detailed mastery insights!",
                font=("Helvetica Neue", 13), text_color=PALETTE["text_muted"]
            ).pack(anchor="w", pady=10)
        else:
            for cat_name, count, avg_score, max_score in cat_data:
                row = ctk.CTkFrame(b_inner, fg_color="transparent")
                row.pack(fill="x", pady=6)

                ctk.CTkLabel(
                    row, text=cat_name,
                    font=("Helvetica Neue", 13, "bold"),
                    text_color=PALETTE["text_primary"], width=180, anchor="w"
                ).pack(side="left")

                ctk.CTkLabel(
                    row, text=f"{count} quizzes",
                    font=("Helvetica Neue", 12),
                    text_color=PALETTE["text_muted"], width=90, anchor="w"
                ).pack(side="left")

                # Visual progress bar
                p = ctk.CTkProgressBar(row, height=8, corner_radius=4, progress_color=PALETTE["primary"], width=320)
                p.pack(side="left", padx=15)
                p.set(min(1.0, (avg_score or 0) / 100.0))

                ctk.CTkLabel(
                    row, text=f"{avg_score:.1f}% avg",
                    font=("Helvetica Neue", 12, "bold"),
                    text_color=PALETTE["text_primary"], width=90, anchor="w"
                ).pack(side="left")

    # ============================================================
    #  VIEW 8: ACHIEVEMENTS & BADGES
    # ============================================================
    def show_achievements_view(self):
        self._clear_content()
        self._highlight_nav("Badges")

        scroll = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        header = ctk.CTkFrame(scroll, fg_color="transparent")
        header.pack(fill="x", pady=(5, 15))

        ctk.CTkLabel(
            header, text="Achievements & Badges",
            font=("Helvetica Neue", 24, "bold"),
            text_color=PALETTE["text_primary"]
        ).pack(anchor="w")
        ctk.CTkLabel(
            header, text="Earn special badges as you conquer quizzes and expand your streak.",
            font=("Helvetica Neue", 13),
            text_color=PALETTE["text_secondary"]
        ).pack(anchor="w", pady=(2, 0))

        stats = self.db.get_user_stats(self.student_name)
        total_q = stats["total_quizzes"]
        best_pct = stats["best_pct"]
        best_streak = stats["max_streak"]

        all_badges = [
            ("🎯", "First Step", "Complete your first quiz session", total_q >= 1, PALETTE["success"]),
            ("🔥", "Knowledge Seeker", "Complete 5 quizzes", total_q >= 5, PALETTE["warning"]),
            ("🚀", "Quiz Master", "Complete 10 quizzes", total_q >= 10, PALETTE["primary"]),
            ("💎", "Grandmaster", "Complete 25 quizzes", total_q >= 25, PALETTE["accent_purple"]),
            ("⭐", "High Flyer", "Score 80% or higher in any quiz", best_pct >= 80, PALETTE["primary"]),
            ("🌟", "Flawless Victory", "Achieve a perfect 100% score", best_pct >= 100, PALETTE["warning"]),
            ("🔥", "Streak Starter", "Achieve a 3-question answer streak", best_streak >= 3, PALETTE["warning"]),
            ("⚡", "On Fire", "Achieve a 5-question answer streak", best_streak >= 5, PALETTE["danger"]),
            ("💥", "Unstoppable", "Achieve a 10-question answer streak", best_streak >= 10, PALETTE["accent_pink"]),
            ("🤖", "AI Pioneer", "Enable Google Gemini API question mode", self.gemini.is_configured(), PALETTE["accent_cyan"]),
        ]

        grid = ctk.CTkFrame(scroll, fg_color="transparent")
        grid.pack(fill="x")
        grid.columnconfigure((0, 1), weight=1, uniform="badge_col")

        for idx, (icon, title, desc, unlocked, color) in enumerate(all_badges):
            row = idx // 2
            col = idx % 2

            card_border = color if unlocked else PALETTE["card_border"]
            card = ctk.CTkFrame(
                grid, corner_radius=16,
                fg_color=PALETTE["card_bg"],
                border_width=1, border_color=card_border
            )
            card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=20, pady=16)

            left = ctk.CTkFrame(inner, fg_color="transparent")
            left.pack(side="left", fill="both", expand=True)

            title_row = ctk.CTkFrame(left, fg_color="transparent")
            title_row.pack(anchor="w")

            ctk.CTkLabel(title_row, text=icon, font=("Helvetica Neue", 22)).pack(side="left", padx=(0, 8))
            ctk.CTkLabel(
                title_row, text=title,
                font=("Helvetica Neue", 14, "bold"),
                text_color=PALETTE["text_primary"] if unlocked else PALETTE["text_muted"]
            ).pack(side="left")

            ctk.CTkLabel(
                left, text=desc,
                font=("Helvetica Neue", 12),
                text_color=PALETTE["text_secondary"]
            ).pack(anchor="w", pady=(4, 0))

            # Right badge status
            if unlocked:
                badge = ctk.CTkFrame(inner, fg_color=PALETTE["success_light"], corner_radius=8)
                badge.pack(side="right")
                ctk.CTkLabel(badge, text="✓ UNLOCKED", font=("Helvetica Neue", 10, "bold"), text_color=PALETTE["success"]).pack(padx=8, pady=4)
            else:
                badge = ctk.CTkFrame(inner, fg_color=PALETTE["card_bg_alt"], corner_radius=8)
                badge.pack(side="right")
                ctk.CTkLabel(badge, text="🔒 LOCKED", font=("Helvetica Neue", 10, "bold"), text_color=PALETTE["text_muted"]).pack(padx=8, pady=4)

    # ============================================================
    #  VIEW 9: HISTORY & RECORDS
    # ============================================================
    def show_history_view(self):
        self._clear_content()
        self._highlight_nav("History")

        scroll = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        header = ctk.CTkFrame(scroll, fg_color="transparent")
        header.pack(fill="x", pady=(5, 15))

        ctk.CTkLabel(
            header, text="Quiz History Records",
            font=("Helvetica Neue", 24, "bold"),
            text_color=PALETTE["text_primary"]
        ).pack(anchor="w")
        ctk.CTkLabel(
            header, text="Detailed chronological log of all completed quiz attempts.",
            font=("Helvetica Neue", 13),
            text_color=PALETTE["text_secondary"]
        ).pack(anchor="w", pady=(2, 0))

        records = self.db.get_recent_results(limit=40)
        if not records:
            ctk.CTkLabel(
                scroll, text="No quiz history recorded yet. Complete a quiz to view records here!",
                font=("Helvetica Neue", 14), text_color=PALETTE["text_muted"]
            ).pack(pady=40)
            return

        for r in records:
            # (id, name, category, difficulty, score, total, percentage, streak_max, time_taken, date)
            pct = r[6]
            pct_color = PALETTE["success"] if pct >= 80 else PALETTE["primary"] if pct >= 60 else PALETTE["warning"] if pct >= 40 else PALETTE["danger"]

            card = ctk.CTkFrame(
                scroll, corner_radius=14,
                fg_color=PALETTE["card_bg"],
                border_width=1, border_color=PALETTE["card_border"]
            )
            card.pack(fill="x", pady=5)

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=20, pady=12)

            left = ctk.CTkFrame(inner, fg_color="transparent")
            left.pack(side="left")

            ctk.CTkLabel(
                left, text=f"{r[2]}  •  {r[3]}",
                font=("Helvetica Neue", 13, "bold"),
                text_color=PALETTE["text_primary"]
            ).pack(anchor="w")
            
            ctk.CTkLabel(
                left, text=f"Player: {r[1]}   |   Date: {r[9]}",
                font=("Helvetica Neue", 11),
                text_color=PALETTE["text_muted"]
            ).pack(anchor="w", pady=(2, 0))

            right = ctk.CTkFrame(inner, fg_color="transparent")
            right.pack(side="right")

            score_badge = ctk.CTkFrame(right, fg_color=PALETTE["card_bg_alt"], corner_radius=8)
            score_badge.pack(side="left", padx=(0, 15))
            ctk.CTkLabel(score_badge, text=f"{r[4]}/{r[5]} ({pct:.0f}%)", font=("Helvetica Neue", 13, "bold"), text_color=pct_color).pack(padx=10, pady=4)

            ctk.CTkLabel(right, text=f"🔥 {r[7]} streak", font=("Helvetica Neue", 11, "bold"), text_color=PALETTE["warning"]).pack(side="left", padx=(0, 15))
            ctk.CTkLabel(right, text=f"⏱ {r[8]:.0f}s", font=("Helvetica Neue", 11), text_color=PALETTE["text_muted"]).pack(side="left")

    # ============================================================
    #  VIEW 10: AI CONFIGURATION (GOOGLE GEMINI)
    # ============================================================
    def show_ai_setup_view(self):
        self._clear_content()
        self._highlight_nav("AI Setup")

        scroll = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        header = ctk.CTkFrame(scroll, fg_color="transparent")
        header.pack(fill="x", pady=(5, 15))

        ctk.CTkLabel(
            header, text="Google Gemini AI Integration",
            font=("Helvetica Neue", 24, "bold"),
            text_color=PALETTE["text_primary"]
        ).pack(anchor="w")
        ctk.CTkLabel(
            header, text="Supercharge question generation with Google's state-of-the-art Gemini 1.5 Flash model.",
            font=("Helvetica Neue", 13),
            text_color=PALETTE["text_secondary"]
        ).pack(anchor="w", pady=(2, 0))

        # Main settings card
        card = ctk.CTkFrame(
            scroll, corner_radius=18,
            fg_color=PALETTE["card_bg"],
            border_width=1, border_color=PALETTE["card_border"]
        )
        card.pack(fill="x", pady=(0, 20))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=30, pady=24)

        ctk.CTkLabel(inner, text="Gemini API Key", font=("Helvetica Neue", 14, "bold"), text_color=PALETTE["text_primary"]).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(inner, text="Get your free key with high rate-limits from Google AI Studio (ai.google.dev).", font=("Helvetica Neue", 12), text_color=PALETTE["text_secondary"]).pack(anchor="w", pady=(0, 10))

        # Entry row with show/hide
        entry_row = ctk.CTkFrame(inner, fg_color="transparent")
        entry_row.pack(fill="x", pady=(0, 14))

        self.api_key_entry = ctk.CTkEntry(
            entry_row, height=44, corner_radius=10,
            placeholder_text="Paste your Google Gemini API key here...",
            font=("Helvetica Neue", 13), show="•"
        )
        self.api_key_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        if self.gemini.api_key:
            self.api_key_entry.insert(0, self.gemini.api_key)

        self.show_key_var = ctk.BooleanVar(value=False)
        def toggle_key_mask():
            self.api_key_entry.configure(show="" if self.show_key_var.get() else "•")

        ctk.CTkCheckBox(entry_row, text="Show", variable=self.show_key_var, command=toggle_key_mask, width=60).pack(side="left")

        # Status label
        self.ai_status_lbl = ctk.CTkLabel(inner, text="", font=("Helvetica Neue", 12, "bold"), wraplength=750, justify="left")
        self.ai_status_lbl.pack(anchor="w", pady=(0, 10))

        # Action buttons
        btn_row = ctk.CTkFrame(inner, fg_color="transparent")
        btn_row.pack(anchor="w")

        test_btn = ctk.CTkButton(
            btn_row, text="🔌 Connect & Test Key",
            command=self._test_gemini_key,
            width=180, height=40, corner_radius=10,
            font=("Helvetica Neue", 12, "bold"),
            fg_color=PALETTE["primary"], hover_color=PALETTE["primary_hover"]
        )
        test_btn.pack(side="left", padx=(0, 10))

        clear_btn = ctk.CTkButton(
            btn_row, text="Remove Key",
            command=self._remove_gemini_key,
            width=120, height=40, corner_radius=10,
            font=("Helvetica Neue", 12, "bold"),
            fg_color=PALETTE["card_bg_alt"], hover_color=PALETTE["danger_hover"],
            text_color=PALETTE["text_primary"]
        )
        clear_btn.pack(side="left")

        # Explanatory card
        help_card = ctk.CTkFrame(
            scroll, corner_radius=16,
            fg_color=PALETTE["card_bg_alt"],
            border_width=1, border_color=PALETTE["card_border"]
        )
        help_card.pack(fill="x", pady=10)

        h_inner = ctk.CTkFrame(help_card, fg_color="transparent")
        h_inner.pack(fill="both", expand=True, padx=24, pady=18)

        ctk.CTkLabel(h_inner, text="✨ Instant Offline Procedural Fallback", font=("Helvetica Neue", 14, "bold"), text_color=PALETTE["text_primary"]).pack(anchor="w")
        ctk.CTkLabel(
            h_inner,
            text="Quiz Master Pro includes an advanced, zero-dependency offline procedural generator. If you don't have an API key or lose internet connection, the app automatically switches to procedural generation without interruptions!",
            font=("Helvetica Neue", 12), text_color=PALETTE["text_secondary"], wraplength=880, justify="left"
        ).pack(anchor="w", pady=(4, 0))

    def _test_gemini_key(self):
        key = self.api_key_entry.get().strip()
        if not key:
            self.ai_status_lbl.configure(text="⚠️ Please enter an API key to test.", text_color=PALETTE["warning"])
            return

        self.ai_status_lbl.configure(text="⏳ Verifying connection to Google Gemini endpoint...", text_color=PALETTE["primary"])
        self.update()

        def test_worker():
            temp_client = GeminiClient(key)
            ok, msg = temp_client.test_connection()
            def update_ui():
                if ok:
                    self.gemini.update_key(key)
                    self.db.set_setting("gemini_api_key", key)
                    self.ai_status_lbl.configure(text=f"✅ {msg}", text_color=PALETTE["success"])
                else:
                    self.ai_status_lbl.configure(text=f"❌ {msg}", text_color=PALETTE["danger"])
            self.after(0, update_ui)

        threading.Thread(target=test_worker, daemon=True).start()

    def _remove_gemini_key(self):
        self.gemini.update_key("")
        self.db.set_setting("gemini_api_key", "")
        self.api_key_entry.delete(0, "end")
        self.ai_status_lbl.configure(text="Key removed. Procedural offline mode active.", text_color=PALETTE["text_muted"])

    # ============================================================
    #  VIEW 11: SETTINGS & PREFERENCES
    # ============================================================
    def show_settings_view(self):
        self._clear_content()
        self._highlight_nav("Settings")

        scroll = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        header = ctk.CTkFrame(scroll, fg_color="transparent")
        header.pack(fill="x", pady=(5, 15))

        ctk.CTkLabel(
            header, text="Application Preferences",
            font=("Helvetica Neue", 24, "bold"),
            text_color=PALETTE["text_primary"]
        ).pack(anchor="w")
        ctk.CTkLabel(
            header, text="Customize appearance, timers, question counts, and system storage.",
            font=("Helvetica Neue", 13),
            text_color=PALETTE["text_secondary"]
        ).pack(anchor="w", pady=(2, 0))

        # Settings Card
        card = ctk.CTkFrame(
            scroll, corner_radius=18,
            fg_color=PALETTE["card_bg"],
            border_width=1, border_color=PALETTE["card_border"]
        )
        card.pack(fill="x", pady=(0, 20))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=30, pady=24)

        # Theme Setting
        ctk.CTkLabel(inner, text="Appearance Theme:", font=("Helvetica Neue", 13, "bold"), text_color=PALETTE["text_primary"]).pack(anchor="w", pady=(0, 6))
        theme_seg = ctk.CTkSegmentedButton(
            inner, values=["Dark", "Light", "System"],
            command=self._on_theme_select,
            selected_color=PALETTE["primary"]
        )
        theme_seg.set(self.current_theme)
        theme_seg.pack(anchor="w", pady=(0, 18))

        # Default timer
        ctk.CTkLabel(inner, text="Default Timer Duration:", font=("Helvetica Neue", 13, "bold"), text_color=PALETTE["text_primary"]).pack(anchor="w", pady=(0, 6))
        t_seg = ctk.CTkSegmentedButton(
            inner, values=["10s", "15s", "20s", "30s"],
            command=self._on_timer_change,
            selected_color=PALETTE["primary"]
        )
        t_seg.set(f"{self.timer_seconds}s")
        t_seg.pack(anchor="w", pady=(0, 18))

        # Default question count
        ctk.CTkLabel(inner, text="Default Questions Per Quiz:", font=("Helvetica Neue", 13, "bold"), text_color=PALETTE["text_primary"]).pack(anchor="w", pady=(0, 6))
        q_seg = ctk.CTkSegmentedButton(
            inner, values=["5", "10", "15", "20"],
            command=self._on_q_count_change,
            selected_color=PALETTE["primary"]
        )
        q_seg.set(str(self.questions_per_quiz))
        q_seg.pack(anchor="w", pady=(0, 24))

        # Database management row
        ctk.CTkLabel(inner, text="Data Management:", font=("Helvetica Neue", 13, "bold"), text_color=PALETTE["text_primary"]).pack(anchor="w", pady=(0, 6))
        
        clear_hist_btn = ctk.CTkButton(
            inner, text="🗑 Clear All Quiz History",
            command=self._confirm_clear_history,
            width=200, height=38, corner_radius=10,
            font=("Helvetica Neue", 12, "bold"),
            fg_color=PALETTE["danger"], hover_color=PALETTE["danger_hover"]
        )
        clear_hist_btn.pack(anchor="w")

    def _on_theme_select(self, theme_val):
        self.current_theme = theme_val
        ctk.set_appearance_mode(theme_val)
        self.theme_btn.configure(text="☀️" if theme_val == "Light" else "🌙")
        self.db.set_setting("theme", theme_val)

    def _confirm_clear_history(self):
        if messagebox.askyesno("Confirm Reset", "Are you sure you want to permanently delete all recorded quiz attempts? This cannot be undone."):
            self.db.clear_all_history()
            messagebox.showinfo("Reset Complete", "All quiz history records have been cleared.")
            self.show_hub_view()

    # ── Application Exit ────────────────────────────────────────
    def on_exit(self):
        self._stop_timer()
        self.destroy()


# ================================================================
#  ENTRY POINT
# ================================================================

if __name__ == "__main__":
    app = QuizMasterProApp()
    app.mainloop()