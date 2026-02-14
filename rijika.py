import pygame
import sys
import random
import json
import os
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional, Callable
import math
import uuid
import threading

import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for pygame embedding
import matplotlib.pyplot as plt
import matplotlib.backends.backend_agg as agg

# ========== NEW IMPORTS for ML ==========
from sklearn.ensemble import RandomForestClassifier
from sklearn.multioutput import MultiOutputClassifier
import joblib
# ========================================

from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

load_dotenv()

pygame.init()

SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 950
FPS = 60

COLOR_BG = (10, 15, 25)
COLOR_PANEL = (20, 30, 45)
COLOR_PANEL_HOVER = (35, 50, 70)
COLOR_PRIMARY = (0, 200, 255)
COLOR_SUCCESS = (0, 255, 150)
COLOR_WARNING = (255, 200, 50)
COLOR_DANGER = (255, 80, 80)
COLOR_TEXT = (255, 255, 255)
COLOR_TEXT_DIM = (180, 200, 220)
COLOR_ACCENT = (180, 100, 255)
COLOR_BORDER = (60, 80, 100)
COLOR_GRADIENT_START = (0, 150, 255)
COLOR_GRADIENT_END = (100, 50, 200)
MONTHS_PER_GAME = 24
STARTING_HAPPINESS = 50
BURNOUT_STRESS = 100
BURNOUT_HAPPINESS = 10
ACTIONS_PER_MONTH = 3

AVATARS = [
    {"emoji": "👨‍💼", "label": "Executive"},
    {"emoji": "👩‍💼", "label": "Director"},
    {"emoji": "👨‍🎓", "label": "Scholar"},
    {"emoji": "👩‍🎓", "label": "Graduate"},
    {"emoji": "👨‍💻", "label": "Dev"},
    {"emoji": "👩‍💻", "label": "Coder"},
    {"emoji": "🧑‍🚀", "label": "Explorer"},
    {"emoji": "🦸",   "label": "Hero"},
    {"emoji": "🧙",   "label": "Wizard"},
    {"emoji": "🤑",   "label": "Mogul"},
    {"emoji": "🦊",   "label": "Fox"},
    {"emoji": "🐉",   "label": "Dragon"},
]

AVATAR_FACES = [
    ("😊", "Happy"),
    ("😎", "Cool"),
    ("🤩", "Star"),
    ("🥸", "Nerd"),
    ("😤", "Fierce"),
    ("😏", "Smirk"),
    ("🤓", "Geek"),
    ("😈", "Devil"),
]

AVATAR_ACCESSORIES = [
    ("", "None", (0, 0)),
    ("👑", "Crown", (0, -0.45)),
    ("🎩", "Top Hat", (0, -0.45)),
    ("🧢", "Cap", (0, -0.35)),
    ("👓", "Glasses", (0, 0)),
    ("🕶️", "Shades", (0, 0)),
    ("😷", "Mask", (0, 0)),
    ("🧔", "Beard", (0, 0)),
    ("🤑", "Money Eye", (0, -0.1)),
    ("🎓", "Grad Cap", (0.05, -0.45)),
    ("🎧", "Headphones", (0, -0.05)),
    ("⚔️", "Warrior", (0.4, -0.4)),
]

AVATAR_BG_COLORS = [
    ((0, 200, 255),   "Cyan"),
    ((180, 100, 255), "Purple"),
    ((0, 255, 150),   "Green"),
    ((255, 200, 50),  "Gold"),
    ((255, 80, 80),   "Red"),
    ((255, 150, 0),   "Orange"),
    ((100, 180, 255), "Blue"),
    ((255, 100, 200), "Pink"),
    ((150, 255, 100), "Lime"),
    ((200, 200, 200), "Silver"),
]

def draw_composite_avatar(screen, face_emoji, acc_data, x, y, font_size):
    font = pygame.font.SysFont("Segoe UI Emoji", int(font_size))
    face_surf = font.render(face_emoji, True, COLOR_TEXT)
    face_rect = face_surf.get_rect(center=(x, y))
    screen.blit(face_surf, face_rect)
    if acc_data and acc_data[0]:
        acc_emoji, _, offsets = acc_data
        off_x_pct, off_y_pct = offsets
        pixel_x = x + (font_size * off_x_pct)
        pixel_y = y + (font_size * off_y_pct)
        acc_surf = font.render(acc_emoji, True, COLOR_TEXT)
        acc_rect = acc_surf.get_rect(center=(pixel_x, pixel_y))
        screen.blit(acc_surf, acc_rect)


# ============================================================
# AI-POWERED FINANCIAL BOT
# ============================================================
class AIPoweredFinancialBot:
    def __init__(self):
        self.name = "Finley"
        self.avatar = "🦊"
        self.enabled = True
        self.is_thinking = False
        self.last_response = "Hi! I'm Finley, your AI-powered financial assistant! Ask me about investing, saving, debt, or well‑being! 🦊"
        self.ready = True
        self.hints = {
            "invest": [
                "Investing early lets compound interest work for you!",
                "Try investing $1k-$5k when you have extra cash.",
                "Higher risk = higher potential returns, but don't invest your emergency fund!"
            ],
            "save": [
                "Aim for 3 months of expenses in your emergency fund!",
                "Save at least $100 each month to build your safety net.",
                "Emergency fund protects you from unexpected costs like medical bills."
            ],
            "debt": [
                "Pay off high-interest debt first to reduce stress!",
                "Every $1k debt payment reduces your stress by 5%.",
                "Being debt-free is one of the 4 main goals!"
            ],
            "happiness": [
                "Low happiness causes debuffs! Take a vacation or date night.",
                "Balance work and life - don't forget leisure activities!",
                "Happiness below 30% will make you distracted and lose income."
            ],
            "stress": [
                "High stress leads to burnout! Use therapy or pay debt.",
                "Stress above 80% is dangerous - take action quickly!",
                "Emergency fund and low debt both help reduce stress."
            ],
            "education": [
                "University adds +$1500/month income but costs $30k debt and +15 stress!",
                "Masters requires University first, adds +$1000/month, costs $50k debt and +20 stress!",
                "Higher education is worth it long-term, but manage your stress levels!"
            ],
            "general": [
                f"You have {ACTIONS_PER_MONTH} actions per month - use them wisely!",
                "Complete all 4 goals for maximum bonus points!",
                "Right-click any action to lock it for next month!",
                "Net Worth = Cash + Investments + Emergency - Debt",
                "You started in Month 0 - survive 24 months to win!"
            ]
        }
        self.llm = None
        self.chain = None
        self.chat_runner = None
        self.session_id = str(uuid.uuid4())
        self.history = None
        try:
            AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
            AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
            AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
            AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
            if all([AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY,
                    AZURE_OPENAI_API_VERSION, AZURE_OPENAI_DEPLOYMENT]):
                self.llm = AzureChatOpenAI(
                    azure_endpoint=AZURE_OPENAI_ENDPOINT,
                    api_key=AZURE_OPENAI_API_KEY,
                    api_version=AZURE_OPENAI_API_VERSION,
                    deployment_name=AZURE_OPENAI_DEPLOYMENT,
                )
                self.prompt = ChatPromptTemplate.from_messages([
                    ("system", self._get_system_prompt()),
                    MessagesPlaceholder(variable_name="history"),
                    ("human", "{input}"),
                ])
                self.chain = self.prompt | self.llm
                self.history = ChatMessageHistory()
                self.chat_runner = RunnableWithMessageHistory(
                    self.chain,
                    lambda session_id: self.history,
                    input_messages_key="input",
                    history_messages_key="history",
                )
        except Exception as e:
            print(f" LLM setup failed: {e}")
            self.llm = None
            self.chat_runner = None

    def _get_system_prompt(self):
        return """
Role: You are "Finley", a financial assistant and virtual pet for CCDS Hackathon 2026.
Personality: Warm, encouraging, and knowledgeable about personal finance.
Goal: Help players manage their money, reduce stress, increase happiness, and achieve financial goals.
Response: Concise (2–3 sentences max). Use emojis occasionally to be friendly.
        """

    def get_context_from_game(self, game):
        return {
            'month': game.current_month,
            'money': game.money,
            'debt': game.debt,
            'investments': game.investments,
            'emergency_fund': game.emergency_fund,
            'happiness': game.happiness,
            'stress': game.stress,
            'actions_remaining': game.actions_remaining
        }

    def _hardcoded_response(self, question, game_state=None):
        question = question.lower()
        context = ""
        if game_state:
            context = f"(Month {game_state.get('month', 0)} - Cash: ${game_state.get('money', 0):,.0f}) "
        if "invest" in question:
            response = random.choice(self.hints["invest"])
        elif "save" in question or "emergency" in question:
            response = random.choice(self.hints["save"])
        elif "debt" in question or "pay" in question:
            response = random.choice(self.hints["debt"])
        elif "happ" in question or "fun" in question or "leisure" in question:
            response = random.choice(self.hints["happiness"])
        elif "stress" in question or "burnout" in question or "therapy" in question:
            response = random.choice(self.hints["stress"])
        elif "edu" in question or "university" in question or "master" in question or "degree" in question:
            response = random.choice(self.hints["education"])
        else:
            response = random.choice(self.hints["general"])
        return context + response

    def ask(self, question, game_state=None):
        self.is_thinking = True
        if self.chat_runner is None:
            self.last_response = self._hardcoded_response(question, game_state)
            self.is_thinking = False
            return self.last_response
        def worker():
            try:
                context_str = ""
                if game_state:
                    context_str = f"(Month {game_state['month']}, Cash: ${game_state['money']:,.0f}, Debt: ${game_state['debt']:,.0f}) "
                full_input = f"{context_str}{question}"
                result = self.chat_runner.invoke(
                    {"input": full_input},
                    config={"configurable": {"session_id": self.session_id}},
                )
                self.last_response = result.content
            except Exception as e:
                print(f"LLM error: {e}")
                self.last_response = self._hardcoded_response(question, game_state)
            finally:
                self.is_thinking = False
        threading.Thread(target=worker, daemon=True).start()
        return "..."

    def reset_conversation(self):
        if self.history:
            self.history.clear()
        self.last_response = "Conversation reset! How can I help you? 🦊"


# ============================================================
# CHATBOT UI HELPERS
# ============================================================

def draw_chatbot_icon(screen, x, y, is_thinking=False, has_new_message=False):
    pygame.draw.circle(screen, COLOR_ACCENT, (x, y), 30)
    pygame.draw.circle(screen, COLOR_PRIMARY, (x, y), 32, 2)
    font = pygame.font.SysFont("Arial", 36, bold=True)
    text = font.render("🦊", True, COLOR_TEXT)
    screen.blit(text, text.get_rect(center=(x, y)))
    if is_thinking:
        t = pygame.time.get_ticks() * 0.01
        dots = "." * (int(t) % 4)
        font_small = pygame.font.SysFont("Arial", 14)
        screen.blit(font_small.render(f"thinking{dots}", True, COLOR_TEXT_DIM), (x - 30, y + 35))
    if has_new_message and not is_thinking:
        pygame.draw.circle(screen, COLOR_SUCCESS, (x + 20, y - 20), 8)
        pygame.draw.circle(screen, COLOR_TEXT, (x + 20, y - 20), 10, 1)


def _wrap_text_modal(text, font, max_width):
    """Word-wrap helper that respects newlines in the text."""
    paragraphs = text.split('\n')
    all_lines = []
    for para in paragraphs:
        words = para.split()
        if not words:
            all_lines.append('')
            continue
        current_line = []
        for word in words:
            current_line.append(word)
            if font.size(' '.join(current_line))[0] > max_width:
                current_line.pop()
                if current_line:
                    all_lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            all_lines.append(' '.join(current_line))
    return all_lines


