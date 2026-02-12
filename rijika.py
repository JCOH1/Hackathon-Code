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

pygame.init()

SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 900
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

# ============================================================
# AVATAR OPTIONS
# ============================================================
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


class SimpleHintBot:
    def __init__(self):
        self.name = "Finley"
        self.avatar = "🦊"
        self.enabled = True
        self.is_thinking = False
        self.last_response = "Hi! I'm Finley, your financial assistant! Ask me for tips! 🦊"
        self.ready = True
        self.hints = {
            "invest": [
                "💡 Investing early lets compound interest work for you!",
                "💡 Try investing $1k-$5k when you have extra cash.",
                "💡 Higher risk = higher potential returns, but don't invest your emergency fund!"
            ],
            "save": [
                "💡 Aim for 3 months of expenses in your emergency fund!",
                "💡 Save at least $100 each month to build your safety net.",
                "💡 Emergency fund protects you from unexpected costs like medical bills."
            ],
            "debt": [
                "💡 Pay off high-interest debt first to reduce stress!",
                "💡 Every $1k debt payment reduces your stress by 5%.",
                "💡 Being debt-free is one of the 4 main goals!"
            ],
            "happiness": [
                "💡 Low happiness causes debuffs! Take a vacation or date night.",
                "💡 Balance work and life - don't forget leisure activities!",
                "💡 Happiness below 30% will make you distracted and lose income."
            ],
            "stress": [
                "💡 High stress leads to burnout! Use therapy or pay debt.",
                "💡 Stress above 80% is dangerous - take action quickly!",
                "💡 Emergency fund and low debt both help reduce stress."
            ],
            "education": [
                "🎓 University adds +$1500/month income but costs $30k debt and +15 stress!",
                "🎓 Masters requires University first, adds +$1000/month, costs $50k debt and +20 stress!",
                "🎓 Higher education is worth it long-term, but manage your stress levels!"
            ],
            "general": [
                f"💡 You have {ACTIONS_PER_MONTH} actions per month - use them wisely!",
                "💡 Complete all 4 goals for maximum bonus points!",
                "💡 Right-click any action to lock it for next month!",
                "💡 Net Worth = Cash + Investments + Emergency - Debt",
                "💡 You started in Month 0 - survive 24 months to win!"
            ]
        }

    def ask(self, question, game_state=None):
        self.is_thinking = True
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
        self.last_response = context + response
        self.is_thinking = False
        return self.last_response

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

    def reset_conversation(self):
        self.last_response = "Conversation reset! How can I help you? 🦊"


finance_chatbot = SimpleHintBot()


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


def draw_chatbot_modal(screen, font, chatbot, game_state=None):
    modal_w, modal_h = 500, 600
    modal_x = SCREEN_WIDTH - modal_w - 30
    modal_y = 100
    pygame.draw.rect(screen, COLOR_BG, (modal_x, modal_y, modal_w, modal_h), border_radius=20)
    pygame.draw.rect(screen, COLOR_ACCENT, (modal_x, modal_y, modal_w, modal_h), 3, border_radius=20)
    pygame.draw.rect(screen, COLOR_PANEL, (modal_x, modal_y, modal_w, 70),
                     border_top_left_radius=20, border_top_right_radius=20)
    avatar_font = pygame.font.SysFont("Arial", 40)
    screen.blit(avatar_font.render("🦊", True, COLOR_TEXT), (modal_x + 20, modal_y + 15))
    title_font = pygame.font.SysFont("Arial", 24, bold=True)
    screen.blit(title_font.render(f"{chatbot.name} - Financial Assistant", True, COLOR_PRIMARY),
                (modal_x + 80, modal_y + 25))
    history_rect = pygame.Rect(modal_x + 20, modal_y + 90, modal_w - 40, modal_h - 180)
    pygame.draw.rect(screen, COLOR_PANEL, history_rect, border_radius=10)
    y_offset = modal_y + 110
    font_small = pygame.font.SysFont("Arial", 16)
    bot_bubble = pygame.Rect(modal_x + 30, y_offset, modal_w - 100, 80)
    pygame.draw.rect(screen, COLOR_PANEL_HOVER, bot_bubble, border_radius=15)
    pygame.draw.rect(screen, COLOR_ACCENT, bot_bubble, 1, border_radius=15)
    words = chatbot.last_response.split()
    lines = []
    current_line = []
    for word in words:
        current_line.append(word)
        if font_small.size(' '.join(current_line))[0] > modal_w - 140:
            current_line.pop()
            lines.append(' '.join(current_line))
            current_line = [word]
    if current_line:
        lines.append(' '.join(current_line))
    for i, line in enumerate(lines[:4]):
        screen.blit(font_small.render(line, True, COLOR_TEXT), (modal_x + 45, y_offset + 10 + i * 20))
    return modal_x, modal_y, modal_w, modal_h, history_rect


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


class FinanceGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("FinanceQuest - Master Your Financial Future")
        self.clock = pygame.time.Clock()
        pygame.display.set_icon(self.screen)
        pygame.event.set_allowed([pygame.QUIT, pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION,
                                   pygame.MOUSEWHEEL, pygame.KEYDOWN])
        self._init_fonts()
        self.state = GameState.TITLE
        self.tutorial_step = 0
        self.selected_class = None
        self.selected_education = None
        self.selected_difficulty = None
        self.selected_avatar_index = 0      # NEW: tracks chosen avatar
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
        self.chatbot = finance_chatbot
        self.chatbot_has_new_message = False

    def _init_fonts(self):
        self.font_xl = pygame.font.SysFont("Arial Black", 72, bold=True)
        self.font_large = pygame.font.SysFont("Arial", 48, bold=True)
        self.font_medium = pygame.font.SysFont("Arial", 28, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 20, bold=True)
        self.font_tiny = pygame.font.SysFont("Arial", 16)
        self.font_digital = pygame.font.SysFont("Courier New", 32, bold=True)
        self.font_emoji_large = pygame.font.SysFont("Segoe UI Emoji", 30)
        self.font_emoji_header = pygame.font.SysFont("Segoe UI Emoji", 28)

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
        self.active_dropdown = None
        self.dropdown_hover = False
        self.dropdown_last_hover_time = 0
        self.dropdown_stay_duration = 2000
        self.show_custom_input = False
        self.custom_input_text = ""
        self.custom_input_type = ""
        self.help_scroll_offset = 0
        self.help_max_scroll = 0

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
            'easy':   DifficultyConfig("Easy Mode", 0.05, 0.5, "🟢 Fewer emergencies, stable markets"),
            'normal': DifficultyConfig("Normal Mode", 0.10, 1.0, "🟡 Balanced challenge"),
            'hard':   DifficultyConfig("Hard Mode", 0.20, 1.5, "🔴 Frequent emergencies, volatile markets")
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
            EmergencyEvent("🚑 Medical Emergency", "You've been diagnosed with a serious health condition requiring immediate treatment.", cost=8000, stress_increase=30),
            EmergencyEvent("💼 Job Loss", "Your company has downsized and you've been laid off. No income for 3 months.", months_no_income=3, stress_increase=40),
            EmergencyEvent("📉 Market Crash", "The stock market has crashed! Your investments have lost significant value.", investment_loss=0.4, stress_increase=25),
            EmergencyEvent("🏠 Home Emergency", "Major repairs needed for your living space.", cost=3500, stress_increase=15),
            EmergencyEvent("👨‍👩‍👧 Family Emergency", "A family member needs financial assistance urgently.", cost=5000, stress_increase=20)
        ]

    def _init_ui_elements(self):
        self._init_title_buttons()
        self._init_tutorial_buttons()
        self._init_setup_buttons()
        self._init_game_over_buttons()

    def _init_title_buttons(self):
        self.cached_buttons[GameState.TITLE] = [
            Button(SCREEN_WIDTH//2-150, 500, 300, 70, "New Game", COLOR_PRIMARY, text_color=COLOR_BG, button_id="new_game", gradient=True, icon="🎮"),
            Button(SCREEN_WIDTH//2-150, 590, 300, 70, "Skip Tutorial", COLOR_PANEL, text_color=COLOR_TEXT, button_id="skip_tutorial", icon="⏩"),
            Button(SCREEN_WIDTH-150, 20, 130, 50, "Help", COLOR_ACCENT, text_color=COLOR_TEXT, button_id="help_title", icon="❓")
        ]
        self.cached_buttons[GameState.TITLE][0].callback = lambda: setattr(self, 'state', GameState.TUTORIAL)
        self.cached_buttons[GameState.TITLE][1].callback = lambda: setattr(self, 'state', GameState.SETUP)
        self.cached_buttons[GameState.TITLE][2].callback = self._toggle_help

    def _init_tutorial_buttons(self):
        panel_rect = pygame.Rect(200, 150, SCREEN_WIDTH-400, 500)
        btn_y = panel_rect.bottom - 90
        self.cached_buttons[GameState.TUTORIAL] = [
            Button(panel_rect.left+50, btn_y, 180, 50, "Previous", COLOR_PANEL_HOVER, button_id="tut_prev", icon="◀"),
            Button(panel_rect.right-230, btn_y, 180, 50, "Next", COLOR_PRIMARY, text_color=COLOR_BG, button_id="tut_next", gradient=True, icon="▶"),
            Button(SCREEN_WIDTH-250, 800, 200, 50, "Skip All", COLOR_PANEL, button_id="tut_skip", icon="⏭")
        ]
        self.cached_buttons[GameState.TUTORIAL][0].callback = self._tut_prev
        self.cached_buttons[GameState.TUTORIAL][1].callback = self._tut_next
        self.cached_buttons[GameState.TUTORIAL][2].callback = self._tut_skip

    def _init_setup_buttons(self):
        self.cached_buttons[GameState.SETUP] = [
            Button(SCREEN_WIDTH//2-120, 820, 240, 55, "Start Journey", COLOR_SUCCESS, text_color=COLOR_BG, button_id="setup_start", gradient=True, icon="🚀"),
            Button(SCREEN_WIDTH//2-80, 882, 160, 40, "Back", COLOR_PANEL, button_id="setup_back", icon="↩")
        ]
        self.cached_buttons[GameState.SETUP][0].callback = self.start_game
        self.cached_buttons[GameState.SETUP][1].callback = lambda: setattr(self, 'state', GameState.TITLE)

    def _init_game_over_buttons(self):
        self.cached_buttons[GameState.GAME_OVER] = [
            Button(SCREEN_WIDTH//2-220, 680, 200, 60, "Play Again", COLOR_SUCCESS, text_color=COLOR_BG, button_id="play_again", gradient=True, icon="🔄"),
            Button(SCREEN_WIDTH//2+20, 680, 200, 60, "Main Menu", COLOR_PANEL, button_id="menu", icon="🏠")
        ]
        self.cached_buttons[GameState.GAME_OVER][0].callback = self._reset_for_new_game
        self.cached_buttons[GameState.GAME_OVER][1].callback = lambda: setattr(self, 'state', GameState.TITLE)

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

    def _update_playing_buttons(self):
        self.cached_buttons[GameState.PLAYING] = [
            btn for btn in self.cached_buttons[GameState.PLAYING]
            if btn.button_id in ["next_month", "help", "chatbot"]
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
                tooltip = f"📚 {c.name}: +${c.cost:,.0f} investment in your future!" if c.choice_type == 'education' else f"🎁 {c.name}"
                util_actions.append((f"{c.name}\n${c.cost:,.0f}", lambda k=k: self.take_life_choice(k), enabled, col, tooltip))
        if util_actions:
            ay = self._create_section_buttons("GROWTH & ASSETS", util_actions, ay, btn_w, btn_h, view_rect)
        if self.debuffs:
            health_actions = []
            if 'addict' in self.debuffs:
                health_actions.append(("🏥 Rehab\n$1.5k", self.treat_addiction, self.money >= 1500, COLOR_DANGER, "Treatment for addiction"))
            if 'unhappy' in self.debuffs or 'distracted' in self.debuffs:
                health_actions.append(("🧠 Therapy\n$800", self.seek_therapy, self.money >= 800, COLOR_ACCENT, "Clear debuffs and reduce stress"))
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
            display_label = f"🔒 {label}" if is_locked else label
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
            if btn.button_id not in ["next_month", "help", "chatbot"]:
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
        # Use the player's chosen avatar
        self.selected_avatar = AVATARS[self.selected_avatar_index]["emoji"]
        self.actions_taken_this_month = 0
        self.actions_remaining = ACTIONS_PER_MONTH
        self.locked_action = None
        for goal in self.goals.values():
            goal['completed'] = False
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
        if choice.choice_type == 'education':
            self._handle_education_upgrade(choice_key, choice)
            return
        self.happiness = min(100, self.happiness + choice.happiness)
        self.stress = max(0, self.stress + choice.stress)
        if choice.choice_type == 'risky':
            if self._handle_risky_choice(choice_key, choice): return
        if choice_key == 'vehicle': self.has_vehicle = True
        self.game_message = f"✨ {choice.name}: Happiness +{choice.happiness:.0f} | Actions: {self.actions_remaining}/{ACTIONS_PER_MONTH}"
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
            self.game_message = f"💰 You won ${choice.win_amount:.0f}!"
            self._add_particle(self.screen.get_width()//2, self.screen.get_height()//2, COLOR_WARNING)
            self.need_button_update = True; return True
        if choice.debuff_chance > 0 and random.random() < choice.debuff_chance:
            if choice.debuff not in self.debuffs:
                self.debuffs.append(choice.debuff)
                self.game_message = f"⚠️ Addicted to {choice.name}!"
                self._add_particle(self.screen.get_width()//2, self.screen.get_height()//2, COLOR_DANGER)
                self.need_button_update = True; return True
        return False

    def invest_money(self, amount):
        if self.actions_remaining <= 0: self.game_message = f"⚠️ No actions left!"; return
        if self.money >= amount:
            self.money -= amount; self.investments += amount
            self.actions_taken_this_month += 1; self.actions_remaining -= 1
            self.game_message = f"💰 Invested ${amount:.0f} | Actions: {self.actions_remaining}/{ACTIONS_PER_MONTH}"
            self._add_particle(self.screen.get_width()//2, self.screen.get_height()//2, COLOR_PRIMARY)
            self.need_button_update = True

    def withdraw_investment(self, amount):
        if self.actions_remaining <= 0: self.game_message = f"⚠️ No actions left!"; return
        withdrawal = min(amount, self.investments)
        if withdrawal > 0:
            self.investments -= withdrawal; self.money += withdrawal
            self.actions_taken_this_month += 1; self.actions_remaining -= 1
            self.game_message = f"💸 Withdrew ${withdrawal:.0f} | Actions: {self.actions_remaining}/{ACTIONS_PER_MONTH}"
            self.need_button_update = True
        else:
            self.game_message = "No investments!"

    def add_to_emergency_fund(self, amount):
        if self.actions_remaining <= 0: self.game_message = f"⚠️ No actions left!"; return
        if self.money >= amount:
            self.money -= amount; self.emergency_fund += amount
            self.actions_taken_this_month += 1; self.actions_remaining -= 1
            self.game_message = f"🏦 Saved ${amount:.0f} | Actions: {self.actions_remaining}/{ACTIONS_PER_MONTH}"
            self.need_button_update = True

    def pay_off_debt(self, amount):
        if self.actions_remaining <= 0: self.game_message = f"⚠️ No actions left!"; return
        payment = min(amount, self.debt, self.money)
        if payment > 0:
            self.money -= payment; self.debt -= payment; self.stress = max(0, self.stress - 5)
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
                self.actions_taken_this_month += 1; self.actions_remaining -= 1
                self.game_message = f"💵 Saved ${amount:.0f} | Actions: {self.actions_remaining}/{ACTIONS_PER_MONTH}"
                self.need_button_update = True
            else:
                self.game_message = "❌ Not enough money"
        elif action_type == 'withdraw':
            self._withdraw_emergency(amount)
        elif action_type == 'pay_debt':
            self.pay_off_debt(amount)
        self.close_dropdown()

    def _withdraw_emergency(self, amount):
        if self.actions_remaining <= 0: self.game_message = f"⚠️ No actions left!"; return
        withdrawal = min(amount, self.emergency_fund)
        if withdrawal > 0:
            self.emergency_fund -= withdrawal; self.money += withdrawal
            self.actions_taken_this_month += 1; self.actions_remaining -= 1
            self.game_message = f"🏦 Withdrew ${withdrawal:.0f} | Actions: {self.actions_remaining}/{ACTIONS_PER_MONTH}"
            self.need_button_update = True

    def handle_custom_input_submit(self):
        try:
            amount = float(self.custom_input_text)
            if amount <= 0 or amount > 100000:
                self.game_message = "❌ Amount must be between $1 and $100,000"; return
            self.execute_financial_action(self.custom_input_type, amount)
            self.show_custom_input = False; self.custom_input_text = ""
        except ValueError:
            self.game_message = "❌ Invalid amount"

    def treat_addiction(self):
        if self.actions_remaining <= 0: self.game_message = f"⚠️ No actions left!"; return
        if self.money < 1500: self.game_message = "Need $1500 for treatment"; return
        self.money -= 1500; self.actions_taken_this_month += 1; self.actions_remaining -= 1
        if random.random() < self.happiness / 100:
            self.debuffs = [d for d in self.debuffs if d != 'addict']
            self.happiness = min(100, self.happiness + 10)
            self.game_message = f"🏥 Addiction cured! | Actions: {self.actions_remaining}/{ACTIONS_PER_MONTH}"
            self._add_particle(self.screen.get_width()//2, self.screen.get_height()//2, COLOR_SUCCESS)
        else:
            self.game_message = f"❌ Treatment failed. | Actions: {self.actions_remaining}/{ACTIONS_PER_MONTH}"
        self.need_button_update = True

    def seek_therapy(self):
        if self.actions_remaining <= 0: self.game_message = f"⚠️ No actions left!"; return
        if self.money < 800: self.game_message = "Need $800 for therapy"; return
        self.money -= 800
        self.debuffs = [d for d in self.debuffs if d not in ['unhappy', 'distracted']]
        self.stress = max(0, self.stress - 20); self.happiness = min(100, self.happiness + 15)
        self.actions_taken_this_month += 1; self.actions_remaining -= 1
        self.game_message = f"🧠 Therapy successful! | Actions: {self.actions_remaining}/{ACTIONS_PER_MONTH}"
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
            self.high_score = score; self._save_high_score()
        self.game_message = reason or ('Game completed!' if completed else 'Game over!')
        self.state = GameState.GAME_OVER

    # -----------------------------------------------------------------------
    # DRAWING HELPERS
    # -----------------------------------------------------------------------

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

    # -----------------------------------------------------------------------
    # SCREEN DRAW METHODS
    # -----------------------------------------------------------------------

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
            self._draw_text(f"🏆 High Score: {self.high_score:,}", self.font_medium, COLOR_WARNING, SCREEN_WIDTH//2, 430, center=True)
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

    def _draw_setup(self, events):
        """Setup screen: class | education | difficulty + avatar picker row."""
        self._draw_gradient_background()
        self._draw_text("⚡ CHARACTER SETUP", self.font_large, COLOR_PRIMARY, SCREEN_WIDTH//2, 40, center=True, glow=True)

        # Three columns top
        section_width = 380
        gap = 35
        top_row_total = 3 * section_width + 2 * gap
        start_x = (SCREEN_WIDTH - top_row_total) // 2
        self._draw_class_selection(start_x, section_width, events)
        self._draw_education_selection(start_x + section_width + gap, section_width, events)
        self._draw_difficulty_selection(start_x + (section_width + gap) * 2, section_width, events)

        # Avatar picker below
        self._draw_avatar_selection(events)

        # Buttons
        self.cached_buttons[GameState.SETUP][0].enabled = all(
            [self.selected_class, self.selected_education, self.selected_difficulty])
        for btn in self.cached_buttons[GameState.SETUP]:
            font = self.font_small if btn.button_id == "setup_back" else self.font_medium
            btn.draw(self.screen, font)
        for event in events:
            for btn in self.cached_buttons[GameState.SETUP]:
                btn.handle_event(event)

    def _draw_avatar_selection(self, events):
        """Full-width avatar selection strip between the 3-column selectors and the Start button."""
        section_y = 680
        panel_x = 60
        panel_w = SCREEN_WIDTH - 120
        panel_h = 120

        # Panel background
        pygame.draw.rect(self.screen, COLOR_PANEL, (panel_x, section_y, panel_w, panel_h), border_radius=16)
        pygame.draw.rect(self.screen, COLOR_ACCENT, (panel_x, section_y, panel_w, panel_h), 2, border_radius=16)

        # Title
        self._draw_text("CHOOSE YOUR AVATAR", self.font_small, COLOR_ACCENT, panel_x + 20, section_y + 12)

        # Tiles
        num = len(AVATARS)
        tile_size = 68
        tile_gap = 10
        tiles_total_w = num * tile_size + (num - 1) * tile_gap
        # leave room on the right for the preview (≈130px)
        tile_start_x = panel_x + 20
        tile_y = section_y + 38

        mouse_pos = pygame.mouse.get_pos()

        for i, av in enumerate(AVATARS):
            tx = tile_start_x + i * (tile_size + tile_gap)
            tile_rect = pygame.Rect(tx, tile_y, tile_size, tile_size)
            is_selected = (i == self.selected_avatar_index)
            is_hovered = tile_rect.collidepoint(mouse_pos)

            # Background
            if is_selected:
                # Soft glow halo
                halo = pygame.Surface((tile_size + 12, tile_size + 12), pygame.SRCALPHA)
                pygame.draw.rect(halo, (*COLOR_PRIMARY, 55), (0, 0, tile_size+12, tile_size+12), border_radius=14)
                self.screen.blit(halo, (tx - 6, tile_y - 6))
                pygame.draw.rect(self.screen, COLOR_PRIMARY, tile_rect, border_radius=12)
                border_col, border_w = COLOR_PRIMARY, 3
            elif is_hovered:
                pygame.draw.rect(self.screen, COLOR_PANEL_HOVER, tile_rect, border_radius=12)
                border_col, border_w = COLOR_ACCENT, 2
            else:
                pygame.draw.rect(self.screen, (28, 42, 62), tile_rect, border_radius=12)
                border_col, border_w = COLOR_BORDER, 1

            pygame.draw.rect(self.screen, border_col, tile_rect, border_w, border_radius=12)

            # Emoji
            es = self.font_emoji_large.render(av["emoji"], True, COLOR_TEXT)
            self.screen.blit(es, es.get_rect(center=(tx + tile_size//2, tile_y + tile_size//2 - 6)))

            # Label
            lf = pygame.font.SysFont("Arial", 10)
            ls = lf.render(av["label"], True, COLOR_BG if is_selected else COLOR_TEXT_DIM)
            self.screen.blit(ls, ls.get_rect(center=(tx + tile_size//2, tile_y + tile_size - 10)))

            # Click
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if tile_rect.collidepoint(event.pos):
                        self.selected_avatar_index = i
                        self._add_particle(tx + tile_size//2, tile_y + tile_size//2, COLOR_ACCENT)

        # Live preview on the right side of the panel
        preview_x = panel_x + panel_w - 110
        preview_emoji = AVATARS[self.selected_avatar_index]["emoji"]
        preview_label = AVATARS[self.selected_avatar_index]["label"]

        pf = pygame.font.SysFont("Segoe UI Emoji", 42)
        ps = pf.render(preview_emoji, True, COLOR_TEXT)
        self.screen.blit(ps, ps.get_rect(center=(preview_x + 40, section_y + 52)))

        plf = pygame.font.SysFont("Arial", 13, bold=True)
        pls = plf.render(preview_label, True, COLOR_ACCENT)
        self.screen.blit(pls, pls.get_rect(center=(preview_x + 40, section_y + 95)))

    def _draw_class_selection(self, x, width, events):
        y = 90
        self._draw_text("SOCIAL CLASS", self.font_small, COLOR_ACCENT, x + width//2, y, center=True)
        y += 40
        for key, config in self.class_configs.items():
            color = COLOR_PRIMARY if self.selected_class == key else COLOR_PANEL
            text_color = COLOR_BG if self.selected_class == key else COLOR_TEXT
            btn = Button(x, y, width, 115, f"{config.avatar_emoji} {config.name}\n💰 ${config.starting_money:,.0f}\n💳 ${config.debt:,.0f}",
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
            cost_text = "🎓 Free" if config.cost == 0 else f"📚 ${config.cost:,}"
            btn = Button(x, y, width, 115, f"{config.name}\n💵 ${config.income:,.0f}/mo\n{cost_text}",
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
        draw_chatbot_icon(self.screen, 80, SCREEN_HEIGHT-80, self.chatbot.is_thinking, self.chatbot_has_new_message)
        if self.show_chatbot:
            modal_x, modal_y, modal_w, modal_h, history_rect = draw_chatbot_modal(self.screen, self.font_medium, self.chatbot)
            input_rect = pygame.Rect(modal_x+20, modal_y+modal_h-80, modal_w-100, 50)
            pygame.draw.rect(self.screen, COLOR_PANEL, input_rect, border_radius=10)
            pygame.draw.rect(self.screen, COLOR_PRIMARY, input_rect, 2, border_radius=10)
            send_btn = Button(modal_x+modal_w-70, modal_y+modal_h-80, 50, 50, "→", COLOR_SUCCESS, COLOR_BG, "send_chat", gradient=True)
            close_btn = Button(modal_x+modal_w-50, modal_y+20, 30, 30, "✕", COLOR_DANGER, COLOR_TEXT, "close_chat")
            cursor = "|" if pygame.time.get_ticks() % 1000 < 500 else " "
            display_text = (self.chatbot_input_text + cursor) if self.chatbot_input_active else (self.chatbot_input_text or "Ask for help...")
            self.screen.blit(self.font_tiny.render(display_text, True, COLOR_TEXT), (input_rect.x+10, input_rect.y+15))
            close_btn.draw(self.screen, self.font_small)
            send_btn.draw(self.screen, self.font_small)
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if close_btn.rect.collidepoint(event.pos): self._toggle_chatbot()
                    elif send_btn.rect.collidepoint(event.pos): self._send_chatbot_message()
                    elif input_rect.collidepoint(event.pos): self.chatbot_input_active = True
                    else: self.chatbot_input_active = False
                if event.type == pygame.KEYDOWN and self.chatbot_input_active:
                    if event.key == pygame.K_RETURN: self._send_chatbot_message()
                    elif event.key == pygame.K_BACKSPACE: self.chatbot_input_text = self.chatbot_input_text[:-1]
                    elif event.key == pygame.K_ESCAPE: self.chatbot_input_active = False
                    elif len(self.chatbot_input_text) < 50: self.chatbot_input_text += event.unicode
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if pygame.Rect(50, SCREEN_HEIGHT-110, 60, 60).collidepoint(event.pos):
                    self._toggle_chatbot()
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                for btn in self.cached_buttons[GameState.PLAYING]:
                    if btn.visible and btn.rect.collidepoint(event.pos) and hasattr(btn, 'lock_data') and btn.lock_data:
                        if self.locked_action and self.locked_action['callback'] == btn.lock_data['callback']:
                            self.locked_action = None; self.game_message = "🔓 Action unlocked"
                        else:
                            self.locked_action = btn.lock_data; self.game_message = f"🔒 Locked: {btn.lock_data['name']}"
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

        # Avatar bubble (uses chosen emoji)
        pygame.draw.circle(self.screen, COLOR_PRIMARY, (90, 40), 25)
        pygame.draw.circle(self.screen, COLOR_ACCENT, (90, 40), 27, 2)
        as_ = self.font_emoji_header.render(self.selected_avatar, True, COLOR_TEXT)
        self.screen.blit(as_, as_.get_rect(center=(90, 40)))

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
        self._draw_text("🧠 WELL-BEING", self.font_small, COLOR_ACCENT, p, sy)
        sy += 40
        self._draw_text(f"😊 Happiness: {self.happiness:.0f}%", self.font_small, COLOR_TEXT, p, sy)
        self._draw_progress_bar(p, sy+25, sidebar_w-60, 12, self.happiness, COLOR_SUCCESS)
        sy += 55
        self._draw_text(f"😰 Stress: {self.stress:.0f}%", self.font_small, COLOR_TEXT, p, sy)
        self._draw_progress_bar(p, sy+25, sidebar_w-60, 12, self.stress, COLOR_DANGER)
        sy += 65
        pygame.draw.line(self.screen, COLOR_PANEL_HOVER, (p, sy), (sidebar_w-p, sy)); sy += 25
        self._draw_text("💰 FINANCES", self.font_small, COLOR_ACCENT, p, sy); sy += 35
        for label, val, col in [
            ("📈 Income", f"+${self.monthly_income:,.0f}", COLOR_SUCCESS),
            ("📉 Expenses", f"-${(self.rent+self.groceries+self.transport):,.0f}", COLOR_DANGER),
            ("💳 Debt", f"${self.debt:,.0f}", COLOR_DANGER),
            ("📊 Investments", f"${self.investments:,.0f}", COLOR_PRIMARY),
            ("🏦 Emergency", f"${self.emergency_fund:,.0f}", COLOR_WARNING),
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
            self._draw_text("⚠️ Active Effects:", self.font_small, COLOR_DANGER, p, sy); sy += 30
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
        # Actions counter
        pygame.draw.rect(self.screen, COLOR_PANEL, (mx, controls_y, 160, 90), border_radius=15)
        pygame.draw.rect(self.screen, COLOR_BORDER, (mx, controls_y, 160, 90), 2, border_radius=15)
        self._draw_text("ACTIONS LEFT", self.font_tiny, COLOR_TEXT_DIM, mx+80, controls_y+15, center=True)
        ac = {3: (COLOR_SUCCESS, "FULL"), 2: (COLOR_SUCCESS, "GOOD"), 1: (COLOR_WARNING, "LOW")}.get(self.actions_remaining, (COLOR_DANGER, "NONE"))
        self._draw_text(str(self.actions_remaining), self.font_xl, ac[0], mx+80, controls_y+50, center=True, glow=True)
        self._draw_text(ac[1], self.font_tiny, ac[0], mx+80, controls_y+70, center=True)
        # Next month button
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
        self._draw_text("⚡ AVAILABLE ACTIONS", self.font_small, COLOR_PRIMARY, action_rect.x+20, header_height+20)
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
        self._draw_text("📚 GAME GUIDE", self.font_large, COLOR_PRIMARY, px+pw//2, py+40, center=True, glow=True)
        sections = [
            ("🎯 Goal", "Complete 24 months with high net worth and happiness!"),
            ("⚡ Actions", f"You have {ACTIONS_PER_MONTH} actions per month. Right-click to lock actions for next month."),
            ("💰 Financial Tips", "• Invest early for compound returns\n• Keep 3 months income as emergency fund\n• Pay off high-interest debt first"),
            ("😊 Well-being", "• Low happiness causes debuffs\n• High stress leads to burnout\n• Balance work and life!"),
            ("🎓 Education", "• Increases monthly income permanently\n• Costs added to debt\n• Higher education = higher income"),
            ("⚠️ Warning Signs", "• Red money = trouble ahead\n• Orange stress bar = burnout risk\n• Debuffs reduce your income"),
            ("💳 Financial Actions", "• Invest: Grow your wealth over time\n• Save: Build emergency fund\n• Withdraw: Take from emergency fund\n• Pay Debt: Reduce debt and stress"),
            ("🎮 Lifestyle Choices", "• Leisure: Boost happiness, reduce stress\n• Risky: Potential rewards but addiction risk\n• Education: Long-term income boost\n• Utilities: One-time purchases"),
            ("🔒 Lock System", "Right-click any action button to lock it. Locked actions automatically execute at the start of next month!"),
            ("🏆 Scoring", "Final score = Net Worth + Goal Bonuses + Happiness × 100 + Months × 500"),
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
            self._draw_text(f"💰 Cost: -${self.current_event.cost:,.0f}", self.font_medium, COLOR_DANGER, x+w//2, iy, center=True); iy += 35
        if self.current_event.stress_increase > 0:
            self._draw_text(f"😰 Stress: +{self.current_event.stress_increase}%", self.font_medium, COLOR_DANGER, x+w//2, iy, center=True)
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
            ("💰 Net Worth", f"${(self.money+self.investments+self.emergency_fund-self.debt):,.0f}"),
            ("😊 Happiness", f"{self.happiness:.0f}%"),
            ("🎯 Goals Met", f"{sum(1 for g in self.goals.values() if g['completed'])}/4"),
            ("📅 Months", f"{self.current_month}")
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
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = FinanceGame()
    game.run()