def draw_chatbot_modal(screen, font, chatbot, input_text="", input_active=False, game_state=None):
    """
    Dynamically-sized AI response bubble + visible input field.

    Changes vs original:
      1. Response bubble height is calculated from actual wrapped lines
         (grows/shrinks with content, max 60% of modal body height).
      2. Input box always shows placeholder text when empty.
      3. Bubble shows a subtle animated 'thinking…' indicator.

    Returns: (modal_x, modal_y, modal_w, modal_h, history_rect)
    """
    MODAL_W     = 500
    HEADER_H    = 70          # fox header bar
    INPUT_H     = 60          # input row at the bottom
    FOOTER_PAD  = 10          # gap below input
    BUBBLE_PAD  = 14          # inner padding inside the bubble
    LINE_H      = 22          # pixels per text line
    MAX_LINES   = 14          # cap bubble growth at this many lines
    FONT_SIZE   = 16

    font_small = pygame.font.SysFont("Arial", FONT_SIZE)

    # ── measure how many lines the current response needs ──────────────────
    bubble_inner_w = MODAL_W - 60 - BUBBLE_PAD * 2   # bubble width minus padding

    if chatbot.is_thinking:
        t = pygame.time.get_ticks() // 400
        display_text = "Finley is thinking" + "." * (t % 4)
    else:
        display_text = chatbot.last_response

    wrapped = _wrap_text_modal(display_text, font_small, bubble_inner_w)
    n_lines  = min(len(wrapped), MAX_LINES)
    n_lines  = max(n_lines, 2)          # always at least 2 lines tall

    bubble_h = n_lines * LINE_H + BUBBLE_PAD * 2

    # ── total modal height is dynamic ──────────────────────────────────────
    BODY_PAD   = 20           # gap above bubble
    BOTTOM_PAD = 14           # gap between bubble bottom and input
    MODAL_H    = HEADER_H + BODY_PAD + bubble_h + BOTTOM_PAD + INPUT_H + FOOTER_PAD

    modal_x = SCREEN_WIDTH - MODAL_W - 30
    modal_y = 100

    # ── modal shell ────────────────────────────────────────────────────────
    pygame.draw.rect(screen, COLOR_BG,
                     (modal_x, modal_y, MODAL_W, MODAL_H), border_radius=20)
    pygame.draw.rect(screen, COLOR_ACCENT,
                     (modal_x, modal_y, MODAL_W, MODAL_H), 3, border_radius=20)

    # header bar
    pygame.draw.rect(screen, COLOR_PANEL,
                     (modal_x, modal_y, MODAL_W, HEADER_H),
                     border_top_left_radius=20, border_top_right_radius=20)
    avatar_font = pygame.font.SysFont("Segoe UI Emoji", 36)
    screen.blit(avatar_font.render("🦊", True, COLOR_TEXT),
                (modal_x + 16, modal_y + 14))
    title_font = pygame.font.SysFont("Arial", 22, bold=True)
    screen.blit(
        title_font.render(f"{chatbot.name} – Financial Assistant", True, COLOR_PRIMARY),
        (modal_x + 70, modal_y + 22),
    )

    # ── response bubble ────────────────────────────────────────────────────
    bubble_x = modal_x + 20
    bubble_y = modal_y + HEADER_H + BODY_PAD
    bubble_w = MODAL_W - 40

    pygame.draw.rect(screen, COLOR_PANEL_HOVER,
                     (bubble_x, bubble_y, bubble_w, bubble_h), border_radius=14)
    pygame.draw.rect(screen, COLOR_ACCENT,
                     (bubble_x, bubble_y, bubble_w, bubble_h), 1, border_radius=14)

    # render text lines (clipped to MAX_LINES)
    text_color = COLOR_TEXT_DIM if chatbot.is_thinking else COLOR_TEXT
    for i, line in enumerate(wrapped[:MAX_LINES]):
        surf = font_small.render(line, True, text_color)
        screen.blit(surf, (bubble_x + BUBBLE_PAD,
                           bubble_y + BUBBLE_PAD + i * LINE_H))

    # overflow indicator
    if len(wrapped) > MAX_LINES:
        more_font = pygame.font.SysFont("Arial", 13)
        more_surf = more_font.render("▾ scroll for more", True, COLOR_ACCENT)
        screen.blit(more_surf,
                    (bubble_x + bubble_w - more_surf.get_width() - 8,
                     bubble_y + bubble_h - 18))

    # ── input box ──────────────────────────────────────────────────────────
    input_y   = bubble_y + bubble_h + BOTTOM_PAD
    input_rect = pygame.Rect(modal_x + 16, input_y, MODAL_W - 80, INPUT_H - 8)

    pygame.draw.rect(screen, COLOR_PANEL, input_rect, border_radius=10)
    border_col = COLOR_PRIMARY if input_active else COLOR_BORDER
    pygame.draw.rect(screen, border_col, input_rect, 2, border_radius=10)

    # placeholder or typed text
    cursor = "|" if (input_active and pygame.time.get_ticks() % 1000 < 500) else ""
    if input_text:
        display = input_text + cursor
        txt_col  = COLOR_TEXT
    else:
        display  = "Ask Finley anything… " + cursor if input_active else "💬  Ask Finley anything…"
        txt_col  = COLOR_TEXT_DIM

    inp_font = pygame.font.SysFont("Arial", 15)
    inp_surf = inp_font.render(display, True, txt_col)
    # vertically centre inside input box
    screen.blit(inp_surf, (input_rect.x + 12,
                            input_rect.y + (input_rect.height - inp_surf.get_height()) // 2))

    # ── history rect (for external hit-testing) ────────────────────────────
    history_rect = pygame.Rect(bubble_x, bubble_y, bubble_w, bubble_h)

    return modal_x, modal_y, MODAL_W, MODAL_H, history_rect, input_rect


# ============================================================
# GAME STATE & UI COMPONENTS
# ============================================================

class GameState(Enum):
    TITLE = 1
    TUTORIAL = 2
    SETUP = 3
    PLAYING = 4
    GAME_OVER = 5


@dataclass
class ClassConfig:
    name: str
    starting_money: float
    rent: float
    groceries: float
    transport: float
    debt: float
    description: str
    avatar_emoji: str = "👤"


@dataclass
class EducationConfig:
    name: str
    cost: float
    income: float
    description: str


@dataclass
class DifficultyConfig:
    name: str
    emergency_chance: float
    market_volatility: float
    description: str


@dataclass
class LifeChoice:
    name: str
    cost: float
    happiness: float
    stress: float
    choice_type: str
    debuff_chance: float = 0.0
    debuff: str = ""
    win_chance: float = 0.0
    win_amount: float = 0.0
    one_time: bool = False


@dataclass
class EmergencyEvent:
    name: str
    description: str
    cost: float = 0
    months_no_income: int = 0
    investment_loss: float = 0.0
    stress_increase: float = 0


class Button:
    def __init__(self, x, y, width, height, text, color=COLOR_PANEL, text_color=COLOR_TEXT,
                 button_id="", tooltip="", gradient=False, icon=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.base_color = color
        self.text_color = text_color
        self.hover = False
        self.enabled = True
        self.callback: Optional[Callable] = None
        self.button_id = button_id
        self.visible = True
        self.original_y = y
        self.tooltip = tooltip
        self.gradient = gradient
        self.icon = icon
        self.pulse = 0
        self.pulse_dir = 1
        self.action_type = None
        self.lock_data = None
        self._text_cache = {}
        self._cache_dirty = True

    def _get_cached_text(self, font, color):
        cache_key = (self.text, id(font), color)
        if self._cache_dirty or cache_key not in self._text_cache:
            lines = self.text.split('\n')
            surfaces = [font.render(line, True, color) for line in lines]
            self._text_cache[cache_key] = (lines, surfaces)
            self._cache_dirty = False
        return self._text_cache[cache_key]

    def draw(self, screen, font):
        if not self.visible:
            return
        if self.button_id == "next_month" and self.enabled:
            self.pulse += 0.05 * self.pulse_dir
            if self.pulse > 1 or self.pulse < 0:
                self.pulse_dir *= -1
            pulse_offset = int(3 * math.sin(self.pulse))
        else:
            pulse_offset = 0
        if not self.enabled:
            draw_color = (40, 45, 55)
            draw_text_color = (80, 85, 95)
            border_color = (60, 65, 75)
        elif self.hover:
            c = self.base_color
            draw_color = (min(c[0]+50, 255), min(c[1]+50, 255), min(c[2]+50, 255))
            draw_text_color = self.text_color
            border_color = COLOR_PRIMARY
        else:
            draw_color = self.base_color
            draw_text_color = self.text_color
            border_color = COLOR_BORDER
        if self.enabled:
            shadow_offset = 6 if self.hover else 3
            shadow_alpha = 100 if self.hover else 50
            shadow_surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            shadow_surf.fill((0, 0, 0, shadow_alpha))
            screen.blit(shadow_surf, (self.rect.x + shadow_offset, self.rect.y + shadow_offset + pulse_offset))
        if self.gradient and self.enabled:
            for i in range(self.rect.height):
                ratio = i / self.rect.height
                color = (
                    int(COLOR_GRADIENT_START[0] * (1 - ratio) + COLOR_GRADIENT_END[0] * ratio),
                    int(COLOR_GRADIENT_START[1] * (1 - ratio) + COLOR_GRADIENT_END[1] * ratio),
                    int(COLOR_GRADIENT_START[2] * (1 - ratio) + COLOR_GRADIENT_END[2] * ratio)
                )
                pygame.draw.line(screen, color,
                                 (self.rect.x, self.rect.y + i - pulse_offset),
                                 (self.rect.x + self.rect.width, self.rect.y + i - pulse_offset))
        else:
            button_y = self.rect.y - (2 if self.hover else 0) - pulse_offset
            button_rect = pygame.Rect(self.rect.x, button_y, self.rect.width, self.rect.height)
            pygame.draw.rect(screen, draw_color, button_rect, border_radius=12)
        border_width = 3 if self.hover else 2
        if self.enabled:
            button_rect = pygame.Rect(self.rect.x, self.rect.y - pulse_offset, self.rect.width, self.rect.height)
            pygame.draw.rect(screen, border_color, button_rect, border_width, border_radius=12)
        display_text = self.text
        if self.icon:
            display_text = f"{self.icon} {self.text}"
        lines, surfaces = self._get_cached_text(font, draw_text_color)
        total_height = len(lines) * font.get_linesize()
        start_y = button_rect.centery - total_height // 2
        for i, text_surface in enumerate(surfaces):
            text_rect = text_surface.get_rect(
                center=(button_rect.centerx, start_y + i * font.get_linesize() + font.get_linesize() // 2))
            screen.blit(text_surface, text_rect)

    def draw_tooltip(self, screen, font):
        if not self.hover or not self.tooltip or not self.enabled:
            return
        padding = 12
        tooltip_font = pygame.font.SysFont("Arial", 14, bold=True)
        max_width = 350
        words = self.tooltip.split()
        lines = []
        current_line = []
        for word in words:
            current_line.append(word)
            if tooltip_font.size(' '.join(current_line))[0] > max_width - padding * 2:
                current_line.pop()
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        line_height = tooltip_font.get_linesize()
        tooltip_width = max(tooltip_font.size(line)[0] for line in lines) + padding * 2
        tooltip_height = len(lines) * line_height + padding * 2
        mouse_x, mouse_y = pygame.mouse.get_pos()
        tooltip_x = mouse_x + 20
        tooltip_y = mouse_y + 20
        if tooltip_x + tooltip_width > screen.get_width():
            tooltip_x = mouse_x - tooltip_width - 20
        if tooltip_y + tooltip_height > screen.get_height():
            tooltip_y = mouse_y - tooltip_height - 20
        tooltip_rect = pygame.Rect(tooltip_x, tooltip_y, tooltip_width, tooltip_height)
        for i in range(tooltip_rect.height):
            alpha = 230 + i * 0.1
            color = (25, 35, 50, min(255, int(alpha)))
            pygame.draw.line(screen, color[:3],
                             (tooltip_rect.x, tooltip_rect.y + i),
                             (tooltip_rect.x + tooltip_rect.width, tooltip_rect.y + i))
        pygame.draw.rect(screen, COLOR_PRIMARY, tooltip_rect, 2, border_radius=8)
        y = tooltip_y + padding
        for line in lines:
            text_surf = tooltip_font.render(line, True, COLOR_TEXT)
            screen.blit(text_surf, (tooltip_x + padding, y))
            y += line_height

    def handle_event(self, event) -> bool:
        if not self.visible or not self.enabled:
            return False
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hover:
                if self.callback:
                    self.callback()
                return True
        return False

    def update_text(self, new_text: str):
        if self.text != new_text:
            self.text = new_text
            self._cache_dirty = True


# ============================================================
# CUSTOM AVATAR CREATOR STATE
# ============================================================

class CustomAvatarCreator:
    def __init__(self):
        self.visible = False
        self.selected_face_idx = 0
        self.selected_acc_idx = 0
        self.selected_bg_idx = 0
        self.custom_emoji_text = ""
        self.custom_emoji_input_active = False
        self.tab = 'builder'

    def get_avatar_composition(self):
        if self.custom_emoji_text.strip():
            return (self.custom_emoji_text.strip(), AVATAR_ACCESSORIES[0])
        face = AVATAR_FACES[self.selected_face_idx][0]
        acc_data = AVATAR_ACCESSORIES[self.selected_acc_idx]
        return (face, acc_data)

    def get_bg_color(self):
        return AVATAR_BG_COLORS[self.selected_bg_idx][0]

    def reset_custom(self):
        self.custom_emoji_text = ""
        self.custom_emoji_input_active = False


class FinanceGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("FinanceQuest - Master Your Financial Future")
        self.clock = pygame.time.Clock()
        pygame.event.set_allowed([pygame.QUIT, pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION,
                                   pygame.MOUSEWHEEL, pygame.KEYDOWN])
        self._init_fonts()
        self.state = GameState.TITLE
        self.tutorial_step = 0
        self.selected_class = None
        self.selected_education = None
        self.selected_difficulty = None
        self.selected_avatar_index = 0
        self.particles = []
        self._init_player_stats()
        self.debuffs = []
        self.months_no_income = 0
        self.has_vehicle = False
        self.current_education_level = 'polytechnic'
        self.has_university = False
        self.has_masters = False
        self.game_message = ""
        self.high_score = self._load_high_score()
        self._init_goals()
        self.show_event_modal = False
        self.current_event = None
        self.scroll_offset = 0
        self.max_scroll = 0
        self.help_scroll_offset = 0
        self.help_max_scroll = 0
        self.cached_buttons = {state: [] for state in GameState}
        self.need_button_update = True
        self._bg_cache = {}
        self._init_configs()
        self._init_ui_elements()
        self.active_dropdown = None
        self.dropdown_hover = False
        self.dropdown_last_hover_time = 0
        self.dropdown_stay_duration = 2000
        self.show_custom_input = False
        self.custom_input_text = ""
        self.custom_input_type = ""
        self.show_chatbot = False
        self.chatbot_input_text = ""
        self.chatbot_input_active = False
        self.chatbot = AIPoweredFinancialBot()
        self.chatbot_has_new_message = False
        self.avatar_creator = CustomAvatarCreator()

        # ========== DATA SCIENCE ADDITIONS ==========
        self.monthly_log = []               # monthly snapshots for dashboard
        # Action counters for statistics
        self.total_investments = 0
        self.total_saved = 0
        self.total_debt_paid = 0
        self.num_leisure = 0
        self.num_risky = 0

        # ========== GOAL PREDICTION ==========
        self.goal_predictor = None
        self.goal_features = None
        self._load_goal_predictor()
        # ======================================

    def _init_fonts(self):
        self.font_xl = pygame.font.SysFont("Arial Black", 72, bold=True)
        self.font_large = pygame.font.SysFont("Arial", 48, bold=True)
        self.font_medium = pygame.font.SysFont("Arial", 28, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 20, bold=True)
        self.font_tiny = pygame.font.SysFont("Arial", 16)
        self.font_digital = pygame.font.SysFont("Courier New", 32, bold=True)
        self.font_emoji_large = pygame.font.SysFont("Segoe UI Emoji", 30)
        self.font_emoji_header = pygame.font.SysFont("Segoe UI Emoji", 28)
        self.font_emoji_xl = pygame.font.SysFont("Segoe UI Emoji", 52)
        self.font_emoji_med = pygame.font.SysFont("Segoe UI Emoji", 26)

    def _init_player_stats(self):
        self.money = 0.0
        self.monthly_income = 0.0
        self.debt = 0.0
        self.investments = 0.0
        self.emergency_fund = 0.0
        self.happiness = STARTING_HAPPINESS
        self.stress = 0.0
        self.current_month = 0
        self.rent = 0.0
        self.groceries = 0.0
        self.transport = 0.0
        self.actions_taken_this_month = 0
        self.actions_remaining = ACTIONS_PER_MONTH
        self.locked_action = None
        self.show_help_panel = False
        self.current_tooltip = ""
        self.selected_avatar = AVATARS[0]["emoji"]
        self.selected_avatar_acc = AVATAR_ACCESSORIES[0]
        self.selected_avatar_bg = AVATAR_BG_COLORS[0][0]
        self.active_dropdown = None
        self.dropdown_hover = False
        self.dropdown_last_hover_time = 0
        self.dropdown_stay_duration = 2000
        self.show_custom_input = False
        self.custom_input_text = ""
        self.custom_input_type = ""
        self.help_scroll_offset = 0
        self.help_max_scroll = 0

    # ========== DATA SCIENCE HELPER METHODS ==========
    def _save_game_summary(self):
        if not self.monthly_log:
            return
        avg_happiness = sum(m['happiness'] for m in self.monthly_log) / len(self.monthly_log)
        avg_stress = sum(m['stress'] for m in self.monthly_log) / len(self.monthly_log)
        summary = {
            'class': self.selected_class,
            'education': self.selected_education,
            'difficulty': self.selected_difficulty,
            'total_investments': self.total_investments,
            'total_saved': self.total_saved,
            'total_debt_paid': self.total_debt_paid,
            'num_leisure': self.num_leisure,
            'num_risky': self.num_risky,
            'had_addiction': int('addict' in self.debuffs),
            'avg_happiness': avg_happiness,
            'avg_stress': avg_stress,
            'final_score': self.calculate_score(),
        }
        try:
            with open('game_summaries.json', 'r') as f:
                summaries = json.load(f)
        except FileNotFoundError:
            summaries = []
        summaries.append(summary)
        with open('game_summaries.json', 'w') as f:
            json.dump(summaries, f, indent=2)

    def _save_goal_training_data(self):
        """Save early-game features and final goal outcomes for training."""
        if len(self.monthly_log) < 6:
            return  # not enough data
        early = self.monthly_log[:6]
        avg_hap = sum(m['happiness'] for m in early) / 6
        avg_str = sum(m['stress'] for m in early) / 6

        # Use the cumulative action totals (they include actions up to month 6)
        # This is a simplification; ideally we'd have per‑month action counts.
        data = {
            'early_avg_happiness': avg_hap,
            'early_avg_stress': avg_str,
            'early_total_investments': self.total_investments,
            'early_total_saved': self.total_saved,
            'early_total_debt_paid': self.total_debt_paid,
            'early_num_leisure': self.num_leisure,
            'early_num_risky': self.num_risky,
            'goal_networth': self.goals['netWorth']['completed'],
            'goal_emergency': self.goals['emergencyFund']['completed'],
            'goal_debtfree': self.goals['debtFree']['completed'],
            'goal_happiness': self.goals['happiness']['completed'],
        }
        try:
            with open('goal_training_data.json', 'r') as f:
                all_data = json.load(f)
        except FileNotFoundError:
            all_data = []
        all_data.append(data)
        with open('goal_training_data.json', 'w') as f:
            json.dump(all_data, f, indent=2)

    def _load_goal_predictor(self):
        if os.path.exists('goal_predictor.pkl') and os.path.exists('goal_features.pkl'):
            try:
                self.goal_predictor = joblib.load('goal_predictor.pkl')
                self.goal_features = joblib.load('goal_features.pkl')
            except Exception as e:
                print(f"Failed to load goal predictor: {e}")
                self.goal_predictor = None

    def predict_goal_completion(self):
        # 1. Safety Check: Ensure model exists and we have enough game data
        if not self.goal_predictor or len(self.monthly_log) < 6:
            return None

        # 2. Extract features from the first 6 months
        early = self.monthly_log[:6]
        avg_hap = sum(m['happiness'] for m in early) / 6
        avg_str = sum(m['stress'] for m in early) / 6
        
        features = pd.DataFrame([[
            avg_hap,
            avg_str,
            self.total_investments,
            self.total_saved,
            self.total_debt_paid,
            self.num_leisure,
            self.num_risky
        ]], columns=self.goal_features)

        # 3. Get predictions
        # probs is a list of arrays (one for each of the 4 goals)
        probs = self.goal_predictor.predict_proba(features)

        # 4. Helper function to safely extract "Success" probability
        def get_prob(prob_array):
            # If the model only saw one outcome during training (e.g., always failed),
            # the array shape will be (1, 1) and index 1 won't exist.
            if prob_array.shape[1] < 2:
                # Default to 0.0 (0%) if we can't find the success probability
                return 0.0 
            return prob_array[0][1]

        # 5. Build results safely
        try:
            results = {
                'Net Worth':      get_prob(probs[0]),
                'Emergency Fund': get_prob(probs[1]),
                'Debt Free':      get_prob(probs[2]),
                'Happiness':      get_prob(probs[3])
            }
        except Exception as e:
            print(f"⚠️ Prediction error: {e}")
            return None

        return results
    def _show_goal_predictions(self):
        if not self.goal_predictor or len(self.monthly_log) < 6:
            self.game_message = "Need at least 6 months of data and a trained model."
            return
        results = self.predict_goal_completion()
        if not results:
            return

        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

        panel_w, panel_h = 500, 350
        panel_x = (SCREEN_WIDTH - panel_w) // 2
        panel_y = (SCREEN_HEIGHT - panel_h) // 2
        pygame.draw.rect(self.screen, COLOR_PANEL, (panel_x, panel_y, panel_w, panel_h), border_radius=15)
        pygame.draw.rect(self.screen, COLOR_ACCENT, (panel_x, panel_y, panel_w, panel_h), 3, border_radius=15)

        self._draw_text("Goal Completion Odds", self.font_medium, COLOR_PRIMARY, panel_x+panel_w//2, panel_y+30, center=True)

        y = panel_y + 70
        for goal, prob in results.items():
            color = COLOR_SUCCESS if prob > 0.7 else COLOR_WARNING if prob > 0.3 else COLOR_DANGER
            self._draw_text(f"{goal}: {prob*100:.1f}%", self.font_small, color, panel_x+30, y)
            # progress bar
            bar_x = panel_x + 200
            bar_y = y - 5
            bar_w = 250
            bar_h = 20
            pygame.draw.rect(self.screen, COLOR_PANEL_HOVER, (bar_x, bar_y, bar_w, bar_h), border_radius=5)
            fill_w = int(bar_w * prob)
            pygame.draw.rect(self.screen, color, (bar_x, bar_y, fill_w, bar_h), border_radius=5)
            y += 40

        # Close button
        close_btn = Button(panel_x+panel_w-60, panel_y+10, 40, 40, "✕", COLOR_DANGER, COLOR_TEXT, "close_pred")
        close_btn.draw(self.screen, self.font_small)
        pygame.display.flip()

        # Wait for click
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if close_btn.rect.collidepoint(event.pos):
                        waiting = False
            self.clock.tick(30)

    def show_dashboard(self):
        if not self.monthly_log:
            return

        # Helper to convert pygame 0-255 colors to matplotlib 0-1 floats
        def norm(color):
            return tuple(c/255.0 for c in color)

        df = pd.DataFrame(self.monthly_log)
        df['net_worth'] = df['money'] + df['investments'] + df['emergency_fund'] - df['debt']

        # Custom dark theme
        plt.style.use('dark_background')
        fig, axes = plt.subplots(2, 2, figsize=(12, 9))
        fig.patch.set_facecolor(norm(COLOR_BG))
        fig.suptitle(f'GAME DASHBOARD — Final Score: {self.calculate_score():,}', 
                    fontsize=18, fontweight='bold', color=norm(COLOR_PRIMARY), y=0.98)

        # Colors for plots (normalized)
        colors = {
            'net_worth': norm(COLOR_PRIMARY),
            'happiness': norm(COLOR_SUCCESS),
            'stress': norm(COLOR_DANGER),
            'cash': norm((0, 255, 150)),      # lime
            'invest': norm(COLOR_PRIMARY),
            'emergency': norm(COLOR_WARNING),
            'debt': norm(COLOR_DANGER)
        }
        panel_bg = norm(COLOR_PANEL)
        panel_hover = norm(COLOR_PANEL_HOVER)
        text_dim = norm(COLOR_TEXT_DIM)
        text_color = norm(COLOR_TEXT)
        accent = norm(COLOR_ACCENT)
        border = norm(COLOR_BORDER)

        # 1. Net worth over time
        ax = axes[0,0]
        ax.set_facecolor(panel_bg)
        ax.plot(df['month'], df['net_worth'], marker='o', color=colors['net_worth'], 
                linewidth=3, markersize=8)
        ax.set_title('Net Worth Progression', color=accent, fontsize=14)
        ax.set_xlabel('Month', color=text_dim)
        ax.set_ylabel('$', color=text_dim)
        ax.tick_params(colors=text_dim)
        ax.grid(True, linestyle='--', alpha=0.3, color=border)
        for spine in ax.spines.values():
            spine.set_color(border)

        # 2. Happiness vs Stress
        ax = axes[0,1]
        ax.set_facecolor(panel_bg)
        ax.plot(df['month'], df['happiness'], label='Happiness', color=colors['happiness'],
                linewidth=3)
        ax.plot(df['month'], df['stress'], label='Stress', color=colors['stress'],
                linewidth=3)
        ax.set_title('Well‑Being Over Time', color=accent, fontsize=14)
        ax.set_xlabel('Month', color=text_dim)
        ax.set_ylabel('Percentage', color=text_dim)
        ax.set_ylim(0, 100)
        ax.tick_params(colors=text_dim)
        ax.legend(facecolor=panel_bg, labelcolor=text_color)
        ax.grid(True, linestyle='--', alpha=0.3, color=border)
        for spine in ax.spines.values():
            spine.set_color(border)

        # 3. Final asset composition
        ax = axes[1,0]
        ax.set_facecolor(panel_bg)
        end = df.iloc[-1]
        labels = ['Cash', 'Investments', 'Emergency', 'Debt (-)']
        values = [end['money'], end['investments'], end['emergency_fund'], -end['debt']]
        bar_colors = [colors['cash'], colors['invest'], colors['emergency'], colors['debt']]
        bars = ax.bar(labels, values, color=bar_colors, edgecolor=border, linewidth=2)
        ax.set_title('Final Financial Snapshot', color=accent, fontsize=14)
        ax.tick_params(colors=text_dim, rotation=15)
        ax.axhline(0, color=border, linewidth=1)

        # Legend
        from matplotlib.patches import Rectangle
        legend_handles = [Rectangle((0,0),1,1, color=bar_colors[i], ec=border, linewidth=2) for i in range(len(labels))]
        ax.legend(legend_handles, labels, loc='upper right', facecolor=panel_bg, labelcolor=text_color, framealpha=0.9)

        for spine in ax.spines.values():
            spine.set_color(border)

        # 4. Action statistics (text panel)
        ax = axes[1,1]
        ax.set_facecolor(panel_bg)
        ax.axis('off')
        stats_text = (
            f"Total Invested: ${self.total_investments:,.0f}\n"
            f"Total Saved: ${self.total_saved:,.0f}\n"
            f"Debt Paid: ${self.total_debt_paid:,.0f}\n"
            f"Leisure Actions: {self.num_leisure}\n"
            f"Risky Actions: {self.num_risky}\n"
            f"Had Addiction: {'Yes' if 'addict' in self.debuffs else 'No'}"
        )
        ax.text(0.1, 0.5, stats_text, transform=ax.transAxes,
                fontsize=13, color=text_color, verticalalignment='center',
                family='monospace', linespacing=1.8,
                bbox=dict(boxstyle='round,pad=0.5', facecolor=panel_hover, 
                        edgecolor=accent, linewidth=2))

        plt.tight_layout()

        # Render to pygame surface
        canvas = agg.FigureCanvasAgg(fig)
        canvas.draw()
        buffer, (width, height) = canvas.print_to_buffer()
        surf = pygame.image.frombuffer(buffer, (width, height), "RGBA")

        # Draw semi‑transparent overlay behind dashboard
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # Blit the dashboard surface
        dash_x = (SCREEN_WIDTH - width) // 2
        dash_y = (SCREEN_HEIGHT - height) // 2
        self.screen.blit(surf, (dash_x, dash_y))

        # ---- CLOSE BUTTON ----
        close_btn_size = 40
        close_btn_rect = pygame.Rect(dash_x + width - close_btn_size - 10, dash_y + 10, close_btn_size, close_btn_size)
        pygame.draw.rect(self.screen, COLOR_DANGER, close_btn_rect, border_radius=8)
        pygame.draw.rect(self.screen, COLOR_TEXT, close_btn_rect, 2, border_radius=8)
        self._draw_text("✕", self.font_medium, COLOR_TEXT, close_btn_rect.centerx, close_btn_rect.centery, center=True)

        pygame.display.flip()

        # Wait for close button or ESC key
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    waiting = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if close_btn_rect.collidepoint(event.pos):
                        waiting = False
            self.clock.tick(30)
    # ===================================================

    def _toggle_chatbot(self):
        self.show_chatbot = not self.show_chatbot
        self.chatbot_input_active = False
        if self.show_chatbot:
            self.chatbot_has_new_message = False

    def _send_chatbot_message(self):
        if not self.chatbot_input_text.strip():
            return
        question = self.chatbot_input_text
        self.chatbot_input_text = ""
        context = self.chatbot.get_context_from_game(self)
        def ask_ai():
            self.chatbot.ask(question, context)
            self.chatbot_has_new_message = True
        threading.Thread(target=ask_ai, daemon=True).start()

    def _add_particle(self, x, y, color):
        self.particles.append({
            'x': x, 'y': y,
            'vx': random.uniform(-2, 2), 'vy': random.uniform(-3, 1),
            'life': 60, 'color': color, 'size': random.randint(2, 4)
        })

    def _update_particles(self):
        for p in self.particles[:]:
            p['x'] += p['vx']; p['y'] += p['vy']
            p['vy'] += 0.1; p['life'] -= 1
            if p['life'] <= 0:
                self.particles.remove(p)

    def _draw_particles(self):
        for p in self.particles:
            pygame.draw.circle(self.screen, p['color'][:3],
                               (int(p['x']), int(p['y'])), p['size'])

    def _init_goals(self):
        self.goals = {
            'netWorth':    {'target': 50000, 'completed': False, 'label': 'Net Worth $50k'},
            'emergencyFund': {'target': 10000, 'completed': False, 'label': 'Save $10k Fund'},
            'debtFree':    {'completed': False, 'label': 'Become Debt-Free'},
            'happiness':   {'target': 70, 'completed': False, 'label': '70+ Happiness'}
        }

    def _init_configs(self):
        self.class_configs = {
            'upper': ClassConfig("Upper Class", 50000, 2500, 800, 400, 0, "No debt - Start with financial freedom", "💼"),
            'middle': ClassConfig("Middle Class", 15000, 1500, 500, 300, 5000, "Some starting debt - Balanced start", "👔"),
            'lower':  ClassConfig("Lower Class", 2000, 800, 300, 150, 15000, "Significant debt - Challenging start", "🎒")
        }
        self.education_configs = {
            'polytechnic': EducationConfig("Polytechnic", 0, 3500, "Standard education - No debt"),
            'university':  EducationConfig("University", 30000, 5000, "Higher earning potential, high debt"),
            'masters':     EducationConfig("Masters", 50000, 6500, "Max earning potential, massive debt")
        }
        self.difficulty_configs = {
            'easy':   DifficultyConfig("Easy Mode", 0.05, 0.5, "Fewer emergencies, stable markets"),
            'normal': DifficultyConfig("Normal Mode", 0.10, 1.0, "Balanced challenge"),
            'hard':   DifficultyConfig("Hard Mode", 0.20, 1.5, "Frequent emergencies, volatile markets")
        }
        self.life_choices = {
            'vacation':     LifeChoice("Vacation", 2500, 15, -10, "leisure"),
            'fineDining':   LifeChoice("Fine Dining", 500, 8, -3, "leisure"),
            'staycation':   LifeChoice("Staycation", 800, 10, -5, "leisure"),
            'themePark':    LifeChoice("Theme Park", 300, 12, -4, "leisure"),
            'shopping':     LifeChoice("Shopping", 1000, 10, -5, "risky", 0.3, "addict"),
            'gambling':     LifeChoice("Gambling", 1500, 5, 0, "risky", 0.4, "addict", 0.2, 3000),
            'clubbing':     LifeChoice("Clubbing", 600, 8, -3, "risky", 0.25, "addict"),
            'smoking':      LifeChoice("Smoking", 200, 2, -8, "risky", 0.5, "addict"),
            'vehicle':      LifeChoice("Buy Vehicle", 25000, 20, 0, "utility", one_time=True),
            'relationship': LifeChoice("Date Night", 500, 15, -5, "utility"),
            'university':   LifeChoice("University", 30000, 0, 0, "education", one_time=True),
            'masters':      LifeChoice("Masters", 50000, 0, 0, "education", one_time=True)
        }
        self.emergency_events = [
            EmergencyEvent("Medical Emergency", "You've been diagnosed with a serious health condition requiring immediate treatment.", cost=8000, stress_increase=30),
            EmergencyEvent("Job Loss", "Your company has downsized and you've been laid off. No income for 3 months.", months_no_income=3, stress_increase=40),
            EmergencyEvent("Market Crash", "The stock market has crashed! Your investments have lost significant value.", investment_loss=0.4, stress_increase=25),
            EmergencyEvent("Home Emergency", "Major repairs needed for your living space.", cost=3500, stress_increase=15),
            EmergencyEvent("Family Emergency", "A family member needs financial assistance urgently.", cost=5000, stress_increase=20)
        ]

    def _init_ui_elements(self):
        self._init_title_buttons()
        self._init_tutorial_buttons()
        self._init_setup_buttons()
        self._init_game_over_buttons()

    def _init_title_buttons(self):
        self.cached_buttons[GameState.TITLE] = [
            Button(SCREEN_WIDTH//2-150, 500, 300, 70, "New Game", COLOR_PRIMARY, text_color=COLOR_BG, button_id="new_game", gradient=True),
            Button(SCREEN_WIDTH//2-150, 590, 300, 70, "Skip Tutorial", COLOR_PANEL, text_color=COLOR_TEXT, button_id="skip_tutorial"),
            Button(SCREEN_WIDTH-150, 20, 130, 50, "Help", COLOR_ACCENT, text_color=COLOR_TEXT, button_id="help_title",)
        ]
        self.cached_buttons[GameState.TITLE][0].callback = lambda: setattr(self, 'state', GameState.TUTORIAL)
        self.cached_buttons[GameState.TITLE][1].callback = lambda: setattr(self, 'state', GameState.SETUP)
        self.cached_buttons[GameState.TITLE][2].callback = self._toggle_help

    def _init_tutorial_buttons(self):
        panel_rect = pygame.Rect(200, 150, SCREEN_WIDTH-400, 500)
        btn_y = panel_rect.bottom - 90
        self.cached_buttons[GameState.TUTORIAL] = [
            Button(panel_rect.left+50, btn_y, 180, 50, "Previous", COLOR_PANEL_HOVER, button_id="tut_prev"),
            Button(panel_rect.right-230, btn_y, 180, 50, "Next", COLOR_PRIMARY, text_color=COLOR_BG, button_id="tut_next", gradient=True),
            Button(SCREEN_WIDTH-250, 800, 200, 50, "Skip All", COLOR_PANEL, button_id="tut_skip")
        ]
        self.cached_buttons[GameState.TUTORIAL][0].callback = self._tut_prev
        self.cached_buttons[GameState.TUTORIAL][1].callback = self._tut_next
        self.cached_buttons[GameState.TUTORIAL][2].callback = self._tut_skip

    def _init_setup_buttons(self):
        self.cached_buttons[GameState.SETUP] = [
            Button(SCREEN_WIDTH//2-120, 820, 240, 55, "Start Journey", COLOR_SUCCESS, text_color=COLOR_BG, button_id="setup_start", gradient=True),
            Button(SCREEN_WIDTH//2-80, 882, 160, 40, "Back", COLOR_PANEL, button_id="setup_back")
        ]
        self.cached_buttons[GameState.SETUP][0].callback = self.start_game
        self.cached_buttons[GameState.SETUP][1].callback = lambda: setattr(self, 'state', GameState.TITLE)

    def _init_game_over_buttons(self):
        center_x = SCREEN_WIDTH // 2
        self.cached_buttons[GameState.GAME_OVER] = [
            Button(center_x - 220, 680, 200, 60, "Play Again", COLOR_SUCCESS, text_color=COLOR_BG, button_id="play_again", gradient=True),
            Button(center_x + 20, 680, 200, 60, "Main Menu", COLOR_PANEL, button_id="menu"),
            Button(center_x - 100, 760, 200, 50, "View Statistics", COLOR_ACCENT, text_color=COLOR_TEXT, button_id="stats")
        ]
        self.cached_buttons[GameState.GAME_OVER][0].callback = self._reset_for_new_game
        self.cached_buttons[GameState.GAME_OVER][1].callback = lambda: setattr(self, 'state', GameState.TITLE)
        self.cached_buttons[GameState.GAME_OVER][2].callback = self.show_dashboard

    def _reset_for_new_game(self):
        self.state = GameState.SETUP
        self.tutorial_step = 0
        self.selected_class = None
        self.selected_education = None
        self.selected_difficulty = None
        self.selected_avatar_index = 0
        self.need_button_update = True

    def _init_playing_buttons(self):
        if self.cached_buttons[GameState.PLAYING]:
            return
        next_btn = Button(0, 0, 200, 80, "NEXT MONTH", COLOR_SUCCESS, text_color=COLOR_BG, button_id="next_month", gradient=True)
        next_btn.callback = self.next_month
        self.cached_buttons[GameState.PLAYING].append(next_btn)
        help_btn = Button(SCREEN_WIDTH-120, 20, 100, 40, "HELP", COLOR_ACCENT, text_color=COLOR_TEXT, button_id="help")
        help_btn.callback = self._toggle_help
        self.cached_buttons[GameState.PLAYING].append(help_btn)
        chatbot_btn = Button(SCREEN_WIDTH-230, 20, 100, 40, "ASK AI", COLOR_PRIMARY, text_color=COLOR_BG, button_id="chatbot", gradient=True, icon="🦊")
        chatbot_btn.callback = self._toggle_chatbot
        self.cached_buttons[GameState.PLAYING].append(chatbot_btn)

        # ========== NEW PREDICT BUTTON ==========
        predict_btn = Button(SCREEN_WIDTH-350, 20, 120, 40, "PREDICT GOALS", COLOR_ACCENT, COLOR_TEXT, button_id="predict")
        predict_btn.callback = self._show_goal_predictions
        self.cached_buttons[GameState.PLAYING].append(predict_btn)
        # ========================================

    def _update_playing_buttons(self):
        self.cached_buttons[GameState.PLAYING] = [
            btn for btn in self.cached_buttons[GameState.PLAYING]
            if btn.button_id in ["next_month", "help", "chatbot", "predict"]
        ]
        self._create_action_buttons()
        self.need_button_update = False

    def _create_action_buttons(self):
        header_height = 80
        action_panel_w = 400
        sidebar_w = 350
        main_area_w = SCREEN_WIDTH - sidebar_w - action_panel_w
        view_rect = pygame.Rect(sidebar_w + main_area_w + 10, header_height + 10,
                                action_panel_w - 20, SCREEN_HEIGHT - header_height - 100)
        btn_w = (view_rect.width - 20) // 2
        btn_h = 60
        ay = 10
        fin_actions = [
            ("💰 Invest", 'invest', self.money >= 100, COLOR_PRIMARY, f"Invest in the market | Actions: {self.actions_remaining}/{ACTIONS_PER_MONTH}"),
            ("💵 Save", 'save', self.money >= 100, COLOR_SUCCESS, f"Save to emergency fund | Actions: {self.actions_remaining}/{ACTIONS_PER_MONTH}"),
            ("🏦 Withdraw", 'withdraw', self.emergency_fund > 0, COLOR_WARNING, f"Withdraw from emergency fund | Actions: {self.actions_remaining}/{ACTIONS_PER_MONTH}"),
            ("💳 Pay Debt", 'pay_debt', self.money >= 100 and self.debt > 0, COLOR_DANGER, f"Pay off debt and reduce stress | Actions: {self.actions_remaining}/{ACTIONS_PER_MONTH}"),
        ]
        ay = self._create_financial_dropdown_buttons("FINANCIAL ACTIONS", fin_actions, ay, btn_w, btn_h, view_rect)
        if self.happiness < 80:
            lifestyle_actions = [
                (f"{c.name}\n${c.cost:,.0f}", lambda k=k: self.take_life_choice(k), self.money >= c.cost, COLOR_PANEL,
                 f"😊 {c.name}: +{c.happiness} happiness, {c.stress} stress")
                for k, c in self.life_choices.items() if c.choice_type == 'leisure'
            ]
            if lifestyle_actions:
                ay = self._create_section_buttons("LIFESTYLE", lifestyle_actions, ay, btn_w, btn_h, view_rect)
        util_actions = []
        for k, c in self.life_choices.items():
            if c.choice_type in ['utility', 'education']:
                enabled = self._is_choice_available(k, c)
                col = COLOR_ACCENT if c.choice_type == 'education' else COLOR_PANEL
                tooltip = f"{c.name}: +${c.cost:,.0f} investment in your future!" if c.choice_type == 'education' else f"{c.name}"
                util_actions.append((f"{c.name}\n${c.cost:,.0f}", lambda k=k: self.take_life_choice(k), enabled, col, tooltip))
        if util_actions:
            ay = self._create_section_buttons("GROWTH & ASSETS", util_actions, ay, btn_w, btn_h, view_rect)
        if self.debuffs:
            health_actions = []
            if 'addict' in self.debuffs:
                health_actions.append(("Rehab\n$1.5k", self.treat_addiction, self.money >= 1500, COLOR_DANGER, "Treatment for addiction"))
            if 'unhappy' in self.debuffs or 'distracted' in self.debuffs:
                health_actions.append(("Therapy\n$800", self.seek_therapy, self.money >= 800, COLOR_ACCENT, "Clear debuffs and reduce stress"))
            if health_actions:
                ay = self._create_section_buttons("HEALTH", health_actions, ay, btn_w, btn_h, view_rect)
        self.max_scroll = max(0, ay - view_rect.height + 100)

    def _is_choice_available(self, choice_key, choice):
        if self.money < choice.cost: return False
        if choice_key == 'vehicle' and self.has_vehicle: return False
        if choice_key == 'university' and self.has_university: return False
        if choice_key == 'masters' and (self.has_masters or not self.has_university): return False
        return True

    def _create_section_buttons(self, title, buttons_data, start_y, btn_w, btn_h, view_rect):
        ay = start_y + 50
        for i, b_data in enumerate(buttons_data):
            label, callback, enabled, color, tooltip = b_data
            bx_rel = 0 if i % 2 == 0 else btn_w + 15
            by_rel = ay + (i // 2) * (btn_h + 15)
            screen_x = view_rect.x + bx_rel
            screen_y = view_rect.y + by_rel - self.scroll_offset
            original_y = view_rect.y + by_rel
            is_locked = self.locked_action and self.locked_action['callback'] == callback
            display_label = f"{label}" if is_locked else label
            btn = Button(screen_x, screen_y, btn_w, btn_h, display_label, color,
                         button_id=f"action_{len(self.cached_buttons[GameState.PLAYING])}",
                         tooltip=tooltip + "\n[Right-click to lock/unlock for next month]")
            btn.original_y = original_y
            btn.enabled = enabled and self.actions_remaining > 0
            btn.callback = callback
            btn.visible = True
            btn.lock_data = {'name': label, 'callback': callback}
            self.cached_buttons[GameState.PLAYING].append(btn)
        rows = (len(buttons_data) + 1) // 2
        return ay + rows * (btn_h + 15) + 30

    def _create_financial_dropdown_buttons(self, title, buttons_data, start_y, btn_w, btn_h, view_rect):
        ay = start_y + 50
        for i, b_data in enumerate(buttons_data):
            label, action_type, enabled, color, tooltip = b_data
            bx_rel = 0 if i % 2 == 0 else btn_w + 15
            by_rel = ay + (i // 2) * (btn_h + 15)
            screen_x = view_rect.x + bx_rel
            screen_y = view_rect.y + by_rel - self.scroll_offset
            original_y = view_rect.y + by_rel
            btn = Button(screen_x, screen_y, btn_w, btn_h, label, color,
                         button_id=f"financial_{action_type}", tooltip=tooltip)
            btn.original_y = original_y
            btn.enabled = enabled and self.actions_remaining > 0
            btn.action_type = action_type
            btn.visible = True
            self.cached_buttons[GameState.PLAYING].append(btn)
        rows = (len(buttons_data) + 1) // 2
        return ay + rows * (btn_h + 15) + 30

    def _update_button_positions(self):
        if not self.cached_buttons[GameState.PLAYING]:
            return
        header_height = 80
        action_panel_w = 400
        sidebar_w = 350
        main_area_w = SCREEN_WIDTH - sidebar_w - action_panel_w
        view_rect = pygame.Rect(sidebar_w + main_area_w + 10, header_height + 10,
                                action_panel_w - 20, SCREEN_HEIGHT - header_height - 100)
        for btn in self.cached_buttons[GameState.PLAYING]:
            if btn.button_id not in ["next_month", "help", "chatbot", "predict"]:
                new_y = btn.original_y - self.scroll_offset
                btn.rect.y = new_y
                btn.visible = (new_y + btn.rect.height > view_rect.y and new_y < view_rect.bottom)

    def _load_high_score(self):
        try:
            if os.path.exists('highscore.json'):
                with open('highscore.json', 'r') as f:
                    return json.load(f).get('high_score', 0)
        except Exception:
            pass
        return 0

    def _save_high_score(self):
        try:
            with open('highscore.json', 'w') as f:
                json.dump({'high_score': self.high_score}, f)
        except Exception:
            pass

    def _toggle_help(self):
        self.show_help_panel = not self.show_help_panel
        self.help_scroll_offset = 0

    def start_game(self):
        if not all([self.selected_class, self.selected_education, self.selected_difficulty]):
            return
        cc = self.class_configs[self.selected_class]
        ec = self.education_configs[self.selected_education]
        self.money = cc.starting_money
        self.monthly_income = ec.income
        self.debt = cc.debt + ec.cost
        self.rent = cc.rent
        self.groceries = cc.groceries
        self.transport = cc.transport
        self.investments = 0
        self.emergency_fund = 0
        self.happiness = STARTING_HAPPINESS
        self.stress = 0
        self.current_month = 0
        self.debuffs = []
        self.months_no_income = 0
        self.has_vehicle = False
        self.current_education_level = self.selected_education
        self.has_university = self.selected_education in ['university', 'masters']
        self.has_masters = self.selected_education == 'masters'
        self.game_message = "Welcome to your financial journey! Good luck."
        face, acc_data = self.avatar_creator.get_avatar_composition()
        self.selected_avatar = face
        self.selected_avatar_acc = acc_data
        self.selected_avatar_bg = self.avatar_creator.get_bg_color()
        self.actions_taken_this_month = 0
        self.actions_remaining = ACTIONS_PER_MONTH
        self.locked_action = None
        for goal in self.goals.values():
            goal['completed'] = False

        # Reset data science counters
        self.monthly_log = []
        self.total_investments = 0
        self.total_saved = 0
        self.total_debt_paid = 0
        self.num_leisure = 0
        self.num_risky = 0

        self._init_playing_buttons()
        self.need_button_update = True
        self.state = GameState.PLAYING

    def _tut_prev(self):
        if self.tutorial_step > 0: self.tutorial_step -= 1

    def _tut_next(self):
        if self.tutorial_step < 3:
            self.tutorial_step += 1
        else:
            self.state = GameState.SETUP
            self.tutorial_step = 0

    def _tut_skip(self):
        self.state = GameState.SETUP
        self.tutorial_step = 0

    def next_month(self):
        if self.current_month >= MONTHS_PER_GAME:
            self.end_game(True)
            return
        messages = []
        self._add_particle(SCREEN_WIDTH//2, SCREEN_HEIGHT//2, COLOR_SUCCESS)
        if self.locked_action:
            messages.append(f"🔒 Auto: {self.locked_action['name']}")
            self.locked_action['callback']()
        messages.extend(self._process_income())
        self._process_expenses()
        if self.debt > 0: self.debt *= 1.00417
        if self.investments > 0: self._process_investments()
        if self.emergency_fund > 0: self.emergency_fund *= 1.00167
        self._update_wellbeing(messages)
        self._check_random_events()

        # Append monthly snapshot before incrementing month
        snapshot = {
            'month': self.current_month,
            'money': self.money,
            'debt': self.debt,
            'investments': self.investments,
            'emergency_fund': self.emergency_fund,
            'happiness': self.happiness,
            'stress': self.stress,
        }
        self.monthly_log.append(snapshot)

        self.current_month += 1
        self.actions_taken_this_month = 0
        self.actions_remaining = ACTIONS_PER_MONTH
        self.game_message = " | ".join(messages) if messages else f"Month {self.current_month} complete."
        self.check_goals()
        self.need_button_update = True
        if self.money < -10000:
            self.end_game(False, "Bankrupt! Debt exceeded $10,000 limit.")

    def _process_income(self):
        messages = []
        if self.months_no_income == 0:
            income = self.monthly_income
            if 'distracted' in self.debuffs:
                income *= 0.8
                messages.append("Distracted: -20% income")
                if random.random() < 0.1:
                    self.months_no_income = 2
                    messages.append("Fired due to performance!")
                    self.stress += 30
                    self._add_particle(random.randint(0, SCREEN_WIDTH), 100, COLOR_DANGER)
            self.money += income
            self._add_particle(random.randint(0, SCREEN_WIDTH), 100, COLOR_SUCCESS)
        else:
            self.months_no_income -= 1
            messages.append(f"No income ({self.months_no_income} months left)")
        return messages

    def _process_expenses(self):
        self.money -= self.rent + self.groceries + self.transport

    def _process_investments(self):
        diff = self.difficulty_configs[self.selected_difficulty]
        monthly_return = (random.random() * 0.25 - 0.10) / 12 * diff.market_volatility
        self.investments *= (1 + monthly_return)

    def _update_wellbeing(self, messages):
        self.stress = max(0, self.stress - 2)
        dti = self.debt / (self.monthly_income * 12) if self.monthly_income > 0 else 0
        if dti > 0.5: self.stress += 5
        if self.emergency_fund < self.monthly_income * 3: self.stress += 2
        self.happiness = max(0, self.happiness - 3)
        if 'unhappy' in self.debuffs: messages.append("You are unhappy!")
        if self.stress >= BURNOUT_STRESS or self.happiness <= BURNOUT_HAPPINESS: self._trigger_burnout()
        self.stress = min(100, self.stress)
        self.happiness = min(100, self.happiness)

    def _trigger_burnout(self):
        self.trigger_event(EmergencyEvent("🔥 BURNOUT!", "You've reached your breaking point. Forced medical leave.", cost=2000, months_no_income=2))
        self.stress = 50
        if 'unhappy' not in self.debuffs: self.debuffs.append('unhappy')

    def _check_random_events(self):
        diff = self.difficulty_configs[self.selected_difficulty]
        if random.random() < diff.emergency_chance:
            self.trigger_event(random.choice(self.emergency_events))
        debuff_chance = 0.5 - (self.happiness / 100) * 0.4
        if random.random() < debuff_chance and 'distracted' not in self.debuffs:
            self.debuffs.append('distracted')
            self.stress += 10

    def trigger_event(self, event):
        self.current_event = event
        self.show_event_modal = True

    def handle_event_close(self):
        if self.current_event:
            if self.current_event.cost > 0:
                self.money -= self.current_event.cost
                self._add_particle(SCREEN_WIDTH//2, SCREEN_HEIGHT//2, COLOR_DANGER)
            if self.current_event.stress_increase > 0:
                self.stress = min(100, self.stress + self.current_event.stress_increase)
            if self.current_event.months_no_income > 0:
                self.months_no_income = self.current_event.months_no_income
            if self.current_event.investment_loss > 0:
                self.investments *= (1 - self.current_event.investment_loss)
        self.show_event_modal = False
        self.current_event = None
        self.need_button_update = True

    def take_life_choice(self, choice_key):
        if self.actions_remaining <= 0:
            self.game_message = f"⚠️ No actions left! ({self.actions_taken_this_month}/{ACTIONS_PER_MONTH})"
            return
        choice = self.life_choices[choice_key]
        if not self._validate_life_choice(choice_key, choice): return
        self.money -= choice.cost
        self.actions_taken_this_month += 1
        self.actions_remaining -= 1
        if choice.happiness > 0:
            self._add_particle(self.screen.get_width()//2, self.screen.get_height()//2, COLOR_SUCCESS)

        # Update counters for statistics
        if choice.choice_type == 'leisure':
            self.num_leisure += 1
        elif choice.choice_type == 'risky':
            self.num_risky += 1

        if choice.choice_type == 'education':
            self._handle_education_upgrade(choice_key, choice)
            return
        self.happiness = min(100, self.happiness + choice.happiness)
        self.stress = max(0, self.stress + choice.stress)
        if choice.choice_type == 'risky':
            if self._handle_risky_choice(choice_key, choice): return
        if choice_key == 'vehicle': self.has_vehicle = True
        self.game_message = f"{choice.name}: Happiness +{choice.happiness:.0f} | Actions: {self.actions_remaining}/{ACTIONS_PER_MONTH}"
        self.need_button_update = True

    def _validate_life_choice(self, choice_key, choice):
        if choice.one_time and choice_key == 'vehicle' and self.has_vehicle:
            self.game_message = "You already own a vehicle!"; return False
        if choice_key == 'university' and self.has_university:
            self.game_message = "You already have a degree!"; return False
        if choice_key == 'masters':
            if self.has_masters: self.game_message = "Already have a master's!"; return False
            if not self.has_university: self.game_message = "Need University degree first!"; return False
        if self.money < choice.cost: self.game_message = "Not enough money!"; return False
        return True

    def _handle_education_upgrade(self, choice_key, choice):
        if choice_key == 'university':
            self.monthly_income += 1500; self.has_university = True; self.current_education_level = 'university'
            self.debt += choice.cost; self.money += choice.cost
            self.happiness = min(100, self.happiness + 10); self.stress = min(100, self.stress + 15)
            self.game_message = "🎓 Degree Earned! Income +$1500/mo (Added to debt)"
        elif choice_key == 'masters':
            self.monthly_income += 1000; self.has_masters = True; self.current_education_level = 'masters'
            self.debt += choice.cost; self.money += choice.cost
            self.happiness = min(100, self.happiness + 15); self.stress = min(100, self.stress + 20)
            self.game_message = "🎓 Masters Earned! Income +$1000/mo (Added to debt)"
        self.need_button_update = True

    def _handle_risky_choice(self, choice_key, choice):
        if choice_key == 'gambling' and random.random() < choice.win_chance:
            self.money += choice.win_amount
            self.game_message = f"You won ${choice.win_amount:.0f}!"
            self._add_particle(self.screen.get_width()//2, self.screen.get_height()//2, COLOR_WARNING)
            self.need_button_update = True; return True
        if choice.debuff_chance > 0 and random.random() < choice.debuff_chance:
            if choice.debuff not in self.debuffs:
                self.debuffs.append(choice.debuff)
                self.game_message = f"Addicted to {choice.name}!"
                self._add_particle(self.screen.get_width()//2, self.screen.get_height()//2, COLOR_DANGER)
                self.need_button_update = True; return True
        return False

    def invest_money(self, amount):
        if self.actions_remaining <= 0: self.game_message = f"No actions left!"; return
        if self.money >= amount:
            self.money -= amount; self.investments += amount
            self.total_investments += amount   # for statistics
            self.actions_taken_this_month += 1; self.actions_remaining -= 1
            self.game_message = f"Invested ${amount:.0f} | Actions: {self.actions_remaining}/{ACTIONS_PER_MONTH}"
            self._add_particle(self.screen.get_width()//2, self.screen.get_height()//2, COLOR_PRIMARY)
            self.need_button_update = True

    def withdraw_investment(self, amount):
        if self.actions_remaining <= 0: self.game_message = f"⚠️ No actions left!"; return
        withdrawal = min(amount, self.investments)
        if withdrawal > 0:
            self.investments -= withdrawal; self.money += withdrawal
            self.actions_taken_this_month += 1; self.actions_remaining -= 1
            self.game_message = f"Withdrew ${withdrawal:.0f} | Actions: {self.actions_remaining}/{ACTIONS_PER_MONTH}"
            self.need_button_update = True
        else:
            self.game_message = "No investments!"

    def add_to_emergency_fund(self, amount):
        if self.actions_remaining <= 0: self.game_message = f"⚠️ No actions left!"; return
        if self.money >= amount:
            self.money -= amount; self.emergency_fund += amount
            self.total_saved += amount   # for statistics
            self.actions_taken_this_month += 1; self.actions_remaining -= 1
            self.game_message = f"Saved ${amount:.0f} | Actions: {self.actions_remaining}/{ACTIONS_PER_MONTH}"
            self.need_button_update = True

    def pay_off_debt(self, amount):
        if self.actions_remaining <= 0: self.game_message = f"No actions left!"; return
        payment = min(amount, self.debt, self.money)
        if payment > 0:
            self.money -= payment; self.debt -= payment; self.stress = max(0, self.stress - 5)
            self.total_debt_paid += payment   # for statistics
            self.actions_taken_this_month += 1; self.actions_remaining -= 1
            self.game_message = f"💳 Paid ${payment:.0f} debt | Actions: {self.actions_remaining}/{ACTIONS_PER_MONTH}"
            self._add_particle(self.screen.get_width()//2, self.screen.get_height()//2, COLOR_SUCCESS)
            self.need_button_update = True

    def close_dropdown(self):
        self.active_dropdown = None; self.dropdown_hover = False

    def open_custom_input(self, action_type):
        self.show_custom_input = True; self.custom_input_type = action_type
        self.custom_input_text = ""; self.close_dropdown()

    def execute_financial_action(self, action_type, amount):
        if action_type == 'invest':
            self.invest_money(amount)
        elif action_type == 'save':
            if self.money >= amount:
                self.money -= amount; self.emergency_fund += amount
                self.total_saved += amount   # for statistics
                self.actions_taken_this_month += 1; self.actions_remaining -= 1
                self.game_message = f"💵 Saved ${amount:.0f} | Actions: {self.actions_remaining}/{ACTIONS_PER_MONTH}"
                self.need_button_update = True
            else:
                self.game_message = "Not enough money"
        elif action_type == 'withdraw':
            self._withdraw_emergency(amount)
        elif action_type == 'pay_debt':
            self.pay_off_debt(amount)
        self.close_dropdown()

    def _withdraw_emergency(self, amount):
        if self.actions_remaining <= 0: self.game_message = f"No actions left!"; return
        withdrawal = min(amount, self.emergency_fund)
        if withdrawal > 0:
            self.emergency_fund -= withdrawal; self.money += withdrawal
            self.actions_taken_this_month += 1; self.actions_remaining -= 1
            self.game_message = f"Withdrew ${withdrawal:.0f} | Actions: {self.actions_remaining}/{ACTIONS_PER_MONTH}"
            self.need_button_update = True

    def handle_custom_input_submit(self):
        try:
            amount = float(self.custom_input_text)
            if amount <= 0 or amount > 100000:
                self.game_message = "Amount must be between $1 and $100,000"; return
            self.execute_financial_action(self.custom_input_type, amount)
            self.show_custom_input = False; self.custom_input_text = ""
        except ValueError:
            self.game_message = "Invalid amount"

    def treat_addiction(self):
        if self.actions_remaining <= 0: self.game_message = f"No actions left!"; return
        if self.money < 1500: self.game_message = "Need $1500 for treatment"; return
        self.money -= 1500; self.actions_taken_this_month += 1; self.actions_remaining -= 1
        if random.random() < self.happiness / 100:
            self.debuffs = [d for d in self.debuffs if d != 'addict']
            self.happiness = min(100, self.happiness + 10)
            self.game_message = f"Addiction cured! | Actions: {self.actions_remaining}/{ACTIONS_PER_MONTH}"
            self._add_particle(self.screen.get_width()//2, self.screen.get_height()//2, COLOR_SUCCESS)
        else:
            self.game_message = f"Treatment failed. | Actions: {self.actions_remaining}/{ACTIONS_PER_MONTH}"
        self.need_button_update = True

    def seek_therapy(self):
        if self.actions_remaining <= 0: self.game_message = f"No actions left!"; return
        if self.money < 800: self.game_message = "Need $800 for therapy"; return
        self.money -= 800
        self.debuffs = [d for d in self.debuffs if d not in ['unhappy', 'distracted']]
        self.stress = max(0, self.stress - 20); self.happiness = min(100, self.happiness + 15)
        self.actions_taken_this_month += 1; self.actions_remaining -= 1
        self.game_message = f"Therapy successful! | Actions: {self.actions_remaining}/{ACTIONS_PER_MONTH}"
        self._add_particle(self.screen.get_width()//2, self.screen.get_height()//2, COLOR_ACCENT)
        self.need_button_update = True

    def check_goals(self):
        nw = self.money + self.investments + self.emergency_fund - self.debt
        if nw >= self.goals['netWorth']['target']: self.goals['netWorth']['completed'] = True
        if self.emergency_fund >= self.goals['emergencyFund']['target']: self.goals['emergencyFund']['completed'] = True
        if self.debt <= 0: self.goals['debtFree']['completed'] = True
        if self.happiness >= self.goals['happiness']['target']: self.goals['happiness']['completed'] = True

    def calculate_score(self):
        nw = self.money + self.investments + self.emergency_fund - self.debt
        goal_bonus = sum(1 for g in self.goals.values() if g['completed']) * 5000
        return max(0, int(nw + goal_bonus + self.happiness * 100 + self.current_month * 500))

    def end_game(self, completed, reason=''):
        score = self.calculate_score()
        if score > self.high_score:
            self.high_score = score
            self._save_high_score()
        self.game_message = reason or ('Game completed!' if completed else 'Game over!')
        self._save_game_summary()          # save for optional later use
        self._save_goal_training_data()    # save for goal prediction training
        self.state = GameState.GAME_OVER

    def _draw_text(self, text, font, color, x, y, center=False, shadow=False, glow=False):
        if shadow:
            ss = font.render(text, True, (0, 0, 0))
            sr = ss.get_rect()
            sr.topleft = (x+3, y+3) if not center else (x+3-ss.get_width()//2, y+3-ss.get_height()//2)
            self.screen.blit(ss, sr)
        if glow:
            for _ in range(1, 4):
                gs = font.render(text, True, color[:3])
                gr = gs.get_rect(center=(x, y)) if center else gs.get_rect(topleft=(x, y))
                self.screen.blit(gs, gr)
        ts = font.render(text, True, color)
        tr = ts.get_rect(center=(x, y)) if center else ts.get_rect(topleft=(x, y))
        self.screen.blit(ts, tr)

    def _draw_progress_bar(self, x, y, width, height, percentage, color, bg_color=COLOR_PANEL, glow=False):
        for i in range(height):
            pygame.draw.line(self.screen, bg_color, (x, y+i), (x+width, y+i))
        fw = int(width * max(0, min(100, percentage)) / 100)
        if fw > 0:
            for i in range(height):
                ratio = i / height
                fc = (int(color[0]*(1-ratio*0.3)), int(color[1]*(1-ratio*0.3)), int(color[2]*(1-ratio*0.3)))
                pygame.draw.line(self.screen, fc, (x, y+i), (x+fw, y+i))
        pygame.draw.rect(self.screen, COLOR_BORDER, (x, y, width, height), 1, border_radius=height//2)

    def _draw_gradient_background(self):
        t = pygame.time.get_ticks() * 0.0005
        for y in range(SCREEN_HEIGHT):
            r = int(15 + math.sin(t + y * 0.01) * 5)
            g = int(23 + math.cos(t + y * 0.01) * 5)
            b = int(42 + math.sin(t * 0.5 + y * 0.01) * 5)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))

    def _wrap_text(self, text, font, max_width):
        words = text.split()
        lines, current_line = [], []
        for word in words:
            current_line.append(word)
            if font.size(' '.join(current_line))[0] > max_width:
                current_line.pop()
                if current_line: lines.append(' '.join(current_line))
                current_line = [word]
        if current_line: lines.append(' '.join(current_line))
        return lines

    def _draw_avatar_creator_modal(self, events):
        ac = self.avatar_creator
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        mw, mh = 820, 700
        mx = (SCREEN_WIDTH - mw) // 2
        my = (SCREEN_HEIGHT - mh) // 2
        pygame.draw.rect(self.screen, (12, 20, 35), (mx, my, mw, mh), border_radius=24)
        pygame.draw.rect(self.screen, COLOR_ACCENT, (mx, my, mw, mh), 3, border_radius=24)
        pygame.draw.rect(self.screen, COLOR_PANEL, (mx, my, mw, 64), border_top_left_radius=24, border_top_right_radius=24)
        self._draw_text("✨ CUSTOM AVATAR CREATOR", self.font_medium, COLOR_ACCENT, mx + mw // 2, my + 32, center=True, glow=True)
        tab_y = my + 76
        for i, (tab_id, tab_label) in enumerate([('builder', 'Build Your Own'), ('quick', 'Quick Pick')]):
            tx = mx + 30 + i * 390
            tab_rect = pygame.Rect(tx, tab_y, 370, 40)
            is_active = ac.tab == tab_id
            bg = COLOR_ACCENT if is_active else COLOR_PANEL_HOVER
            pygame.draw.rect(self.screen, bg, tab_rect, border_radius=10)
            pygame.draw.rect(self.screen, COLOR_ACCENT if is_active else COLOR_BORDER, tab_rect, 2, border_radius=10)
            lf = pygame.font.SysFont("Arial", 17, bold=True)
            ls = lf.render(tab_label, True, COLOR_BG if is_active else COLOR_TEXT)
            self.screen.blit(ls, ls.get_rect(center=tab_rect.center))
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if tab_rect.collidepoint(event.pos):
                        ac.tab = tab_id
                        ac.reset_custom()
        content_y = tab_y + 52
        mouse_pos = pygame.mouse.get_pos()
        if ac.tab == 'builder':
            self._draw_avatar_builder_tab(mx, my, mw, mh, content_y, ac, events, mouse_pos)
        else:
            self._draw_avatar_quickpick_tab(mx, my, mw, mh, content_y, ac, events, mouse_pos)
        prev_x = mx + mw - 185
        prev_y = content_y + 10
        prev_w, prev_h = 165, 190
        pygame.draw.rect(self.screen, COLOR_PANEL, (prev_x, prev_y, prev_w, prev_h), border_radius=18)
        bg_col = ac.get_bg_color()
        pygame.draw.rect(self.screen, bg_col, (prev_x + 4, prev_y + 4, prev_w - 8, prev_h - 8), border_radius=14)
        face, acc_data = ac.get_avatar_composition()
        draw_composite_avatar(self.screen, face, acc_data, prev_x + prev_w // 2, prev_y + 80, 64)
        lf2 = pygame.font.SysFont("Arial", 13, bold=True)
        self.screen.blit(lf2.render("PREVIEW", True, COLOR_TEXT_DIM),
                         lf2.render("PREVIEW", True, COLOR_TEXT_DIM).get_rect(center=(prev_x + prev_w // 2, prev_y + prev_h - 18)))
        pygame.draw.rect(self.screen, COLOR_ACCENT, (prev_x, prev_y, prev_w, prev_h), 2, border_radius=18)
        btn_y = my + mh - 68
        confirm_rect = pygame.Rect(mx + mw // 2 - 230, btn_y, 210, 48)
        cancel_rect  = pygame.Rect(mx + mw // 2 + 20,  btn_y, 210, 48)
        c_hov = confirm_rect.collidepoint(mouse_pos)
        x_hov = cancel_rect.collidepoint(mouse_pos)
        pygame.draw.rect(self.screen, (COLOR_SUCCESS if not c_hov else (50, 255, 180)), confirm_rect, border_radius=12)
        pygame.draw.rect(self.screen, COLOR_PANEL_HOVER if not x_hov else (60, 70, 90), cancel_rect, border_radius=12)
        pygame.draw.rect(self.screen, COLOR_SUCCESS, confirm_rect, 2, border_radius=12)
        pygame.draw.rect(self.screen, COLOR_BORDER, cancel_rect, 2, border_radius=12)
        cf = pygame.font.SysFont("Arial", 18, bold=True)
        self.screen.blit(cf.render("✓  Use This Avatar", True, COLOR_BG), cf.render("✓  Use This Avatar", True, COLOR_BG).get_rect(center=confirm_rect.center))
        self.screen.blit(cf.render("✗  Cancel", True, COLOR_TEXT), cf.render("✗  Cancel", True, COLOR_TEXT).get_rect(center=cancel_rect.center))
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if confirm_rect.collidepoint(event.pos):
                    ac.visible = False
                    self._add_particle(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, COLOR_ACCENT)
                elif cancel_rect.collidepoint(event.pos):
                    ac.visible = False

    def _draw_avatar_builder_tab(self, mx, my, mw, mh, content_y, ac, events, mouse_pos):
        section_x = mx + 20
        row_y = content_y + 5
        self._draw_text("FACE", self.font_tiny, COLOR_ACCENT, section_x, row_y)
        row_y += 24
        tile = 54
        gap  = 8
        for i, (em, label) in enumerate(AVATAR_FACES):
            cols = 10
            col = i % cols
            r   = i // cols
            tx = section_x + col * (tile + gap)
            ty = row_y + r * (tile + gap)
            tr = pygame.Rect(tx, ty, tile, tile)
            is_sel = (i == ac.selected_face_idx) and not ac.custom_emoji_text
            is_hov = tr.collidepoint(mouse_pos)
            if is_sel:
                halo = pygame.Surface((tile + 8, tile + 8), pygame.SRCALPHA)
                pygame.draw.rect(halo, (*COLOR_PRIMARY, 60), (0, 0, tile + 8, tile + 8), border_radius=12)
                self.screen.blit(halo, (tx - 4, ty - 4))
                pygame.draw.rect(self.screen, COLOR_PRIMARY, tr, border_radius=10)
            elif is_hov:
                pygame.draw.rect(self.screen, COLOR_PANEL_HOVER, tr, border_radius=10)
            else:
                pygame.draw.rect(self.screen, (25, 38, 58), tr, border_radius=10)
            pygame.draw.rect(self.screen, (COLOR_PRIMARY if is_sel else (COLOR_ACCENT if is_hov else COLOR_BORDER)), tr, 2, border_radius=10)
            ef = pygame.font.SysFont("Segoe UI Emoji", 26)
            es = ef.render(em, True, COLOR_TEXT)
            self.screen.blit(es, es.get_rect(center=tr.center))
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and tr.collidepoint(event.pos):
                    ac.selected_face_idx = i
                    ac.custom_emoji_text = ""
        rows_face = (len(AVATAR_FACES) + 9) // 10
        row_y += rows_face * (tile + gap) + 14
        self._draw_text("ACCESSORY / OVERLAY", self.font_tiny, COLOR_ACCENT, section_x, row_y)
        row_y += 24
        for i, (em, label, _) in enumerate(AVATAR_ACCESSORIES):
            cols = 10
            col = i % cols
            r   = i // cols
            tx = section_x + col * (tile + gap)
            ty = row_y + r * (tile + gap)
            tr = pygame.Rect(tx, ty, tile, tile)
            is_sel = (i == ac.selected_acc_idx) and not ac.custom_emoji_text
            is_hov = tr.collidepoint(mouse_pos)
            if is_sel:
                pygame.draw.rect(self.screen, COLOR_ACCENT, tr, border_radius=10)
            elif is_hov:
                pygame.draw.rect(self.screen, COLOR_PANEL_HOVER, tr, border_radius=10)
            else:
                pygame.draw.rect(self.screen, (25, 38, 58), tr, border_radius=10)
            pygame.draw.rect(self.screen, (COLOR_ACCENT if is_sel else (COLOR_PRIMARY if is_hov else COLOR_BORDER)), tr, 2, border_radius=10)
            ef = pygame.font.SysFont("Segoe UI Emoji", 26)
            disp = em if em else "∅"
            es = ef.render(disp, True, COLOR_TEXT)
            self.screen.blit(es, es.get_rect(center=tr.center))
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and tr.collidepoint(event.pos):
                    ac.selected_acc_idx = i
                    ac.custom_emoji_text = ""
        rows_acc = (len(AVATAR_ACCESSORIES) + 9) // 10
        row_y += rows_acc * (tile + gap) + 14
        self._draw_text("AVATAR BACKGROUND COLOR", self.font_tiny, COLOR_ACCENT, section_x, row_y)
        row_y += 24
        swatch = 36
        for i, (col, name) in enumerate(AVATAR_BG_COLORS):
            sx = section_x + i * (swatch + 6)
            sr = pygame.Rect(sx, row_y, swatch, swatch)
            is_sel = (i == ac.selected_bg_idx)
            pygame.draw.rect(self.screen, col, sr, border_radius=8)
            if is_sel:
                pygame.draw.rect(self.screen, COLOR_TEXT, sr, 3, border_radius=8)
                pygame.draw.circle(self.screen, COLOR_TEXT, sr.center, 5)
            elif sr.collidepoint(mouse_pos):
                pygame.draw.rect(self.screen, COLOR_TEXT, sr, 2, border_radius=8)
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and sr.collidepoint(event.pos):
                    ac.selected_bg_idx = i
        row_y += swatch + 20
        self._draw_text("OR TYPE YOUR OWN EMOJI (overrides selections above):", self.font_tiny, COLOR_WARNING, section_x, row_y)
        row_y += 24
        input_rect = pygame.Rect(section_x, row_y, 260, 44)
        is_active = ac.custom_emoji_input_active
        pygame.draw.rect(self.screen, COLOR_PANEL, input_rect, border_radius=10)
        pygame.draw.rect(self.screen, (COLOR_WARNING if is_active else COLOR_BORDER), input_rect, 2, border_radius=10)
        disp_text = ac.custom_emoji_text if ac.custom_emoji_text else "e.g. 🦄 or 🤖"
        cursor = "|" if (is_active and pygame.time.get_ticks() % 1000 < 500) else " "
        txt_col = COLOR_TEXT if ac.custom_emoji_text else COLOR_TEXT_DIM
        ef2 = pygame.font.SysFont("Segoe UI Emoji", 22)
        rendered = ef2.render((ac.custom_emoji_text + cursor) if is_active else disp_text, True, txt_col)
        self.screen.blit(rendered, (input_rect.x + 10, input_rect.y + 10))
        clr_rect = pygame.Rect(input_rect.right + 10, row_y + 4, 70, 36)
        clr_hov = clr_rect.collidepoint(mouse_pos)
        pygame.draw.rect(self.screen, (COLOR_DANGER if clr_hov else COLOR_PANEL_HOVER), clr_rect, border_radius=8)
        pygame.draw.rect(self.screen, COLOR_DANGER, clr_rect, 1, border_radius=8)
        cf2 = pygame.font.SysFont("Arial", 14, bold=True)
        self.screen.blit(cf2.render("Clear", True, COLOR_TEXT), cf2.render("Clear", True, COLOR_TEXT).get_rect(center=clr_rect.center))
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if input_rect.collidepoint(event.pos):
                    ac.custom_emoji_input_active = True
                elif clr_rect.collidepoint(event.pos):
                    ac.custom_emoji_text = ""
                    ac.custom_emoji_input_active = False
                else:
                    ac.custom_emoji_input_active = False
            if event.type == pygame.KEYDOWN and ac.custom_emoji_input_active:
                if event.key == pygame.K_BACKSPACE:
                    if ac.custom_emoji_text:
                        ac.custom_emoji_text = ac.custom_emoji_text[:-1]
                elif event.key == pygame.K_ESCAPE:
                    ac.custom_emoji_input_active = False
                elif event.key == pygame.K_RETURN:
                    ac.custom_emoji_input_active = False
                else:
                    if len(ac.custom_emoji_text) < 6:
                        ac.custom_emoji_text += event.unicode

    def _draw_avatar_quickpick_tab(self, mx, my, mw, mh, content_y, ac, events, mouse_pos):
        section_x = mx + 20
        tile_size = 72
        tile_gap  = 14
        cols = 6
        start_y = content_y + 18
        self._draw_text("CHOOSE A PRESET AVATAR", self.font_small, COLOR_ACCENT, section_x + 10, start_y - 8)
        for i, av in enumerate(AVATARS):
            col = i % cols
            row = i // cols
            tx = section_x + col * (tile_size + tile_gap)
            ty = start_y + 30 + row * (tile_size + tile_gap + 20)
            tile_rect = pygame.Rect(tx, ty, tile_size, tile_size)
            is_selected = (ac.tab == 'quick' and ac.selected_face_idx == i and not ac.custom_emoji_text)
            is_hovered  = tile_rect.collidepoint(mouse_pos)
            if is_selected:
                halo = pygame.Surface((tile_size + 12, tile_size + 12), pygame.SRCALPHA)
                pygame.draw.rect(halo, (*COLOR_PRIMARY, 55), (0, 0, tile_size + 12, tile_size + 12), border_radius=14)
                self.screen.blit(halo, (tx - 6, ty - 6))
                pygame.draw.rect(self.screen, COLOR_PRIMARY, tile_rect, border_radius=12)
            elif is_hovered:
                pygame.draw.rect(self.screen, COLOR_PANEL_HOVER, tile_rect, border_radius=12)
            else:
                pygame.draw.rect(self.screen, (28, 42, 62), tile_rect, border_radius=12)
            border_col = COLOR_PRIMARY if is_selected else (COLOR_ACCENT if is_hovered else COLOR_BORDER)
            pygame.draw.rect(self.screen, border_col, tile_rect, 2 if not is_selected else 3, border_radius=12)
            ef = pygame.font.SysFont("Segoe UI Emoji", 34)
            es = ef.render(av["emoji"], True, COLOR_TEXT)
            self.screen.blit(es, es.get_rect(center=(tx + tile_size // 2, ty + tile_size // 2 - 8)))
            lf = pygame.font.SysFont("Arial", 11, bold=True)
            ls = lf.render(av["label"], True, COLOR_BG if is_selected else COLOR_TEXT_DIM)
            self.screen.blit(ls, ls.get_rect(center=(tx + tile_size // 2, ty + tile_size - 10)))
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if tile_rect.collidepoint(event.pos):
                        ac.custom_emoji_text = av["emoji"]
                        ac.selected_face_idx = i
                        self._add_particle(tx + tile_size // 2, ty + tile_size // 2, COLOR_ACCENT)

    def _draw_setup(self, events):
        self._draw_gradient_background()
        self._draw_text("CHARACTER SETUP", self.font_large, COLOR_PRIMARY, SCREEN_WIDTH//2, 40, center=True, glow=True)
        section_width = 380
        gap = 35
        top_row_total = 3 * section_width + 2 * gap
        start_x = (SCREEN_WIDTH - top_row_total) // 2
        self._draw_class_selection(start_x, section_width, events)
        self._draw_education_selection(start_x + section_width + gap, section_width, events)
        self._draw_difficulty_selection(start_x + (section_width + gap) * 2, section_width, events)
        self._draw_avatar_row(events)
        self.cached_buttons[GameState.SETUP][0].enabled = all(
            [self.selected_class, self.selected_education, self.selected_difficulty])
        for btn in self.cached_buttons[GameState.SETUP]:
            font = self.font_small if btn.button_id == "setup_back" else self.font_medium
            btn.draw(self.screen, font)
        for event in events:
            for btn in self.cached_buttons[GameState.SETUP]:
                btn.handle_event(event)

    def _draw_avatar_row(self, events):
        row_y   = 680
        panel_x = 60
        panel_w = SCREEN_WIDTH - 120
        panel_h = 120
        pygame.draw.rect(self.screen, COLOR_PANEL, (panel_x, row_y, panel_w, panel_h), border_radius=16)
        pygame.draw.rect(self.screen, COLOR_ACCENT, (panel_x, row_y, panel_w, panel_h), 2, border_radius=16)
        self._draw_text("YOUR AVATAR", self.font_small, COLOR_ACCENT, panel_x + 22, row_y + 14)
        face, acc_data = self.avatar_creator.get_avatar_composition()
        bg_col = self.avatar_creator.get_bg_color()
        cx, cy = panel_x + 58, row_y + 75
        pygame.draw.circle(self.screen, bg_col, (cx, cy), 35)
        pygame.draw.circle(self.screen, COLOR_ACCENT, (cx, cy), 37, 2)
        draw_composite_avatar(self.screen, face, acc_data, cx, cy, 36)
        desc_f = pygame.font.SysFont("Arial", 15)
        desc_s = desc_f.render(f"Click 'Customise Avatar' to personalise your character", True, COLOR_TEXT_DIM)
        self.screen.blit(desc_s, (panel_x + 115, row_y + 60))
        btn_rect = pygame.Rect(panel_x + panel_w - 250, row_y + 22, 230, 56)
        mouse_pos = pygame.mouse.get_pos()
        is_hov = btn_rect.collidepoint(mouse_pos)
        for i in range(btn_rect.height):
            ratio = i / btn_rect.height
            c = (
                int(COLOR_GRADIENT_START[0] * (1-ratio) + COLOR_GRADIENT_END[0] * ratio),
                int(COLOR_GRADIENT_START[1] * (1-ratio) + COLOR_GRADIENT_END[1] * ratio),
                int(COLOR_GRADIENT_START[2] * (1-ratio) + COLOR_GRADIENT_END[2] * ratio),
            )
            if is_hov:
                c = (min(c[0]+40, 255), min(c[1]+40, 255), min(c[2]+40, 255))
            pygame.draw.line(self.screen, c, (btn_rect.x, btn_rect.y + i), (btn_rect.right, btn_rect.y + i))
        pygame.draw.rect(self.screen, COLOR_PRIMARY if is_hov else COLOR_ACCENT, btn_rect, 2, border_radius=12)
        bf = pygame.font.SysFont("Arial", 18, bold=True)
        bs = bf.render("Customise Avatar", True, COLOR_BG)
        self.screen.blit(bs, bs.get_rect(center=btn_rect.center))
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if btn_rect.collidepoint(event.pos):
                    self.avatar_creator.visible = True

    def _draw_title(self, events):
        self._draw_gradient_background()
        t = pygame.time.get_ticks() * 0.001
        for i in range(3):
            pygame.draw.circle(self.screen, COLOR_PRIMARY[:3],
                               (SCREEN_WIDTH//2, SCREEN_HEIGHT//2),
                               400 + int(math.sin(t+i)*50), 2)
        self._draw_text("FINANCE", self.font_xl, COLOR_PRIMARY, SCREEN_WIDTH//2, 200, center=True, shadow=True, glow=True)
        self._draw_text("QUEST", self.font_xl, COLOR_ACCENT, SCREEN_WIDTH//2, 270, center=True, shadow=True, glow=True)
        self._draw_text("Master Your Financial Future", self.font_medium, COLOR_TEXT_DIM, SCREEN_WIDTH//2, 360, center=True)
        if self.high_score > 0:
            pygame.draw.rect(self.screen, COLOR_PANEL, (SCREEN_WIDTH//2-200, 400, 400, 60), border_radius=15)
            pygame.draw.rect(self.screen, COLOR_WARNING, (SCREEN_WIDTH//2-200, 400, 400, 60), 2, border_radius=15)
            self._draw_text(f"High Score: {self.high_score:,}", self.font_medium, COLOR_WARNING, SCREEN_WIDTH//2, 430, center=True)
        for btn in self.cached_buttons[GameState.TITLE]:
            btn.draw(self.screen, self.font_medium)
        for event in events:
            for btn in self.cached_buttons[GameState.TITLE]:
                btn.handle_event(event)

    def _draw_tutorial(self, events):
        self._draw_gradient_background()
        tutorials = [
            ("Welcome to FinanceQuest!", "Simulate 2 years of financial decisions. Build wealth, maintain well-being, and achieve your goals."),
            ("Core Mechanics", "Every turn is one month. Manage income, expenses, and investments. Watch your Happiness and Stress!"),
            ("Well-Being System", "High Stress causes Burnout. Low Happiness causes Debuffs. Keep a balance to succeed."),
            ("Winning", "Complete the 4 main goals to earn bonus points. Your final score depends on Net Worth and happiness.")
        ]
        title, content = tutorials[self.tutorial_step]
        panel_rect = pygame.Rect(200, 150, SCREEN_WIDTH-400, 500)
        pygame.draw.rect(self.screen, COLOR_PANEL, panel_rect, border_radius=20)
        pygame.draw.rect(self.screen, COLOR_PRIMARY, panel_rect, 3, border_radius=20)
        pygame.draw.rect(self.screen, COLOR_PANEL_HOVER, (200, 150, SCREEN_WIDTH-400, 80),
                         border_top_left_radius=20, border_top_right_radius=20)
        self._draw_text(f"📘 Tutorial {self.tutorial_step+1}/{len(tutorials)}", self.font_medium, COLOR_ACCENT, SCREEN_WIDTH//2, 190, center=True)
        self._draw_text(title, self.font_large, COLOR_PRIMARY, SCREEN_WIDTH//2, 280, center=True, glow=True)
        y = 360
        for line in self._wrap_text(content, self.font_medium, panel_rect.width-100):
            self._draw_text(line, self.font_medium, COLOR_TEXT, SCREEN_WIDTH//2, y, center=True)
            y += 45
        self.cached_buttons[GameState.TUTORIAL][1].update_text("Next" if self.tutorial_step < 3 else "Start Setup")
        self.cached_buttons[GameState.TUTORIAL][0].enabled = self.tutorial_step > 0
        for btn in self.cached_buttons[GameState.TUTORIAL]:
            btn.draw(self.screen, self.font_small)
        for event in events:
            for btn in self.cached_buttons[GameState.TUTORIAL]:
                btn.handle_event(event)

    def _draw_class_selection(self, x, width, events):
        y = 90
        self._draw_text("SOCIAL CLASS", self.font_small, COLOR_ACCENT, x + width//2, y, center=True)
        y += 40
        for key, config in self.class_configs.items():
            color = COLOR_PRIMARY if self.selected_class == key else COLOR_PANEL
            text_color = COLOR_BG if self.selected_class == key else COLOR_TEXT
            btn = Button(x, y, width, 115, f"{config.avatar_emoji} {config.name}\n ${config.starting_money:,.0f}\n ${config.debt:,.0f}",
                         color, text_color, button_id=f"class_{key}", tooltip=config.description)
            btn.draw(self.screen, self.font_small)
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if btn.rect.collidepoint(event.pos):
                        self.selected_class = key
                        self._add_particle(event.pos[0], event.pos[1], COLOR_PRIMARY)
            y += 125

    def _draw_education_selection(self, x, width, events):
        y = 90
        self._draw_text("EDUCATION", self.font_small, COLOR_ACCENT, x + width//2, y, center=True)
        y += 40
        for key, config in self.education_configs.items():
            color = COLOR_PRIMARY if self.selected_education == key else COLOR_PANEL
            text_color = COLOR_BG if self.selected_education == key else COLOR_TEXT
            cost_text = "Free" if config.cost == 0 else f"${config.cost:,}"
            btn = Button(x, y, width, 115, f"{config.name}\n ${config.income:,.0f}/mo\n{cost_text}",
                         color, text_color, button_id=f"edu_{key}", tooltip=config.description)
            btn.draw(self.screen, self.font_small)
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if btn.rect.collidepoint(event.pos):
                        self.selected_education = key
                        self._add_particle(event.pos[0], event.pos[1], COLOR_PRIMARY)
            y += 125

    def _draw_difficulty_selection(self, x, width, events):
        y = 90
        self._draw_text("DIFFICULTY", self.font_small, COLOR_ACCENT, x + width//2, y, center=True)
        y += 40
        for key, config in self.difficulty_configs.items():
            color = COLOR_PRIMARY if self.selected_difficulty == key else COLOR_PANEL
            text_color = COLOR_BG if self.selected_difficulty == key else COLOR_TEXT
            btn = Button(x, y, width, 115, f"{config.name}\n{config.description}",
                         color, text_color, button_id=f"diff_{key}")
            btn.draw(self.screen, self.font_small)
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if btn.rect.collidepoint(event.pos):
                        self.selected_difficulty = key
                        self._add_particle(event.pos[0], event.pos[1], COLOR_PRIMARY)
            y += 125

    def _draw_playing(self, events):
        self._draw_gradient_background()
        self._update_particles()
        self._draw_particles()
        if self.need_button_update:
            self._update_playing_buttons()
        self._update_button_positions()
        header_height = 80
        sidebar_w = 350
        action_panel_w = 400
        main_area_w = SCREEN_WIDTH - sidebar_w - action_panel_w
        self._draw_playing_header()
        self._draw_playing_sidebar(sidebar_w, header_height)
        self._draw_playing_main(sidebar_w, main_area_w, header_height)
        self._draw_playing_actions(action_panel_w, header_height)
        draw_chatbot_icon(self.screen, 80, SCREEN_HEIGHT-80,
                          self.chatbot.is_thinking, self.chatbot_has_new_message)

        # ── CHATBOT MODAL──────────────────────────────
        if self.show_chatbot:
            result = draw_chatbot_modal(
                self.screen, self.font_medium, self.chatbot,
                input_text=self.chatbot_input_text,
                input_active=self.chatbot_input_active,
            )
            modal_x, modal_y, modal_w, modal_h, history_rect, input_rect = result

            # Send / Close buttons anchored to modal bottom
            send_btn  = Button(modal_x + modal_w - 62, input_rect.y,
                               52, input_rect.height, "→",
                               COLOR_SUCCESS, COLOR_BG, "send_chat", gradient=True)
            close_btn = Button(modal_x + modal_w - 46, modal_y + 16,
                               30, 30, "✕",
                               COLOR_DANGER, COLOR_TEXT, "close_chat")
            close_btn.draw(self.screen, self.font_small)
            send_btn.draw(self.screen, self.font_small)

            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if close_btn.rect.collidepoint(event.pos):
                        self._toggle_chatbot()
                    elif send_btn.rect.collidepoint(event.pos):
                        self._send_chatbot_message()
                    elif input_rect.collidepoint(event.pos):
                        self.chatbot_input_active = True
                    else:
                        self.chatbot_input_active = False
                if event.type == pygame.KEYDOWN and self.chatbot_input_active:
                    if event.key == pygame.K_RETURN:
                        self._send_chatbot_message()
                    elif event.key == pygame.K_BACKSPACE:
                        self.chatbot_input_text = self.chatbot_input_text[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        self.chatbot_input_active = False
                    elif len(self.chatbot_input_text) < 120:
                        self.chatbot_input_text += event.unicode

        # chatbot icon click
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if pygame.Rect(50, SCREEN_HEIGHT-110, 60, 60).collidepoint(event.pos):
                    self._toggle_chatbot()

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                for btn in self.cached_buttons[GameState.PLAYING]:
                    if btn.visible and btn.rect.collidepoint(event.pos) and hasattr(btn, 'lock_data') and btn.lock_data:
                        if self.locked_action and self.locked_action['callback'] == btn.lock_data['callback']:
                            self.locked_action = None; self.game_message = "Action unlocked"
                        else:
                            self.locked_action = btn.lock_data; self.game_message = f"Locked: {btn.lock_data['name']}"
                        self.need_button_update = True; break
            for btn in self.cached_buttons[GameState.PLAYING]:
                if btn.button_id in ["next_month", "help", "chatbot"]: btn.handle_event(event)
            for btn in self.cached_buttons[GameState.PLAYING]:
                if btn.button_id not in ["next_month", "help", "chatbot"]: btn.handle_event(event)
        mouse_pos = pygame.mouse.get_pos()
        for btn in self.cached_buttons[GameState.PLAYING]:
            if btn.visible: btn.hover = btn.rect.collidepoint(mouse_pos)

    def _draw_playing_header(self):
        header_height = 80
        pygame.draw.rect(self.screen, COLOR_PANEL, (0, 0, SCREEN_WIDTH, header_height))
        pygame.draw.line(self.screen, COLOR_BORDER, (0, header_height), (SCREEN_WIDTH, header_height), 1)
        nw = self.money + self.investments + self.emergency_fund - self.debt
        bg_col = getattr(self, 'selected_avatar_bg', COLOR_PRIMARY)
        pygame.draw.circle(self.screen, bg_col, (90, 40), 25)
        pygame.draw.circle(self.screen, COLOR_ACCENT, (90, 40), 27, 2)
        acc_data = getattr(self, 'selected_avatar_acc', AVATAR_ACCESSORIES[0])
        draw_composite_avatar(self.screen, self.selected_avatar, acc_data, 90, 40, 28)
        self._draw_text("FINANCE QUEST", self.font_large, COLOR_PRIMARY, 150, 15)
        self._draw_text("MONTH", self.font_tiny, COLOR_TEXT_DIM, 550, 15)
        mc = COLOR_SUCCESS if self.current_month < MONTHS_PER_GAME*0.5 else COLOR_WARNING if self.current_month < MONTHS_PER_GAME*0.8 else COLOR_DANGER
        self._draw_text(f"{self.current_month}/{MONTHS_PER_GAME}", self.font_medium, mc, 550, 35)
        self._draw_text("CASH", self.font_tiny, COLOR_TEXT_DIM, 750, 15)
        self._draw_text(f"${self.money:,.0f}", self.font_medium, COLOR_SUCCESS if self.money > 0 else COLOR_DANGER, 750, 35)
        self._draw_text("NET WORTH", self.font_tiny, COLOR_TEXT_DIM, 950, 15)
        self._draw_text(f"${nw:,.0f}", self.font_medium, COLOR_PRIMARY if nw > 0 else COLOR_WARNING, 950, 35)
        for btn in self.cached_buttons[GameState.PLAYING]:
            if btn.button_id == "help":
                btn.rect.x = SCREEN_WIDTH-120; btn.rect.y = 20; btn.rect.width = 100; btn.rect.height = 40
                btn.draw(self.screen, self.font_small); break
        for btn in self.cached_buttons[GameState.PLAYING]:
            if btn.button_id == "chatbot":
                btn.rect.x = SCREEN_WIDTH-230; btn.rect.y = 20; btn.rect.width = 100; btn.rect.height = 40
                btn.draw(self.screen, self.font_small); break

    def _draw_playing_sidebar(self, sidebar_w, header_height):
        pygame.draw.rect(self.screen, (15, 25, 40), (0, header_height, sidebar_w, SCREEN_HEIGHT-header_height-100))
        pygame.draw.line(self.screen, COLOR_PRIMARY, (sidebar_w, header_height), (sidebar_w, SCREEN_HEIGHT-100), 2)
        sy = header_height + 30
        p = 30
        self._draw_text("WELL-BEING", self.font_small, COLOR_ACCENT, p, sy)
        sy += 40
        self._draw_text(f"Happiness: {self.happiness:.0f}%", self.font_small, COLOR_TEXT, p, sy)
        self._draw_progress_bar(p, sy+25, sidebar_w-60, 12, self.happiness, COLOR_SUCCESS)
        sy += 55
        self._draw_text(f"Stress: {self.stress:.0f}%", self.font_small, COLOR_TEXT, p, sy)
        self._draw_progress_bar(p, sy+25, sidebar_w-60, 12, self.stress, COLOR_DANGER)
        sy += 65
        pygame.draw.line(self.screen, COLOR_PANEL_HOVER, (p, sy), (sidebar_w-p, sy)); sy += 25
        self._draw_text("FINANCES", self.font_small, COLOR_ACCENT, p, sy); sy += 35
        for label, val, col in [
            ("Income", f"+${self.monthly_income:,.0f}", COLOR_SUCCESS),
            ("Expenses", f"-${(self.rent+self.groceries+self.transport):,.0f}", COLOR_DANGER),
            ("Debt", f"${self.debt:,.0f}", COLOR_DANGER),
            ("Investments", f"${self.investments:,.0f}", COLOR_PRIMARY),
            ("Emergency", f"${self.emergency_fund:,.0f}", COLOR_WARNING),
        ]:
            self._draw_text(label, self.font_small, COLOR_TEXT_DIM, p, sy)
            self._draw_text(val, self.font_small, col, sidebar_w-p-50, sy)
            sy += 35
        sy += 10
        pygame.draw.line(self.screen, COLOR_PANEL_HOVER, (p, sy), (sidebar_w-p, sy)); sy += 25
        self._draw_text("📋 STATUS", self.font_small, COLOR_ACCENT, p, sy); sy += 35
        self._draw_text("🎓 Education:", self.font_small, COLOR_TEXT_DIM, p, sy)
        self._draw_text(self.education_configs[self.current_education_level].name, self.font_small, COLOR_ACCENT, p+120, sy)
        if self.debuffs:
            sy += 45
            self._draw_text("Active Effects:", self.font_small, COLOR_DANGER, p, sy); sy += 30
            for d in self.debuffs:
                pygame.draw.rect(self.screen, COLOR_DANGER, (p, sy, 140, 28), border_radius=6)
                self._draw_text(d.upper(), self.font_tiny, COLOR_BG, p+10, sy+6)
                sy += 35

    def _draw_playing_main(self, sidebar_w, main_area_w, header_height):
        mx = sidebar_w + 30
        my = header_height + 30
        self._draw_text("ACTIVE GOALS", self.font_medium, COLOR_PRIMARY, mx, my, glow=True)
        my += 45
        goal_w = (main_area_w - 80) // 2
        goal_h = 80
        for i, goal in enumerate(self.goals.values()):
            gx = mx if i % 2 == 0 else mx + goal_w + 30
            gy = my + (i // 2) * (goal_h + 20)
            gc = COLOR_SUCCESS if goal['completed'] else COLOR_PANEL
            gb = COLOR_SUCCESS if goal['completed'] else COLOR_BORDER
            pygame.draw.rect(self.screen, gc, (gx, gy, goal_w, goal_h), border_radius=12)
            pygame.draw.rect(self.screen, gb, (gx, gy, goal_w, goal_h), 3, border_radius=12)
            self._draw_text(f"{'✓' if goal['completed'] else '○'} {goal['label']}", self.font_small,
                            COLOR_BG if goal['completed'] else COLOR_TEXT, gx+15, gy+30)
        msg_y = my + 220
        msg_rect = pygame.Rect(mx, msg_y, main_area_w-60, 100)
        pygame.draw.rect(self.screen, COLOR_PANEL, msg_rect, border_radius=15)
        pygame.draw.rect(self.screen, COLOR_PRIMARY, msg_rect, 2, border_radius=15)
        self._draw_text("EVENT LOG", self.font_tiny, COLOR_PRIMARY, mx+20, msg_y+15)
        ly = msg_y + 45
        for line in self.game_message.split('|')[:2]:
            self._draw_text(line.strip(), self.font_small, COLOR_TEXT, mx+20, ly); ly += 35
        controls_y = msg_y + 120
        pygame.draw.rect(self.screen, COLOR_PANEL, (mx, controls_y, 160, 90), border_radius=15)
        pygame.draw.rect(self.screen, COLOR_BORDER, (mx, controls_y, 160, 90), 2, border_radius=15)
        self._draw_text("ACTIONS LEFT", self.font_tiny, COLOR_TEXT_DIM, mx+80, controls_y+15, center=True)
        ac = {3: (COLOR_SUCCESS, "FULL"), 2: (COLOR_SUCCESS, "GOOD"), 1: (COLOR_WARNING, "LOW")}.get(self.actions_remaining, (COLOR_DANGER, "NONE"))
        self._draw_text(str(self.actions_remaining), self.font_xl, ac[0], mx+80, controls_y+50, center=True, glow=True)
        self._draw_text(ac[1], self.font_tiny, ac[0], mx+80, controls_y+70, center=True)
        nb_w, nb_h = 200, 90
        nb_x = mx + main_area_w - 60 - nb_w
        for btn in self.cached_buttons[GameState.PLAYING]:
            if btn.button_id == "next_month":
                btn.rect.x = nb_x; btn.rect.y = controls_y
                btn.rect.width = nb_w; btn.rect.height = nb_h
                btn.original_y = controls_y
                btn.update_text("NEXT MONTH")
                btn.draw(self.screen, self.font_medium); break

    def _draw_playing_actions(self, action_panel_w, header_height):
        action_rect = pygame.Rect(SCREEN_WIDTH-action_panel_w, header_height, action_panel_w, SCREEN_HEIGHT-header_height-100)
        pygame.draw.rect(self.screen, (20, 30, 50), action_rect)
        pygame.draw.line(self.screen, COLOR_PRIMARY, (action_rect.x, header_height), (action_rect.x, SCREEN_HEIGHT-100), 2)
        self._draw_text("AVAILABLE ACTIONS", self.font_small, COLOR_PRIMARY, action_rect.x+20, header_height+20)
        if self.active_dropdown:
            mouse_pos = pygame.mouse.get_pos()
            mouse_over_button = mouse_over_dropdown = False
            for btn in self.cached_buttons[GameState.PLAYING]:
                if hasattr(btn, 'action_type') and btn.action_type == self.active_dropdown:
                    if btn.rect.collidepoint(mouse_pos):
                        mouse_over_button = True; self.dropdown_last_hover_time = pygame.time.get_ticks()
                    opt_w, opt_h = 100, 45
                    dw = opt_w * 4 + 20; dh = opt_h + 15
                    dx = btn.rect.x
                    if btn.action_type in ['save', 'invest']:
                        dy = btn.rect.y - dh - 5
                    else:
                        dy = btn.rect.y + btn.rect.height + 5
                    if dx + dw > SCREEN_WIDTH: dx = SCREEN_WIDTH - dw - 10
                    if dy < 0: dy = btn.rect.y + btn.rect.height + 5
                    if dy + dh > SCREEN_HEIGHT - 100: dy = btn.rect.y - dh - 5
                    dr = pygame.Rect(dx, dy, dw, dh)
                    if dr.collidepoint(mouse_pos):
                        mouse_over_dropdown = True; self.dropdown_last_hover_time = pygame.time.get_ticks()
                    break
            self.dropdown_hover = mouse_over_dropdown
            if not mouse_over_button and not mouse_over_dropdown:
                if pygame.time.get_ticks() - self.dropdown_last_hover_time > self.dropdown_stay_duration:
                    self.close_dropdown()
        for btn in self.cached_buttons[GameState.PLAYING]:
            if hasattr(btn, 'action_type') and btn.visible and btn.enabled:
                if btn.rect.collidepoint(pygame.mouse.get_pos()):
                    if self.active_dropdown != btn.action_type:
                        self.active_dropdown = btn.action_type
                        self.dropdown_last_hover_time = pygame.time.get_ticks()
        for btn in self.cached_buttons[GameState.PLAYING]:
            if btn.button_id not in ["next_month", "help", "chatbot"]:
                btn.draw(self.screen, self.font_tiny)
        if self.active_dropdown:
            for btn in self.cached_buttons[GameState.PLAYING]:
                if hasattr(btn, 'action_type') and btn.action_type == self.active_dropdown:
                    self.draw_financial_dropdown(self.screen, btn); break
        for btn in self.cached_buttons[GameState.PLAYING]:
            if btn.button_id not in ["next_month", "help", "chatbot"]:
                btn.draw_tooltip(self.screen, self.font_tiny)

    def _draw_help_panel(self, events):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)); overlay.set_alpha(220); overlay.fill((0,0,0))
        self.screen.blit(overlay, (0, 0))
        pw, ph = 900, 650
        px = (SCREEN_WIDTH-pw)//2; py = (SCREEN_HEIGHT-ph)//2
        for event in events:
            if event.type == pygame.MOUSEWHEEL and self.show_help_panel:
                self.help_scroll_offset = max(0, min(self.help_scroll_offset - event.y*30, self.help_max_scroll))
        content_h = 800
        cs = pygame.Surface((pw-40, content_h), pygame.SRCALPHA); cs.fill((0,0,0,0))
        pygame.draw.rect(self.screen, COLOR_BG, (px, py, pw, ph), border_radius=20)
        pygame.draw.rect(self.screen, COLOR_PRIMARY, (px, py, pw, ph), 4, border_radius=20)
        self._draw_text("GAME GUIDE", self.font_large, COLOR_PRIMARY, px+pw//2, py+40, center=True, glow=True)
        sections = [
            ("Goal", "Complete 24 months with high net worth and happiness!"),
            ("Actions", f"You have {ACTIONS_PER_MONTH} actions per month. Right-click to lock actions for next month."),
            ("Financial Tips", "• Invest early for compound returns\n• Keep 3 months income as emergency fund\n• Pay off high-interest debt first"),
            ("Well-being", "• Low happiness causes debuffs\n• High stress leads to burnout\n• Balance work and life!"),
            ("Education", "• Increases monthly income permanently\n• Costs added to debt\n• Higher education = higher income"),
            ("Warning Signs", "• Red money = trouble ahead\n• Orange stress bar = burnout risk\n• Debuffs reduce your income"),
            ("Financial Actions", "• Invest: Grow your wealth over time\n• Save: Build emergency fund\n• Withdraw: Take from emergency fund\n• Pay Debt: Reduce debt and stress"),
            ("Lifestyle Choices", "• Leisure: Boost happiness, reduce stress\n• Risky: Potential rewards but addiction risk\n• Education: Long-term income boost\n• Utilities: One-time purchases"),
            ("Lock System", "Right-click any action button to lock it. Locked actions automatically execute at the start of next month!"),
            ("Scoring", "Final score = Net Worth + Goal Bonuses + Happiness × 100 + Months × 500"),
        ]
        sh = sum(35 + len(s[1].split('\n'))*25 + 15 for s in sections)
        self.help_max_scroll = max(0, sh - (ph - 150))
        y = 20 - self.help_scroll_offset
        for title, content in sections:
            if y + 30 > 0 and y < content_h:
                cs.blit(self.font_small.render(title, True, COLOR_ACCENT), (30, y)); y += 35
                for line in content.split('\n'):
                    if y + 20 > 0 and y < content_h:
                        cs.blit(self.font_tiny.render(line, True, COLOR_TEXT), (55, y))
                    y += 25
                y += 15
            else:
                y += 35 + len(content.split('\n'))*25 + 15
        self.screen.blit(cs, (px+20, py+100), area=(0, self.help_scroll_offset, pw-40, ph-150))
        if self.help_max_scroll > 0:
            sbh = (ph-150)*(ph-150)/content_h
            sby = py+100 + (self.help_scroll_offset/self.help_max_scroll)*((ph-150)-sbh)
            pygame.draw.rect(self.screen, COLOR_PANEL_HOVER, (px+pw-20, py+100, 8, ph-150), border_radius=4)
            pygame.draw.rect(self.screen, COLOR_PRIMARY, (px+pw-20, sby, 8, sbh), border_radius=4)
        close_btn = Button(px+pw//2-100, py+ph-70, 200, 50, "Close", COLOR_PRIMARY, COLOR_BG, gradient=True, icon="✓")
        close_btn.callback = self._toggle_help
        close_btn.hover = close_btn.rect.collidepoint(pygame.mouse.get_pos())
        close_btn.draw(self.screen, self.font_medium)
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and close_btn.hover:
                self._toggle_help(); break

    def _draw_event_modal(self, events):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)); overlay.set_alpha(200); overlay.fill((0,0,0))
        self.screen.blit(overlay, (0, 0))
        w, h = 600, 450
        x, y = (SCREEN_WIDTH-w)//2, (SCREEN_HEIGHT-h)//2
        pygame.draw.rect(self.screen, COLOR_PANEL, (x, y, w, h), border_radius=20)
        pygame.draw.rect(self.screen, COLOR_ACCENT, (x, y, w, h), 4, border_radius=20)
        self._draw_text(self.current_event.name, self.font_large, COLOR_ACCENT, x+w//2, y+50, center=True, glow=True)
        ty = y + 130
        for line in self._wrap_text(self.current_event.description, self.font_medium, w-80):
            self._draw_text(line, self.font_medium, COLOR_TEXT, x+w//2, ty, center=True); ty += 40
        iy = ty + 30
        if self.current_event.cost > 0:
            self._draw_text(f"Cost: -${self.current_event.cost:,.0f}", self.font_medium, COLOR_DANGER, x+w//2, iy, center=True); iy += 35
        if self.current_event.stress_increase > 0:
            self._draw_text(f"Stress: +{self.current_event.stress_increase}%", self.font_medium, COLOR_DANGER, x+w//2, iy, center=True)
        cont_btn = Button(x+w//2-100, y+h-80, 200, 50, "Continue", COLOR_PRIMARY, COLOR_BG, gradient=True, icon="▶")
        cont_btn.callback = self.handle_event_close
        cont_btn.hover = cont_btn.rect.collidepoint(pygame.mouse.get_pos())
        cont_btn.draw(self.screen, self.font_medium)
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and cont_btn.hover:
                self.handle_event_close()

    def draw_financial_dropdown(self, screen, button):
        if not hasattr(button, 'action_type'): return
        at = button.action_type
        opt_w, opt_h = 100, 45
        dw = opt_w * 4 + 20; dh = opt_h + 15
        dx = button.rect.x
        dy = (button.rect.y - dh - 5) if at in ['invest', 'save'] else (button.rect.y + button.rect.height + 5)
        if dx + dw > SCREEN_WIDTH: dx = SCREEN_WIDTH - dw - 10
        if dy < 0: dy = button.rect.y + button.rect.height + 5
        if dy + dh > SCREEN_HEIGHT - 100: dy = button.rect.y - dh - 5
        dr = pygame.Rect(dx, dy, dw, dh)
        mouse_pos = pygame.mouse.get_pos()
        self.dropdown_hover = dr.collidepoint(mouse_pos)
        if self.dropdown_hover or button.rect.collidepoint(mouse_pos):
            self.dropdown_last_hover_time = pygame.time.get_ticks()
        for i in range(dr.height):
            ratio = i / dr.height
            c = (int(COLOR_PANEL[0]*(1-ratio*0.3)), int(COLOR_PANEL[1]*(1-ratio*0.3)), int(COLOR_PANEL[2]*(1-ratio*0.3)))
            pygame.draw.line(screen, c, (dr.x, dr.y+i), (dr.x+dr.width, dr.y+i))
        pygame.draw.rect(screen, COLOR_PRIMARY, dr, 2, border_radius=8)
        amounts = {'save': [(100,"$100"),(500,"$500"),(1000,"$1k"),(None,"Custom")],
                   'invest': [(1000,"$1k"),(5000,"$5k"),(10000,"$10k"),(None,"Custom")],
                   'withdraw': [(500,"$500"),(1000,"$1k"),(5000,"$5k"),(None,"Custom")],
                   'pay_debt': [(1000,"$1k"),(5000,"$5k"),(10000,"$10k"),(None,"Custom")]
                   }.get(at, [(1000,"$1k"),(3000,"$3k"),(5000,"$5k"),(None,"Custom")])
        for idx, (amount, label) in enumerate(amounts):
            or_ = pygame.Rect(dx+5+idx*opt_w, dy+5, opt_w-5, opt_h-5)
            oh = or_.collidepoint(mouse_pos)
            affordable = True
            if amount is not None:
                if at == 'save' and self.money < amount: affordable = False
                elif at == 'invest' and self.money < amount: affordable = False
                elif at == 'withdraw' and self.emergency_fund < amount: affordable = False
                elif at == 'pay_debt' and (self.money < amount or self.debt < amount): affordable = False
            bg = (40,45,55) if not affordable else (COLOR_PRIMARY if oh else COLOR_PANEL_HOVER)
            tc = (80,85,95) if not affordable else (COLOR_BG if oh else COLOR_TEXT)
            pygame.draw.rect(screen, bg, or_, border_radius=5)
            ts = self.font_tiny.render(label, True, tc)
            screen.blit(ts, ts.get_rect(center=or_.center))
            if oh and affordable and pygame.mouse.get_pressed()[0]:
                if amount is None: self.open_custom_input(at)
                else: self.execute_financial_action(at, amount)
                return True
        return False

    def _draw_custom_input_modal(self, events):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)); overlay.set_alpha(200); overlay.fill((0,0,0))
        self.screen.blit(overlay, (0, 0))
        w, h = 500, 350
        x, y = (SCREEN_WIDTH-w)//2, (SCREEN_HEIGHT-h)//2
        pygame.draw.rect(self.screen, COLOR_BG, (x, y, w, h), border_radius=20)
        pygame.draw.rect(self.screen, COLOR_PRIMARY, (x, y, w, h), 4, border_radius=20)
        titles = {'invest': '💰 Invest Custom Amount', 'save': '💵 Save Custom Amount',
                  'withdraw': '🏦 Withdraw Custom Amount', 'pay_debt': '💳 Pay Debt Custom Amount'}
        self._draw_text(titles.get(self.custom_input_type, 'Enter Amount'), self.font_large, COLOR_PRIMARY, x+w//2, y+40, center=True, glow=True)
        self._draw_text("Enter amount (Max: $100,000)", self.font_small, COLOR_TEXT_DIM, x+w//2, y+100, center=True)
        ir = pygame.Rect(x+50, y+150, w-100, 60)
        pygame.draw.rect(self.screen, COLOR_PANEL, ir, border_radius=10)
        pygame.draw.rect(self.screen, COLOR_PRIMARY, ir, 3, border_radius=10)
        dt = "$" + self.custom_input_text if self.custom_input_text else "$0"
        ts = self.font_medium.render(dt, True, COLOR_TEXT)
        self.screen.blit(ts, ts.get_rect(center=ir.center))
        cb = Button(x+50, y+h-70, 180, 50, "Confirm", COLOR_SUCCESS, COLOR_BG, gradient=True, icon="✓")
        xb = Button(x+w-230, y+h-70, 180, 50, "Cancel", COLOR_PANEL, icon="✗")
        cb.draw(self.screen, self.font_medium); xb.draw(self.screen, self.font_medium)
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN: self.handle_custom_input_submit()
                elif event.key == pygame.K_ESCAPE: self.show_custom_input = False; self.custom_input_text = ""
                elif event.key == pygame.K_BACKSPACE: self.custom_input_text = self.custom_input_text[:-1]
                elif event.unicode.isdigit() or event.unicode == '.':
                    if len(self.custom_input_text) < 10: self.custom_input_text += event.unicode
            mouse_pos = pygame.mouse.get_pos()
            cb.hover = cb.rect.collidepoint(mouse_pos); xb.hover = xb.rect.collidepoint(mouse_pos)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if cb.hover: self.handle_custom_input_submit()
                elif xb.hover: self.show_custom_input = False; self.custom_input_text = ""

    def _draw_game_over(self, events):
        self._draw_gradient_background()
        pygame.draw.rect(self.screen, COLOR_PANEL, (SCREEN_WIDTH//2-450, 80, 900, 750), border_radius=30)
        pygame.draw.rect(self.screen, COLOR_PRIMARY, (SCREEN_WIDTH//2-450, 80, 900, 750), 4, border_radius=30)
        score = self.calculate_score()
        is_hs = score > self.high_score
        self._draw_text("🏆 NEW HIGH SCORE! 🏆" if is_hs else "GAME OVER",
                        self.font_xl, COLOR_WARNING if is_hs else COLOR_TEXT,
                        SCREEN_WIDTH//2, 150, center=True, shadow=True, glow=True)
        self._draw_text(f"Final Score: {score:,}", self.font_large, COLOR_PRIMARY, SCREEN_WIDTH//2, 240, center=True)
        if is_hs:
            self._draw_text("Congratulations! You've set a new record!", self.font_medium, COLOR_SUCCESS, SCREEN_WIDTH//2, 310, center=True)
        sy = 380
        for label, val in [
            ("Net Worth", f"${(self.money+self.investments+self.emergency_fund-self.debt):,.0f}"),
            ("Happiness", f"{self.happiness:.0f}%"),
            ("Goals Met", f"{sum(1 for g in self.goals.values() if g['completed'])}/4"),
            ("Months", f"{self.current_month}")
        ]:
            self._draw_text(label, self.font_medium, COLOR_TEXT_DIM, SCREEN_WIDTH//2-150, sy)
            self._draw_text(val, self.font_medium, COLOR_TEXT, SCREEN_WIDTH//2+150, sy)
            sy += 60
        if self.game_message:
            self._draw_text(self.game_message, self.font_medium, COLOR_DANGER, SCREEN_WIDTH//2, 600, center=True)
        for btn in self.cached_buttons[GameState.GAME_OVER]:
            btn.draw(self.screen, self.font_medium)
        for event in events:
            for btn in self.cached_buttons[GameState.GAME_OVER]:
                btn.handle_event(event)

    def run(self):
        running = True
        while running:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    running = False
                if self.state == GameState.PLAYING and not self.show_event_modal:
                    if event.type == pygame.MOUSEWHEEL:
                        self.scroll_offset = max(0, min(self.scroll_offset - event.y*30, self.max_scroll))
                        self._update_button_positions()
                        self.close_dropdown()
            self.screen.fill(COLOR_BG)
            if self.state == GameState.TITLE: self._draw_title(events)
            elif self.state == GameState.TUTORIAL: self._draw_tutorial(events)
            elif self.state == GameState.SETUP: self._draw_setup(events)
            elif self.state == GameState.PLAYING: self._draw_playing(events)
            elif self.state == GameState.GAME_OVER: self._draw_game_over(events)
            if self.show_help_panel: self._draw_help_panel(events)
            if self.show_event_modal: self._draw_event_modal(events)
            if self.show_custom_input: self._draw_custom_input_modal(events)
            if self.avatar_creator.visible:
                self._draw_avatar_creator_modal(events)
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = FinanceGame()
    game.run()