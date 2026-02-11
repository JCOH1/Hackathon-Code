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

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 900
FPS = 60

# --- THEME COLORS (Vibrant Financial Theme) ---
COLOR_BG = (10, 15, 25)          # Deep Navy
COLOR_PANEL = (20, 30, 45)       # Dark Slate
COLOR_PANEL_HOVER = (35, 50, 70) # Lighter Slate
COLOR_PRIMARY = (0, 200, 255)    # Bright Cyan
COLOR_SUCCESS = (0, 255, 150)    # Mint Green
COLOR_WARNING = (255, 200, 50)   # Gold
COLOR_DANGER = (255, 80, 80)     # Coral Red
COLOR_TEXT = (255, 255, 255)     # Pure White
COLOR_TEXT_DIM = (180, 200, 220) # Soft Blue-White
COLOR_ACCENT = (180, 100, 255)   # Soft Purple
COLOR_BORDER = (60, 80, 100)     # Steel Blue

# Gradient colors for visual flair
COLOR_GRADIENT_START = (0, 150, 255)   # Bright Blue
COLOR_GRADIENT_END = (100, 50, 200)    # Deep Purple

# Game Configuration - MUST BE BEFORE AI CHATBOT
MONTHS_PER_GAME = 24
STARTING_HAPPINESS = 50
BURNOUT_STRESS = 100
BURNOUT_HAPPINESS = 10
ACTIONS_PER_MONTH = 3

# ============================================================
# SIMPLE HINT CHATBOT - No LangChain dependencies, works immediately
# ============================================================

class SimpleHintBot:
    """Simple hint system without LangChain dependencies"""
    
    def __init__(self):
        self.name = "Finley"
        self.avatar = "🦊"
        self.enabled = True
        self.is_thinking = False
        self.last_response = "Hi! I'm Finley, your financial assistant! Ask me for tips! 🦊"
        self.ready = True
        
        # Pre-defined hints and tips
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
        """Simple keyword-based hint system"""
        self.is_thinking = True
        question = question.lower()
        
        # Add game context if available
        context = ""
        if game_state:
            context = f"(Month {game_state.get('month', 0)} - "
            context += f"Cash: ${game_state.get('money', 0):,.0f}) "
        
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
        elif "help" in question or "what" in question or "how" in question or "?" in question:
            response = random.choice(self.hints["general"])
        else:
            response = random.choice(self.hints["general"])
        
        self.last_response = context + response
        self.is_thinking = False
        return self.last_response
    
    def get_context_from_game(self, game):
        """Extract relevant game state for context"""
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
        """Reset the conversation"""
        self.last_response = "Conversation reset! How can I help you? 🦊"

# Initialize global chatbot instance
finance_chatbot = SimpleHintBot()

# ============================================================
# AI Chatbot UI Components
# ============================================================

def draw_chatbot_icon(screen, x, y, is_thinking=False, has_new_message=False):
    """Draw a cute chatbot icon in the corner"""
    # Draw circular background
    pygame.draw.circle(screen, COLOR_ACCENT, (x, y), 30)
    pygame.draw.circle(screen, COLOR_PRIMARY, (x, y), 32, 2)
    
    # Draw avatar
    font = pygame.font.SysFont("Arial", 36, bold=True)
    text = font.render("🦊", True, COLOR_TEXT)
    text_rect = text.get_rect(center=(x, y))
    screen.blit(text, text_rect)
    
    # Thinking animation
    if is_thinking:
        t = pygame.time.get_ticks() * 0.01
        dots = "." * (int(t) % 4)
        font_small = pygame.font.SysFont("Arial", 14)
        thinking_text = font_small.render(f"thinking{dots}", True, COLOR_TEXT_DIM)
        screen.blit(thinking_text, (x - 30, y + 35))
    
    # Notification dot for new message
    if has_new_message and not is_thinking:
        pygame.draw.circle(screen, COLOR_SUCCESS, (x + 20, y - 20), 8)
        pygame.draw.circle(screen, COLOR_TEXT, (x + 20, y - 20), 10, 1)

def draw_chatbot_modal(screen, font, chatbot, game_state=None):
    """Draw the chatbot conversation modal"""
    modal_w, modal_h = 500, 600
    modal_x = SCREEN_WIDTH - modal_w - 30
    modal_y = 100
    
    # Draw modal background
    pygame.draw.rect(screen, COLOR_BG, (modal_x, modal_y, modal_w, modal_h), border_radius=20)
    pygame.draw.rect(screen, COLOR_ACCENT, (modal_x, modal_y, modal_w, modal_h), 3, border_radius=20)
    
    # Header
    pygame.draw.rect(screen, COLOR_PANEL, (modal_x, modal_y, modal_w, 70), 
                    border_top_left_radius=20, border_top_right_radius=20)
    
    # Avatar and title
    avatar_font = pygame.font.SysFont("Arial", 40)
    avatar_text = avatar_font.render("🦊", True, COLOR_TEXT)
    screen.blit(avatar_text, (modal_x + 20, modal_y + 15))
    
    title_font = pygame.font.SysFont("Arial", 24, bold=True)
    title_text = title_font.render(f"{chatbot.name} - Financial Assistant", True, COLOR_PRIMARY)
    screen.blit(title_text, (modal_x + 80, modal_y + 25))
    
    # Conversation history area
    history_rect = pygame.Rect(modal_x + 20, modal_y + 90, modal_w - 40, modal_h - 180)
    pygame.draw.rect(screen, COLOR_PANEL, history_rect, border_radius=10)
    
    # Display last response
    y_offset = modal_y + 110
    font_small = pygame.font.SysFont("Arial", 16)
    
    # Bot message
    bot_bubble = pygame.Rect(modal_x + 30, y_offset, modal_w - 100, 80)
    pygame.draw.rect(screen, COLOR_PANEL_HOVER, bot_bubble, border_radius=15)
    pygame.draw.rect(screen, COLOR_ACCENT, bot_bubble, 1, border_radius=15)
    
    # Word wrap for bot message
    words = chatbot.last_response.split()
    lines = []
    current_line = []
    for word in words:
        current_line.append(word)
        test_line = ' '.join(current_line)
        if font_small.size(test_line)[0] > modal_w - 140:
            current_line.pop()
            lines.append(' '.join(current_line))
            current_line = [word]
    if current_line:
        lines.append(' '.join(current_line))
    
    for i, line in enumerate(lines[:4]):  # Show max 4 lines
        text = font_small.render(line, True, COLOR_TEXT)
        screen.blit(text, (modal_x + 45, y_offset + 10 + i * 20))
    
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
    """Enhanced button class with animations and visual effects"""
    
    def __init__(self, x: int, y: int, width: int, height: int, text: str, 
                 color=COLOR_PANEL, text_color=COLOR_TEXT, button_id: str = "", tooltip: str = "",
                 gradient: bool = False, icon: str = None):
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
        
        # Pulse animation for primary buttons
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

        # Draw shadow with glow effect on hover
        if self.enabled:
            shadow_offset = 6 if self.hover else 3
            shadow_alpha = 100 if self.hover else 50
            shadow_surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            shadow_surf.fill((0, 0, 0, shadow_alpha))
            screen.blit(shadow_surf, (self.rect.x + shadow_offset, self.rect.y + shadow_offset + pulse_offset))
        
        # Draw gradient background if specified
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
        
        # Draw border with glow
        border_width = 3 if self.hover else 2
        if self.enabled:
            button_rect = pygame.Rect(self.rect.x, self.rect.y - pulse_offset, self.rect.width, self.rect.height)
            pygame.draw.rect(screen, border_color, button_rect, border_width, border_radius=12)
        
        # Prepare text with icon if available
        display_text = self.text
        if self.icon:
            display_text = f"{self.icon} {self.text}"
        
        lines, surfaces = self._get_cached_text(font, draw_text_color)
        total_height = len(lines) * font.get_linesize()
        start_y = button_rect.centery - total_height // 2
        
        for i, text_surface in enumerate(surfaces):
            text_rect = text_surface.get_rect(
                center=(button_rect.centerx, start_y + i * font.get_linesize() + font.get_linesize()//2)
            )
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
        
        # Draw tooltip with gradient
        tooltip_rect = pygame.Rect(tooltip_x, tooltip_y, tooltip_width, tooltip_height)
        
        # Gradient background
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
    """Main game class with enhanced visual design"""
    
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("FinanceQuest - Master Your Financial Future")
        self.clock = pygame.time.Clock()
        
        # Set window icon (if available)
        pygame.display.set_icon(self.screen)
        
        pygame.event.set_allowed([
            pygame.QUIT, 
            pygame.MOUSEBUTTONDOWN, 
            pygame.MOUSEMOTION,
            pygame.MOUSEWHEEL
        ])
        
        self._init_fonts()
        
        # Game state
        self.state = GameState.TITLE
        self.tutorial_step = 0
        
        # Setup choices
        self.selected_class = None
        self.selected_education = None
        self.selected_difficulty = None
        
        # Particle effects
        self.particles = []
        
        # Player stats
        self._init_player_stats()
        
        # Game state variables
        self.debuffs = []
        self.months_no_income = 0
        self.has_vehicle = False
        self.current_education_level = 'polytechnic'
        self.has_university = False
        self.has_masters = False
        self.game_message = ""
        self.high_score = self._load_high_score()
        
        # Goals
        self._init_goals()
        
        # Event modal
        self.show_event_modal = False
        self.current_event = None
        
        # Scroll offset for actions
        self.scroll_offset = 0
        self.max_scroll = 0
        
        # Help panel scroll
        self.help_scroll_offset = 0
        self.help_max_scroll = 0
        
        # UI cache
        self.cached_buttons = {state: [] for state in GameState}
        self.need_button_update = True
        
        self._bg_cache = {}
        
        self._init_configs()
        self._init_ui_elements()
        
        # Dropdown system
        self.active_dropdown = None
        self.dropdown_hover = False
        self.dropdown_last_hover_time = 0
        self.dropdown_stay_duration = 2000
        
        # Custom input modal
        self.show_custom_input = False
        self.custom_input_text = ""
        self.custom_input_type = ""

        # AI Chatbot
        self.show_chatbot = False
        self.chatbot_input_text = ""
        self.chatbot_input_active = False
        self.chatbot = finance_chatbot
        self.chatbot_has_new_message = False
        
    def _init_fonts(self):
        """Initialize all fonts with better typography"""
        self.font_xl = pygame.font.SysFont("Arial Black", 72, bold=True)
        self.font_large = pygame.font.SysFont("Arial", 48, bold=True)
        self.font_medium = pygame.font.SysFont("Arial", 28, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 20, bold=True)
        self.font_tiny = pygame.font.SysFont("Arial", 16)
        self.font_digital = pygame.font.SysFont("Courier New", 32, bold=True)
    
    def _init_player_stats(self):
        """Initialize player statistics"""
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
        
        # Action tracking
        self.actions_taken_this_month = 0
        self.actions_remaining = ACTIONS_PER_MONTH
        self.locked_action = None
        
        # Help system
        self.show_help_panel = False
        self.current_tooltip = ""
        
        # Avatar
        self.selected_avatar = "👤"
        
        self.active_dropdown = None
        self.dropdown_hover = False
        self.dropdown_last_hover_time = 0
        self.dropdown_stay_duration = 2000
        
        self.show_custom_input = False
        self.custom_input_text = ""
        self.custom_input_type = ""
        
        # Help scroll
        self.help_scroll_offset = 0
        self.help_max_scroll = 0

    def _toggle_chatbot(self):
        """Toggle the AI chatbot modal"""
        self.show_chatbot = not self.show_chatbot
        self.chatbot_input_active = False
        if self.show_chatbot:
            self.chatbot_has_new_message = False

    def _send_chatbot_message(self):
        """Send a message to the AI chatbot"""
        if not self.chatbot_input_text.strip():
            return
        
        question = self.chatbot_input_text
        self.chatbot_input_text = ""
        
        # Get game context
        context = self.chatbot.get_context_from_game(self)
        
        # Run in thread to avoid freezing UI
        def ask_ai():
            self.chatbot.ask(question, context)
            self.chatbot_has_new_message = True
        
        threading.Thread(target=ask_ai, daemon=True).start()
    
    def _add_particle(self, x, y, color):
        """Add a particle effect"""
        self.particles.append({
            'x': x,
            'y': y,
            'vx': random.uniform(-2, 2),
            'vy': random.uniform(-3, 1),
            'life': 60,
            'color': color,
            'size': random.randint(2, 4)
        })
    
    def _update_particles(self):
        """Update particle effects"""
        for particle in self.particles[:]:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['vy'] += 0.1
            particle['life'] -= 1
            if particle['life'] <= 0:
                self.particles.remove(particle)
    
    def _draw_particles(self):
        """Draw particle effects"""
        for particle in self.particles:
            alpha = min(255, particle['life'] * 4)
            color = (*particle['color'][:3], alpha)
            pygame.draw.circle(self.screen, color[:3], 
                             (int(particle['x']), int(particle['y'])), 
                             particle['size'])
    
    def _init_goals(self):
        """Initialize game goals"""
        self.goals = {
            'netWorth': {'target': 50000, 'completed': False, 'label': 'Net Worth $50k'},
            'emergencyFund': {'target': 10000, 'completed': False, 'label': 'Save $10k Fund'},
            'debtFree': {'completed': False, 'label': 'Become Debt-Free'},
            'happiness': {'target': 70, 'completed': False, 'label': '70+ Happiness'}
        }
        
    def _init_configs(self):
        """Initialize all game configurations"""
        self.class_configs = {
            'upper': ClassConfig(
                "Upper Class", 50000, 2500, 800, 400, 0,
                "No debt - Start with financial freedom", "💼"
            ),
            'middle': ClassConfig(
                "Middle Class", 15000, 1500, 500, 300, 5000,
                "Some starting debt - Balanced start", "👔"
            ),
            'lower': ClassConfig(
                "Lower Class", 2000, 800, 300, 150, 15000,
                "Significant debt - Challenging start", "🎒"
            )
        }
        
        self.education_configs = {
            'polytechnic': EducationConfig(
                "Polytechnic", 0, 3500,
                "Standard education - No debt"
            ),
            'university': EducationConfig(
                "University", 30000, 5000,
                "Higher earning potential, high debt"
            ),
            'masters': EducationConfig(
                "Masters", 50000, 6500,
                "Max earning potential, massive debt"
            )
        }
        
        self.difficulty_configs = {
            'easy': DifficultyConfig(
                "Easy Mode", 0.05, 0.5,
                "🟢 Fewer emergencies, stable markets"
            ),
            'normal': DifficultyConfig(
                "Normal Mode", 0.10, 1.0,
                "🟡 Balanced challenge"
            ),
            'hard': DifficultyConfig(
                "Hard Mode", 0.20, 1.5,
                "🔴 Frequent emergencies, volatile markets"
            )
        }
        
        self.life_choices = {
            'vacation': LifeChoice("Vacation", 2500, 15, -10, "leisure"),
            'fineDining': LifeChoice("Fine Dining", 500, 8, -3, "leisure"),
            'staycation': LifeChoice("Staycation", 800, 10, -5, "leisure"),
            'themePark': LifeChoice("Theme Park", 300, 12, -4, "leisure"),
            'shopping': LifeChoice("Shopping", 1000, 10, -5, "risky", 0.3, "addict"),
            'gambling': LifeChoice("Gambling", 1500, 5, 0, "risky", 0.4, "addict", 0.2, 3000),
            'clubbing': LifeChoice("Clubbing", 600, 8, -3, "risky", 0.25, "addict"),
            'smoking': LifeChoice("Smoking", 200, 2, -8, "risky", 0.5, "addict"),
            'vehicle': LifeChoice("Buy Vehicle", 25000, 20, 0, "utility", one_time=True),
            'relationship': LifeChoice("Date Night", 500, 15, -5, "utility"),
            'university': LifeChoice("University", 30000, 0, 0, "education", one_time=True),
            'masters': LifeChoice("Masters", 50000, 0, 0, "education", one_time=True)
        }
        
        self.emergency_events = [
            EmergencyEvent("🚑 Medical Emergency", 
                        "You've been diagnosed with a serious health condition requiring immediate treatment.",
                        cost=8000, stress_increase=30),
            EmergencyEvent("💼 Job Loss",
                        "Your company has downsized and you've been laid off. No income for 3 months.",
                        months_no_income=3, stress_increase=40),
            EmergencyEvent("📉 Market Crash",
                        "The stock market has crashed! Your investments have lost significant value.",
                        investment_loss=0.4, stress_increase=25),
            EmergencyEvent("🏠 Home Emergency",
                        "Major repairs needed for your living space.",
                        cost=3500, stress_increase=15),
            EmergencyEvent("👨‍👩‍👧 Family Emergency",
                            "A family member needs financial assistance urgently.",
                            cost=5000, stress_increase=20)
        ]
    
    def _init_ui_elements(self):
        """Initialize all UI buttons once"""
        self._init_title_buttons()
        self._init_tutorial_buttons()
        self._init_setup_buttons()
        self._init_game_over_buttons()
        
    def _init_title_buttons(self):
        """Initialize title screen buttons"""
        self.cached_buttons[GameState.TITLE] = [
            Button(SCREEN_WIDTH // 2 - 150, 500, 300, 70, "New Game", 
                  COLOR_PRIMARY, text_color=COLOR_BG, button_id="new_game", 
                  gradient=True, icon="🎮"),
            Button(SCREEN_WIDTH // 2 - 150, 590, 300, 70, "Skip Tutorial", COLOR_PANEL, 
                  text_color=COLOR_TEXT, button_id="skip_tutorial", icon="⏩"),
            Button(SCREEN_WIDTH - 150, 20, 130, 50, "Help", COLOR_ACCENT, 
                  text_color=COLOR_TEXT, button_id="help_title", icon="❓")
        ]
        
        self.cached_buttons[GameState.TITLE][0].callback = lambda: setattr(self, 'state', GameState.TUTORIAL)
        self.cached_buttons[GameState.TITLE][1].callback = lambda: setattr(self, 'state', GameState.SETUP)
        self.cached_buttons[GameState.TITLE][2].callback = self._toggle_help
    
    def _init_tutorial_buttons(self):
        """Initialize tutorial screen buttons"""
        panel_rect = pygame.Rect(200, 150, SCREEN_WIDTH - 400, 500)
        btn_y = panel_rect.bottom - 90
        
        self.cached_buttons[GameState.TUTORIAL] = [
            Button(panel_rect.left + 50, btn_y, 180, 50, "Previous", 
                  COLOR_PANEL_HOVER, button_id="tut_prev", icon="◀"),
            Button(panel_rect.right - 230, btn_y, 180, 50, "Next", 
                  COLOR_PRIMARY, text_color=COLOR_BG, button_id="tut_next", 
                  gradient=True, icon="▶"),
            Button(SCREEN_WIDTH - 250, 800, 200, 50, "Skip All", 
                  COLOR_PANEL, button_id="tut_skip", icon="⏭")
        ]
        
        self.cached_buttons[GameState.TUTORIAL][0].callback = self._tut_prev
        self.cached_buttons[GameState.TUTORIAL][1].callback = self._tut_next
        self.cached_buttons[GameState.TUTORIAL][2].callback = self._tut_skip
    
    def _init_setup_buttons(self):
        """Initialize setup screen buttons"""
        self.cached_buttons[GameState.SETUP] = [
            Button(SCREEN_WIDTH // 2 - 120, 750, 240, 60, "Start Journey", 
                  COLOR_SUCCESS, text_color=COLOR_BG, button_id="setup_start", 
                  gradient=True, icon="🚀"),
            Button(SCREEN_WIDTH // 2 - 80, 830, 160, 40, "Back", 
                  COLOR_PANEL, button_id="setup_back", icon="↩")
        ]
        
        self.cached_buttons[GameState.SETUP][0].callback = self.start_game
        self.cached_buttons[GameState.SETUP][1].callback = lambda: setattr(self, 'state', GameState.TITLE)
    
    def _init_game_over_buttons(self):
        """Initialize game over screen buttons"""
        self.cached_buttons[GameState.GAME_OVER] = [
            Button(SCREEN_WIDTH//2 - 220, 680, 200, 60, "Play Again", 
                  COLOR_SUCCESS, text_color=COLOR_BG, button_id="play_again", 
                  gradient=True, icon="🔄"),
            Button(SCREEN_WIDTH//2 + 20, 680, 200, 60, "Main Menu", 
                  COLOR_PANEL, button_id="menu", icon="🏠")
        ]
        
        self.cached_buttons[GameState.GAME_OVER][0].callback = self._reset_for_new_game
        self.cached_buttons[GameState.GAME_OVER][1].callback = lambda: setattr(self, 'state', GameState.TITLE)
    
    def _reset_for_new_game(self):
        """Reset game state for a new game"""
        self.state = GameState.SETUP
        self.tutorial_step = 0
        self.selected_class = None
        self.selected_education = None
        self.selected_difficulty = None
        self.need_button_update = True
        
    def _init_playing_buttons(self):
        """Initialize playing screen buttons"""
        if self.cached_buttons[GameState.PLAYING]:
            return
        
        # Next Month button
        next_btn = Button(0, 0, 200, 80, "NEXT MONTH", 
                        COLOR_SUCCESS, text_color=COLOR_BG, button_id="next_month",
                        gradient=True)
        next_btn.callback = self.next_month
        self.cached_buttons[GameState.PLAYING].append(next_btn)
        
        # Help button (top right)
        help_btn = Button(SCREEN_WIDTH - 120, 20, 100, 40, "HELP", COLOR_ACCENT, 
                        text_color=COLOR_TEXT, button_id="help")
        help_btn.callback = self._toggle_help
        self.cached_buttons[GameState.PLAYING].append(help_btn)
        
        # AI Chatbot button (top right, next to help)
        chatbot_btn = Button(SCREEN_WIDTH - 230, 20, 100, 40, "ASK AI", COLOR_PRIMARY,
                        text_color=COLOR_BG, button_id="chatbot", gradient=True, icon="🦊")
        chatbot_btn.callback = self._toggle_chatbot
        self.cached_buttons[GameState.PLAYING].append(chatbot_btn)
        
    def _update_playing_buttons(self):
        """Update playing screen buttons based on current game state"""
        # Keep only the Next Month and Help buttons
        self.cached_buttons[GameState.PLAYING] = [
            btn for btn in self.cached_buttons[GameState.PLAYING] 
            if btn.button_id in ["next_month", "help", "chatbot"]
        ]
        
        # Create action buttons
        self._create_action_buttons()
        self.need_button_update = False
    
    def _create_action_buttons(self):
        """Create action buttons for the right sidebar"""
        header_height = 80
        action_panel_w = 400
        sidebar_w = 350
        main_area_w = SCREEN_WIDTH - sidebar_w - action_panel_w
        view_rect = pygame.Rect(sidebar_w + main_area_w + 10, 
                              header_height + 10, 
                              action_panel_w - 20, 
                              SCREEN_HEIGHT - header_height - 100)
        
        btn_w = (view_rect.width - 20) // 2
        btn_h = 60
        ay = 10
        
        # --- SECTION 1: FINANCIAL ACTIONS ---
        fin_actions = [
            ("💰 Invest", 'invest', self.money >= 100, COLOR_PRIMARY, 
             f"Invest in the market | Actions: {self.actions_remaining}/{ACTIONS_PER_MONTH}"),
            ("💵 Save", 'save', self.money >= 100, COLOR_SUCCESS,
             f"Save to emergency fund | Actions: {self.actions_remaining}/{ACTIONS_PER_MONTH}"),
            ("🏦 Withdraw", 'withdraw', self.emergency_fund > 0, COLOR_WARNING,
             f"Withdraw from emergency fund | Actions: {self.actions_remaining}/{ACTIONS_PER_MONTH}"),
            ("💳 Pay Debt", 'pay_debt', self.money >= 100 and self.debt > 0, COLOR_DANGER,
             f"Pay off debt and reduce stress | Actions: {self.actions_remaining}/{ACTIONS_PER_MONTH}"),
        ]
        ay = self._create_financial_dropdown_buttons("FINANCIAL ACTIONS", fin_actions, ay, btn_w, btn_h, view_rect)
        
        # --- SECTION 2: LIFESTYLE ---
        if self.happiness < 80:
            lifestyle_actions = [
                (f"{c.name}\n${c.cost:,.0f}", lambda k=k: self.take_life_choice(k), 
                 self.money >= c.cost, COLOR_PANEL,
                 f"😊 {c.name}: +{c.happiness} happiness, {c.stress} stress")
                for k, c in self.life_choices.items() if c.choice_type == 'leisure'
            ]
            if lifestyle_actions:
                ay = self._create_section_buttons("LIFESTYLE", lifestyle_actions, ay, btn_w, btn_h, view_rect)
        
        # --- SECTION 3: GROWTH & ASSETS ---
        util_actions = []
        for k, c in self.life_choices.items():
            if c.choice_type in ['utility', 'education']:
                enabled = self._is_choice_available(k, c)
                col = COLOR_ACCENT if c.choice_type == 'education' else COLOR_PANEL
                tooltip = f"📚 {c.name}: +${c.cost:,.0f} investment in your future!" if c.choice_type == 'education' else f"🎁 {c.name}"
                util_actions.append((f"{c.name}\n${c.cost:,.0f}", lambda k=k: self.take_life_choice(k), enabled, col, tooltip))
        
        if util_actions:
            ay = self._create_section_buttons("GROWTH & ASSETS", util_actions, ay, btn_w, btn_h, view_rect)
        
        # --- SECTION 4: HEALTH ---
        if self.debuffs:
            health_actions = []
            if 'addict' in self.debuffs:
                health_actions.append(("🏥 Rehab\n$1.5k", self.treat_addiction, self.money >= 1500, COLOR_DANGER,
                                      "Treatment for addiction - Success rate based on happiness"))
            if 'unhappy' in self.debuffs or 'distracted' in self.debuffs:
                health_actions.append(("🧠 Therapy\n$800", self.seek_therapy, self.money >= 800, COLOR_ACCENT,
                                      "Clear debuffs and reduce stress significantly"))
            
            if health_actions:
                ay = self._create_section_buttons("HEALTH", health_actions, ay, btn_w, btn_h, view_rect)
        
        self.max_scroll = max(0, ay - view_rect.height + 100)

    def _is_choice_available(self, choice_key: str, choice: LifeChoice) -> bool:
        """Check if a life choice is available"""
        if self.money < choice.cost:
            return False
        if choice_key == 'vehicle' and self.has_vehicle:
            return False
        if choice_key == 'university' and self.has_university:
            return False
        if choice_key == 'masters' and (self.has_masters or not self.has_university):
            return False
        return True
    
    def _create_section_buttons(self, title: str, buttons_data: list, 
                               start_y: int, btn_w: int, btn_h: int, view_rect) -> int:
        """Create buttons for a section in a 2-column grid layout"""
        ay = start_y + 50
        
        for i, b_data in enumerate(buttons_data):
            label, callback, enabled, color, tooltip = b_data
            
            bx_rel = 0 if i % 2 == 0 else btn_w + 15
            by_rel = ay + (i // 2) * (btn_h + 15)
            
            screen_x = view_rect.x + bx_rel
            screen_y = view_rect.y + by_rel - self.scroll_offset
            original_y = view_rect.y + by_rel
            
            is_locked = (self.locked_action and 
                        self.locked_action['callback'] == callback)
            
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

    def _create_financial_dropdown_buttons(self, title: str, buttons_data: list, 
                                          start_y: int, btn_w: int, btn_h: int, view_rect) -> int:
        """Create dropdown-enabled financial buttons in 2-column grid"""
        ay = start_y + 50
        
        for i, b_data in enumerate(buttons_data):
            label, action_type, enabled, color, tooltip = b_data
            
            bx_rel = 0 if i % 2 == 0 else btn_w + 15
            by_rel = ay + (i // 2) * (btn_h + 15)
            
            screen_x = view_rect.x + bx_rel
            screen_y = view_rect.y + by_rel - self.scroll_offset
            original_y = view_rect.y + by_rel
            
            btn = Button(screen_x, screen_y, btn_w, btn_h, label, color, 
                        button_id=f"financial_{action_type}", 
                        tooltip=tooltip)
            btn.original_y = original_y
            btn.enabled = enabled and self.actions_remaining > 0
            btn.action_type = action_type
            btn.visible = True
            
            self.cached_buttons[GameState.PLAYING].append(btn)
        
        rows = (len(buttons_data) + 1) // 2
        return ay + rows * (btn_h + 15) + 30
    
    def _update_button_positions(self):
        """Update button positions based on scroll offset"""
        if not self.cached_buttons[GameState.PLAYING]:
            return
            
        header_height = 80
        action_panel_w = 400
        sidebar_w = 350
        main_area_w = SCREEN_WIDTH - sidebar_w - action_panel_w
        view_rect = pygame.Rect(sidebar_w + main_area_w + 10, 
                              header_height + 10, 
                              action_panel_w - 20, 
                              SCREEN_HEIGHT - header_height - 100)
        
        for btn in self.cached_buttons[GameState.PLAYING]:
            if btn.button_id not in ["next_month", "help", "chatbot"]:
                new_y = btn.original_y - self.scroll_offset
                btn.rect.y = new_y
                btn.visible = (new_y + btn.rect.height > view_rect.y and new_y < view_rect.bottom)
    
    def _load_high_score(self) -> int:
        """Load high score from file"""
        try:
            if os.path.exists('highscore.json'):
                with open('highscore.json', 'r') as f:
                    data = json.load(f)
                    return data.get('high_score', 0)
        except Exception:
            pass
        return 0
    
    def _save_high_score(self):
        """Save high score to file"""
        try:
            with open('highscore.json', 'w') as f:
                json.dump({'high_score': self.high_score}, f)
        except Exception:
            pass
    
    def _toggle_help(self):
        """Toggle help panel and reset scroll"""
        self.show_help_panel = not self.show_help_panel
        self.help_scroll_offset = 0  # Reset scroll when opening
    
    def start_game(self):
        """Start a new game with selected configuration"""
        if not all([self.selected_class, self.selected_education, self.selected_difficulty]):
            return
            
        class_config = self.class_configs[self.selected_class]
        edu_config = self.education_configs[self.selected_education]
        
        self.money = class_config.starting_money
        self.monthly_income = edu_config.income
        self.debt = class_config.debt + edu_config.cost
        self.rent = class_config.rent
        self.groceries = class_config.groceries
        self.transport = class_config.transport
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
        
        self.selected_avatar = class_config.avatar_emoji
        
        self.actions_taken_this_month = 0
        self.actions_remaining = ACTIONS_PER_MONTH
        self.locked_action = None
        
        for goal in self.goals.values():
            goal['completed'] = False
        
        self._init_playing_buttons()
        self.need_button_update = True
        self.state = GameState.PLAYING
    
    def _tut_prev(self):
        """Go to previous tutorial step"""
        if self.tutorial_step > 0:
            self.tutorial_step -= 1
    
    def _tut_next(self):
        """Go to next tutorial step or finish tutorial"""
        if self.tutorial_step < 3:
            self.tutorial_step += 1
        else:
            self.state = GameState.SETUP
            self.tutorial_step = 0
    
    def _tut_skip(self):
        """Skip tutorial"""
        self.state = GameState.SETUP
        self.tutorial_step = 0
    
    def next_month(self):
        """Advance to next month and process all game logic"""
        if self.current_month >= MONTHS_PER_GAME:
            self.end_game(True)
            return
        
        messages = []
        
        self._add_particle(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, COLOR_SUCCESS)
        
        if self.locked_action:
            messages.append(f"🔒 Auto: {self.locked_action['name']}")
            self.locked_action['callback']()
        
        messages.extend(self._process_income())
        self._process_expenses()
        
        if self.debt > 0:
            self.debt *= 1.00417
        
        if self.investments > 0:
            self._process_investments()
        
        if self.emergency_fund > 0:
            self.emergency_fund *= 1.00167
        
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
    
    def _process_income(self) -> List[str]:
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
        total_expenses = self.rent + self.groceries + self.transport
        self.money -= total_expenses
    
    def _process_investments(self):
        difficulty = self.difficulty_configs[self.selected_difficulty]
        monthly_return = (random.random() * 0.25 - 0.10) / 12 * difficulty.market_volatility
        self.investments *= (1 + monthly_return)
    
    def _update_wellbeing(self, messages: List[str]):
        self.stress = max(0, self.stress - 2)
        debt_to_income = self.debt / (self.monthly_income * 12) if self.monthly_income > 0 else 0
        if debt_to_income > 0.5:
            self.stress += 5
        if self.emergency_fund < self.monthly_income * 3:
            self.stress += 2
        self.happiness = max(0, self.happiness - 3)
        if 'unhappy' in self.debuffs:
            messages.append("You are unhappy!")
        if self.stress >= BURNOUT_STRESS or self.happiness <= BURNOUT_HAPPINESS:
            self._trigger_burnout()
        self.stress = min(100, self.stress)
        self.happiness = min(100, self.happiness)
    
    def _trigger_burnout(self):
        burnout_event = EmergencyEvent(
            "🔥 BURNOUT!",
            "You've reached your breaking point. Forced medical leave.",
            cost=2000,
            months_no_income=2,
            stress_increase=0
        )
        self.trigger_event(burnout_event)
        self.stress = 50
        if 'unhappy' not in self.debuffs:
            self.debuffs.append('unhappy')
    
    def _check_random_events(self):
        difficulty = self.difficulty_configs[self.selected_difficulty]
        if random.random() < difficulty.emergency_chance:
            event = random.choice(self.emergency_events)
            self.trigger_event(event)
        debuff_chance = 0.5 - (self.happiness / 100) * 0.4
        if random.random() < debuff_chance and 'distracted' not in self.debuffs:
            self.debuffs.append('distracted')
            self.stress += 10
    
    def trigger_event(self, event: EmergencyEvent):
        self.current_event = event
        self.show_event_modal = True
    
    def handle_event_close(self):
        if self.current_event:
            if self.current_event.cost > 0:
                self.money -= self.current_event.cost
                self._add_particle(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, COLOR_DANGER)
            if self.current_event.stress_increase > 0:
                self.stress = min(100, self.stress + self.current_event.stress_increase)
            if self.current_event.months_no_income > 0:
                self.months_no_income = self.current_event.months_no_income
            if self.current_event.investment_loss > 0:
                self.investments *= (1 - self.current_event.investment_loss)
        self.show_event_modal = False
        self.current_event = None
        self.need_button_update = True
    
    def take_life_choice(self, choice_key: str):
        if self.actions_remaining <= 0:
            self.game_message = f"⚠️ No actions left! ({self.actions_taken_this_month}/{ACTIONS_PER_MONTH})"
            return
        choice = self.life_choices[choice_key]
        if not self._validate_life_choice(choice_key, choice):
            return
        self.money -= choice.cost
        self.actions_taken_this_month += 1
        self.actions_remaining -= 1
        if choice.happiness > 0:
            self._add_particle(self.screen.get_width() // 2, self.screen.get_height() // 2, COLOR_SUCCESS)
        if choice.choice_type == 'education':
            self._handle_education_upgrade(choice_key, choice)
            return
        self.happiness = min(100, self.happiness + choice.happiness)
        self.stress = max(0, self.stress + choice.stress)
        if choice.choice_type == 'risky':
            if self._handle_risky_choice(choice_key, choice):
                return
        if choice_key == 'vehicle':
            self.has_vehicle = True
        self.game_message = f"✨ {choice.name}: Happiness +{choice.happiness:.0f} | Actions: {self.actions_remaining}/{ACTIONS_PER_MONTH}"
        self.need_button_update = True
    
    def _validate_life_choice(self, choice_key: str, choice: LifeChoice) -> bool:
        if choice.one_time and choice_key == 'vehicle' and self.has_vehicle:
            self.game_message = "You already own a vehicle!"
            return False
        if choice_key == 'university' and self.has_university:
            self.game_message = "You already have a degree!"
            return False
        if choice_key == 'masters':
            if self.has_masters:
                self.game_message = "Already have a master's!"
                return False
            if not self.has_university:
                self.game_message = "Need University degree first!"
                return False
        if self.money < choice.cost:
            self.game_message = "Not enough money!"
            return False
        return True
    
    def _handle_education_upgrade(self, choice_key: str, choice: LifeChoice):
        if choice_key == 'university':
            self.monthly_income += 1500
            self.has_university = True
            self.current_education_level = 'university'
            self.debt += choice.cost
            self.money += choice.cost
            self.happiness = min(100, self.happiness + 10)
            self.stress = min(100, self.stress + 15)
            self.game_message = "🎓 Degree Earned! Income +$1500/mo (Added to debt)"
        elif choice_key == 'masters':
            self.monthly_income += 1000
            self.has_masters = True
            self.current_education_level = 'masters'
            self.debt += choice.cost
            self.money += choice.cost
            self.happiness = min(100, self.happiness + 15)
            self.stress = min(100, self.stress + 20)
            self.game_message = "🎓 Masters Earned! Income +$1000/mo (Added to debt)"
        self.need_button_update = True
    
    def _handle_risky_choice(self, choice_key: str, choice: LifeChoice) -> bool:
        if choice_key == 'gambling' and random.random() < choice.win_chance:
            self.money += choice.win_amount
            self.game_message = f"💰 You won ${choice.win_amount:.0f}!"
            self._add_particle(self.screen.get_width() // 2, self.screen.get_height() // 2, COLOR_WARNING)
            self.need_button_update = True
            return True
        if choice.debuff_chance > 0 and random.random() < choice.debuff_chance:
            if choice.debuff not in self.debuffs:
                self.debuffs.append(choice.debuff)
                self.game_message = f"⚠️ Addicted to {choice.name}!"
                self._add_particle(self.screen.get_width() // 2, self.screen.get_height() // 2, COLOR_DANGER)
                self.need_button_update = True
                return True
        return False
    
    def invest_money(self, amount: float):
        if self.actions_remaining <= 0:
            self.game_message = f"⚠️ No actions left! ({self.actions_taken_this_month}/{ACTIONS_PER_MONTH})"
            return
        if self.money >= amount:
            self.money -= amount
            self.investments += amount
            self.actions_taken_this_month += 1
            self.actions_remaining -= 1
            self.game_message = f"💰 Invested ${amount:.0f} | Actions: {self.actions_remaining}/{ACTIONS_PER_MONTH}"
            self._add_particle(self.screen.get_width() // 2, self.screen.get_height() // 2, COLOR_PRIMARY)
            self.need_button_update = True
    
    def withdraw_investment(self, amount: float):
        if self.actions_remaining <= 0:
            self.game_message = f"⚠️ No actions left! ({self.actions_taken_this_month}/{ACTIONS_PER_MONTH})"
            return
        withdrawal = min(amount, self.investments)
        if withdrawal > 0:
            self.investments -= withdrawal
            self.money += withdrawal
            self.actions_taken_this_month += 1
            self.actions_remaining -= 1
            self.game_message = f"💸 Withdrew ${withdrawal:.0f} | Actions: {self.actions_remaining}/{ACTIONS_PER_MONTH}"
            self.need_button_update = True
        else:
            self.game_message = "No investments!"
    
    def add_to_emergency_fund(self, amount: float):
        if self.actions_remaining <= 0:
            self.game_message = f"⚠️ No actions left! ({self.actions_taken_this_month}/{ACTIONS_PER_MONTH})"
            return
        max_contribution = min(100, amount)
        if self.money >= max_contribution:
            self.money -= max_contribution
            self.emergency_fund += max_contribution
            self.actions_taken_this_month += 1
            self.actions_remaining -= 1
            self.game_message = f"🏦 Saved ${max_contribution:.0f} | Actions: {self.actions_remaining}/{ACTIONS_PER_MONTH}"
            self.need_button_update = True
    
    def pay_off_debt(self, amount: float):
        if self.actions_remaining <= 0:
            self.game_message = f"⚠️ No actions left! ({self.actions_taken_this_month}/{ACTIONS_PER_MONTH})"
            return
        payment = min(amount, self.debt, self.money)
        if payment > 0:
            self.money -= payment
            self.debt -= payment
            self.stress = max(0, self.stress - 5)
            self.actions_taken_this_month += 1
            self.actions_remaining -= 1
            self.game_message = f"💳 Paid ${payment:.0f} debt | Actions: {self.actions_remaining}/{ACTIONS_PER_MONTH}"
            self._add_particle(self.screen.get_width() // 2, self.screen.get_height() // 2, COLOR_SUCCESS)
            self.need_button_update = True
    
    def close_dropdown(self):
        self.active_dropdown = None
        self.dropdown_hover = False
    
    def open_custom_input(self, action_type: str):
        self.show_custom_input = True
        self.custom_input_type = action_type
        self.custom_input_text = ""
        self.close_dropdown()
    
    def execute_financial_action(self, action_type: str, amount: float):
        if action_type == 'invest':
            self.invest_money(amount)
        elif action_type == 'save':
            if self.money >= amount:
                self.money -= amount
                self.emergency_fund += amount
                self.actions_taken_this_month += 1
                self.actions_remaining -= 1
                self.game_message = f"💵 Saved ${amount:.0f} | Actions: {self.actions_remaining}/{ACTIONS_PER_MONTH}"
                self.need_button_update = True
            else:
                self.game_message = "❌ Not enough money"
        elif action_type == 'withdraw':
            self._withdraw_emergency(amount)
        elif action_type == 'pay_debt':
            self.pay_off_debt(amount)
        self.close_dropdown()
    
    def _withdraw_emergency(self, amount: float):
        if self.actions_remaining <= 0:
            self.game_message = f"⚠️ No actions left! ({self.actions_taken_this_month}/{ACTIONS_PER_MONTH})"
            return
        withdrawal = min(amount, self.emergency_fund)
        if withdrawal > 0:
            self.emergency_fund -= withdrawal
            self.money += withdrawal
            self.actions_taken_this_month += 1
            self.actions_remaining -= 1
            self.game_message = f"🏦 Withdrew ${withdrawal:.0f} | Actions: {self.actions_remaining}/{ACTIONS_PER_MONTH}"
            self.need_button_update = True
    
    def handle_custom_input_submit(self):
        try:
            amount = float(self.custom_input_text)
            if amount <= 0 or amount > 100000:
                self.game_message = "❌ Amount must be between $1 and $100,000"
                return
            self.execute_financial_action(self.custom_input_type, amount)
            self.show_custom_input = False
            self.custom_input_text = ""
        except ValueError:
            self.game_message = "❌ Invalid amount"
    
    def treat_addiction(self):
        if self.actions_remaining <= 0:
            self.game_message = f"⚠️ No actions left! ({self.actions_taken_this_month}/{ACTIONS_PER_MONTH})"
            return
        cost = 1500
        if self.money < cost:
            self.game_message = "Need $1500 for treatment"
            return
        success_chance = self.happiness / 100
        self.money -= cost
        self.actions_taken_this_month += 1
        self.actions_remaining -= 1
        if random.random() < success_chance:
            self.debuffs = [d for d in self.debuffs if d != 'addict']
            self.happiness = min(100, self.happiness + 10)
            self.game_message = f"🏥 Addiction cured! | Actions: {self.actions_remaining}/{ACTIONS_PER_MONTH}"
            self._add_particle(self.screen.get_width() // 2, self.screen.get_height() // 2, COLOR_SUCCESS)
        else:
            self.game_message = f"❌ Treatment failed. Need higher happiness. | Actions: {self.actions_remaining}/{ACTIONS_PER_MONTH}"
        self.need_button_update = True
    
    def seek_therapy(self):
        if self.actions_remaining <= 0:
            self.game_message = f"⚠️ No actions left! ({self.actions_taken_this_month}/{ACTIONS_PER_MONTH})"
            return
        cost = 800
        if self.money < cost:
            self.game_message = "Need $800 for therapy"
            return
        self.money -= cost
        self.debuffs = [d for d in self.debuffs if d not in ['unhappy', 'distracted']]
        self.stress = max(0, self.stress - 20)
        self.happiness = min(100, self.happiness + 15)
        self.actions_taken_this_month += 1
        self.actions_remaining -= 1
        self.game_message = f"🧠 Therapy successful! | Actions: {self.actions_remaining}/{ACTIONS_PER_MONTH}"
        self._add_particle(self.screen.get_width() // 2, self.screen.get_height() // 2, COLOR_ACCENT)
        self.need_button_update = True
    
    def check_goals(self):
        net_worth = self.money + self.investments + self.emergency_fund - self.debt
        if net_worth >= self.goals['netWorth']['target']:
            self.goals['netWorth']['completed'] = True
        if self.emergency_fund >= self.goals['emergencyFund']['target']:
            self.goals['emergencyFund']['completed'] = True
        if self.debt <= 0:
            self.goals['debtFree']['completed'] = True
        if self.happiness >= self.goals['happiness']['target']:
            self.goals['happiness']['completed'] = True
    
    def calculate_score(self) -> int:
        net_worth = self.money + self.investments + self.emergency_fund - self.debt
        goal_bonus = sum(1 for g in self.goals.values() if g['completed']) * 5000
        happiness_bonus = self.happiness * 100
        month_bonus = self.current_month * 500
        return max(0, int(net_worth + goal_bonus + happiness_bonus + month_bonus))
    
    def end_game(self, completed: bool, reason: str = ''):
        score = self.calculate_score()
        if score > self.high_score:
            self.high_score = score
            self._save_high_score()
        self.game_message = reason or ('Game completed!' if completed else 'Game over!')
        self.state = GameState.GAME_OVER
    
    # --- Drawing Helper Methods ---
    
    def _draw_text(self, text: str, font, color, x: int, y: int, 
                  center: bool = False, shadow: bool = False, glow: bool = False):
        if shadow:
            shadow_surf = font.render(text, True, (0, 0, 0))
            shadow_rect = shadow_surf.get_rect(center=(x + 3, y + 3) if center else (x + 3, y + 3))
            if not center:
                shadow_rect.topleft = (x + 3, y + 3)
            self.screen.blit(shadow_surf, shadow_rect)
        if glow:
            for offset in range(1, 4):
                glow_surf = font.render(text, True, (*color[:3], 50))
                glow_rect = glow_surf.get_rect(center=(x, y) if center else (x, y))
                if center:
                    glow_rect.center = (x, y)
                else:
                    glow_rect.topleft = (x, y)
                self.screen.blit(glow_surf, glow_rect)
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(center=(x, y) if center else (x, y))
        if not center:
            text_rect.topleft = (x, y)
        self.screen.blit(text_surface, text_rect)
    
    def _draw_progress_bar(self, x: int, y: int, width: int, height: int, 
                          percentage: float, color, bg_color=COLOR_PANEL, glow: bool = False):
        for i in range(height):
            alpha = 100 + i * 2
            bg_color_gradient = (bg_color[0], bg_color[1], bg_color[2])
            pygame.draw.line(self.screen, bg_color_gradient, (x, y + i), (x + width, y + i))
        fill_width = int(width * max(0, min(100, percentage)) / 100)
        if fill_width > 0:
            for i in range(height):
                ratio = i / height
                fill_color = (
                    int(color[0] * (1 - ratio * 0.3)),
                    int(color[1] * (1 - ratio * 0.3)),
                    int(color[2] * (1 - ratio * 0.3))
                )
                pygame.draw.line(self.screen, fill_color, (x, y + i), (x + fill_width, y + i))
        if glow and percentage > 80:
            glow_surf = pygame.Surface((fill_width + 10, height + 10), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (*color[:3], 30), (0, 0, fill_width + 10, height + 10), border_radius=height//2)
            self.screen.blit(glow_surf, (x - 5, y - 5))
        pygame.draw.rect(self.screen, COLOR_BORDER, (x, y, width, height), 1, border_radius=height//2)
    
    def _draw_gradient_background(self):
        time = pygame.time.get_ticks() * 0.0005
        for y in range(SCREEN_HEIGHT):
            ratio = y / SCREEN_HEIGHT
            r = int(15 + math.sin(time + y * 0.01) * 5)
            g = int(23 + math.cos(time + y * 0.01) * 5)
            b = int(42 + math.sin(time * 0.5 + y * 0.01) * 5)
            color = (r, g, b)
            pygame.draw.line(self.screen, color, (0, y), (SCREEN_WIDTH, y))
    
    def _wrap_text(self, text: str, font, max_width: int) -> List[str]:
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            current_line.append(word)
            if font.size(' '.join(current_line))[0] > max_width:
                current_line.pop()
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        return lines
    
    # --- Main Drawing Methods ---
    
    def _draw_title(self, events):
        self._draw_gradient_background()
        time = pygame.time.get_ticks() * 0.001
        for i in range(3):
            radius = 400 + int(math.sin(time + i) * 50)
            alpha = 30 + int(math.sin(time * 0.5 + i) * 20)
            color = (*COLOR_PRIMARY[:3], alpha)
            pygame.draw.circle(self.screen, color[:3], (SCREEN_WIDTH//2, SCREEN_HEIGHT//2), radius, 2)
        self._draw_text("FINANCE", self.font_xl, COLOR_PRIMARY, SCREEN_WIDTH // 2, 200, center=True, shadow=True, glow=True)
        self._draw_text("QUEST", self.font_xl, COLOR_ACCENT, SCREEN_WIDTH // 2, 270, center=True, shadow=True, glow=True)
        self._draw_text("Master Your Financial Future", self.font_medium, COLOR_TEXT_DIM, SCREEN_WIDTH // 2, 360, center=True)
        if self.high_score > 0:
            pygame.draw.rect(self.screen, COLOR_PANEL, (SCREEN_WIDTH//2 - 200, 400, 400, 60), border_radius=15)
            pygame.draw.rect(self.screen, COLOR_WARNING, (SCREEN_WIDTH//2 - 200, 400, 400, 60), 2, border_radius=15)
            self._draw_text(f"🏆 High Score: {self.high_score:,}", self.font_medium, COLOR_WARNING, SCREEN_WIDTH // 2, 430, center=True)
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
        panel_rect = pygame.Rect(200, 150, SCREEN_WIDTH - 400, 500)
        pygame.draw.rect(self.screen, COLOR_PANEL, panel_rect, border_radius=20)
        pygame.draw.rect(self.screen, COLOR_PRIMARY, panel_rect, 3, border_radius=20)
        pygame.draw.rect(self.screen, COLOR_PANEL_HOVER, (200, 150, SCREEN_WIDTH-400, 80), border_top_left_radius=20, border_top_right_radius=20)
        self._draw_text(f"📘 Tutorial {self.tutorial_step + 1}/{len(tutorials)}", self.font_medium, COLOR_ACCENT, SCREEN_WIDTH // 2, 190, center=True)
        self._draw_text(title, self.font_large, COLOR_PRIMARY, SCREEN_WIDTH // 2, 280, center=True, glow=True)
        lines = self._wrap_text(content, self.font_medium, panel_rect.width - 100)
        y = 360
        for line in lines:
            self._draw_text(line, self.font_medium, COLOR_TEXT, SCREEN_WIDTH // 2, y, center=True)
            y += 45
        next_text = "Next" if self.tutorial_step < 3 else "Start Setup"
        self.cached_buttons[GameState.TUTORIAL][1].update_text(next_text)
        self.cached_buttons[GameState.TUTORIAL][0].enabled = self.tutorial_step > 0
        for btn in self.cached_buttons[GameState.TUTORIAL]:
            btn.draw(self.screen, self.font_small)
        for event in events:
            for btn in self.cached_buttons[GameState.TUTORIAL]:
                btn.handle_event(event)

    def _draw_setup(self, events):
        self._draw_gradient_background()
        self._draw_text("⚡ CHARACTER SETUP", self.font_large, COLOR_PRIMARY, SCREEN_WIDTH // 2, 50, center=True, glow=True)
        cols = 3
        section_width = 380
        gap = 40
        start_x = (SCREEN_WIDTH - (cols * section_width + (cols-1)*gap)) // 2
        self._draw_class_selection(start_x, section_width, events)
        self._draw_education_selection(start_x + section_width + gap, section_width, events)
        self._draw_difficulty_selection(start_x + (section_width + gap) * 2, section_width, events)
        self.cached_buttons[GameState.SETUP][0].enabled = all([
            self.selected_class, self.selected_education, self.selected_difficulty
        ])
        for btn in self.cached_buttons[GameState.SETUP]:
            font = self.font_small if btn.button_id == "setup_back" else self.font_medium
            btn.draw(self.screen, font)
        for event in events:
            for btn in self.cached_buttons[GameState.SETUP]:
                btn.handle_event(event)

    def _draw_class_selection(self, x: int, width: int, events):
        y = 120
        self._draw_text("SOCIAL CLASS", self.font_medium, COLOR_ACCENT, x + width//2, y, center=True)
        y += 50
        for key, config in self.class_configs.items():
            color = COLOR_PRIMARY if self.selected_class == key else COLOR_PANEL
            text_color = COLOR_BG if self.selected_class == key else COLOR_TEXT
            btn = Button(x, y, width, 120, f"{config.avatar_emoji} {config.name}\n💰 ${config.starting_money:,.0f}\n💳 ${config.debt:,.0f}", color, text_color, button_id=f"class_{key}", tooltip=config.description)
            btn.draw(self.screen, self.font_small)
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if btn.rect.collidepoint(event.pos):
                        self.selected_class = key
                        self._add_particle(event.pos[0], event.pos[1], COLOR_PRIMARY)
            y += 130

    def _draw_education_selection(self, x: int, width: int, events):
        y = 120
        self._draw_text("EDUCATION", self.font_medium, COLOR_ACCENT, x + width//2, y, center=True)
        y += 50
        for key, config in self.education_configs.items():
            color = COLOR_PRIMARY if self.selected_education == key else COLOR_PANEL
            text_color = COLOR_BG if self.selected_education == key else COLOR_TEXT
            cost_text = "🎓 Free" if config.cost == 0 else f"📚 ${config.cost:,}"
            btn = Button(x, y, width, 120, f"{config.name}\n💵 ${config.income:,.0f}/mo\n{cost_text}", color, text_color, button_id=f"edu_{key}", tooltip=config.description)
            btn.draw(self.screen, self.font_small)
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if btn.rect.collidepoint(event.pos):
                        self.selected_education = key
                        self._add_particle(event.pos[0], event.pos[1], COLOR_PRIMARY)
            y += 130

    def _draw_difficulty_selection(self, x: int, width: int, events):
        y = 120
        self._draw_text("DIFFICULTY", self.font_medium, COLOR_ACCENT, x + width//2, y, center=True)
        y += 50
        for key, config in self.difficulty_configs.items():
            color = COLOR_PRIMARY if self.selected_difficulty == key else COLOR_PANEL
            text_color = COLOR_BG if self.selected_difficulty == key else COLOR_TEXT
            btn = Button(x, y, width, 120, f"{config.name}\n{config.description}", color, text_color, button_id=f"diff_{key}")
            btn.draw(self.screen, self.font_small)
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if btn.rect.collidepoint(event.pos):
                        self.selected_difficulty = key
                        self._add_particle(event.pos[0], event.pos[1], COLOR_PRIMARY)
            y += 130

    def _draw_playing(self, events):
        """Draw main playing screen with AI chatbot"""
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
        
        # Draw AI Chatbot icon in bottom left corner
        draw_chatbot_icon(
            self.screen, 
            80, SCREEN_HEIGHT - 80, 
            self.chatbot.is_thinking, 
            self.chatbot_has_new_message
        )
        
        # Draw chatbot modal if open
        if self.show_chatbot:
            modal_x, modal_y, modal_w, modal_h, history_rect = draw_chatbot_modal(
                self.screen, self.font_medium, self.chatbot
            )
            
            # Draw input box
            input_rect = pygame.Rect(modal_x + 20, modal_y + modal_h - 80, modal_w - 100, 50)
            pygame.draw.rect(self.screen, COLOR_PANEL, input_rect, border_radius=10)
            pygame.draw.rect(self.screen, COLOR_PRIMARY, input_rect, 2, border_radius=10)
            
            # Draw send button
            send_btn = Button(modal_x + modal_w - 70, modal_y + modal_h - 80, 50, 50, "→", 
                            COLOR_SUCCESS, COLOR_BG, "send_chat", gradient=True)
            
            # Draw close button
            close_btn = Button(modal_x + modal_w - 50, modal_y + 20, 30, 30, "✕", COLOR_DANGER, COLOR_TEXT, "close_chat")
            
            # Draw input text
            if self.chatbot_input_active:
                cursor = "|" if pygame.time.get_ticks() % 1000 < 500 else " "
                display_text = self.chatbot_input_text + cursor
            else:
                display_text = self.chatbot_input_text if self.chatbot_input_text else "Ask for help..."
            
            text_surf = self.font_tiny.render(display_text, True, COLOR_TEXT)
            self.screen.blit(text_surf, (input_rect.x + 10, input_rect.y + 15))
            
            # Draw buttons
            close_btn.draw(self.screen, self.font_small)
            send_btn.draw(self.screen, self.font_small)
            
            # Handle chatbot events
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
                    else:
                        if len(self.chatbot_input_text) < 50:
                            self.chatbot_input_text += event.unicode
        
        # Handle chatbot icon click
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Check if chatbot icon clicked
                icon_rect = pygame.Rect(50, SCREEN_HEIGHT - 110, 60, 60)
                if icon_rect.collidepoint(event.pos):
                    self._toggle_chatbot()
        
        # Handle other events
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                mouse_pos = event.pos
                for btn in self.cached_buttons[GameState.PLAYING]:
                    if btn.visible and btn.rect.collidepoint(mouse_pos) and hasattr(btn, 'lock_data'):
                        if self.locked_action and self.locked_action['callback'] == btn.lock_data['callback']:
                            self.locked_action = None
                            self.game_message = "🔓 Action unlocked"
                        else:
                            self.locked_action = btn.lock_data
                            self.game_message = f"🔒 Locked: {btn.lock_data['name']}"
                        self.need_button_update = True
                        break
            
            for btn in self.cached_buttons[GameState.PLAYING]:
                if btn.button_id in ["next_month", "help", "chatbot"]:
                    btn.handle_event(event)
            
            for btn in self.cached_buttons[GameState.PLAYING]:
                if btn.button_id not in ["next_month", "help", "chatbot"]:
                    btn.handle_event(event)
        
        mouse_pos = pygame.mouse.get_pos()
        for btn in self.cached_buttons[GameState.PLAYING]:
            if btn.visible:
                btn.hover = btn.rect.collidepoint(mouse_pos)

    def _draw_playing_header(self):
        """Draw playing screen header - with CASH and NET WORTH as text labels"""
        header_height = 80
        pygame.draw.rect(self.screen, COLOR_PANEL, (0, 0, SCREEN_WIDTH, header_height))
        pygame.draw.line(self.screen, COLOR_BORDER, (0, header_height), (SCREEN_WIDTH, header_height), 1)
        
        net_worth = self.money + self.investments + self.emergency_fund - self.debt
        
        # Avatar display
        pygame.draw.circle(self.screen, COLOR_PRIMARY, (90, 40), 25)
        pygame.draw.circle(self.screen, COLOR_ACCENT, (90, 40), 27, 2)
        self._draw_text(self.selected_avatar, self.font_large, COLOR_TEXT, 90, 40, center=True)
        self._draw_text("FINANCE QUEST", self.font_large, COLOR_PRIMARY, 150, 15)
        
        # MONTH
        self._draw_text("MONTH", self.font_tiny, COLOR_TEXT_DIM, 550, 15)
        month_color = COLOR_SUCCESS if self.current_month < MONTHS_PER_GAME * 0.5 else \
                    COLOR_WARNING if self.current_month < MONTHS_PER_GAME * 0.8 else \
                    COLOR_DANGER
        self._draw_text(f"{self.current_month}/{MONTHS_PER_GAME}", self.font_medium, month_color, 550, 35)
        
        # CASH
        self._draw_text("CASH", self.font_tiny, COLOR_TEXT_DIM, 750, 15)
        cash_color = COLOR_SUCCESS if self.money > 0 else COLOR_DANGER
        self._draw_text(f"${self.money:,.0f}", self.font_medium, cash_color, 750, 35)
        
        # NET WORTH
        self._draw_text("NET WORTH", self.font_tiny, COLOR_TEXT_DIM, 950, 15)
        worth_color = COLOR_PRIMARY if net_worth > 0 else COLOR_WARNING
        self._draw_text(f"${net_worth:,.0f}", self.font_medium, worth_color, 950, 35)
        
        # ============================================================
        # HELP BUTTON - TOP RIGHT CORNER (ORIGINAL DESIGN)
        # ============================================================
        # Draw Help button at top right with ❓ icon
        for btn in self.cached_buttons[GameState.PLAYING]:
            if btn.button_id == "help":
                btn.rect.x = SCREEN_WIDTH - 120
                btn.rect.y = 20
                btn.rect.width = 100
                btn.rect.height = 40
                btn.text = "HELP"
                btn.icon = "❓"
                btn.base_color = COLOR_ACCENT
                btn.gradient = False
                btn.draw(self.screen, self.font_small)
                break
        
        # Draw Chatbot button at top right, next to Help button
        for btn in self.cached_buttons[GameState.PLAYING]:
            if btn.button_id == "chatbot":
                btn.rect.x = SCREEN_WIDTH - 230
                btn.rect.y = 20
                btn.rect.width = 100
                btn.rect.height = 40
                btn.text = "ASK AI"
                btn.icon = "🦊"
                btn.base_color = COLOR_PRIMARY
                btn.gradient = True
                btn.draw(self.screen, self.font_small)
                break

    def _draw_playing_sidebar(self, sidebar_w: int, header_height: int):
        sidebar_rect = pygame.Rect(0, header_height, sidebar_w, SCREEN_HEIGHT - header_height - 100)
        pygame.draw.rect(self.screen, (15, 25, 40), sidebar_rect)
        pygame.draw.line(self.screen, COLOR_PRIMARY, (sidebar_w, header_height), (sidebar_w, SCREEN_HEIGHT - 100), 2)
        
        sy = header_height + 30
        padding = 30
        
        self._draw_text("🧠 WELL-BEING", self.font_small, COLOR_ACCENT, padding, sy)
        sy += 40
        self._draw_text(f"😊 Happiness: {self.happiness:.0f}%", self.font_small, COLOR_TEXT, padding, sy)
        self._draw_progress_bar(padding, sy+25, sidebar_w - 60, 12, self.happiness, COLOR_SUCCESS, glow=self.happiness > 70)
        sy += 55
        self._draw_text(f"😰 Stress: {self.stress:.0f}%", self.font_small, COLOR_TEXT, padding, sy)
        self._draw_progress_bar(padding, sy+25, sidebar_w - 60, 12, self.stress, COLOR_DANGER, glow=self.stress > 70)
        sy += 65
        pygame.draw.line(self.screen, COLOR_PANEL_HOVER, (padding, sy), (sidebar_w - padding, sy))
        sy += 25
        
        self._draw_text("💰 FINANCES", self.font_small, COLOR_ACCENT, padding, sy)
        sy += 35
        fin_items = [
            ("📈 Income", f"+${self.monthly_income:,.0f}", COLOR_SUCCESS),
            ("📉 Expenses", f"-${(self.rent+self.groceries+self.transport):,.0f}", COLOR_DANGER),
            ("💳 Debt", f"${self.debt:,.0f}", COLOR_DANGER),
            ("📊 Investments", f"${self.investments:,.0f}", COLOR_PRIMARY),
            ("🏦 Emergency", f"${self.emergency_fund:,.0f}", COLOR_WARNING),
        ]
        for label, val, col in fin_items:
            self._draw_text(label, self.font_small, COLOR_TEXT_DIM, padding, sy)
            self._draw_text(val, self.font_small, col, sidebar_w - padding - 50, sy)
            sy += 35
        sy += 10
        pygame.draw.line(self.screen, COLOR_PANEL_HOVER, (padding, sy), (sidebar_w - padding, sy))
        sy += 25
        
        self._draw_text("📋 STATUS", self.font_small, COLOR_ACCENT, padding, sy)
        sy += 35
        edu_name = self.education_configs[self.current_education_level].name
        self._draw_text("🎓 Education:", self.font_small, COLOR_TEXT_DIM, padding, sy)
        self._draw_text(edu_name, self.font_small, COLOR_ACCENT, padding + 120, sy)
        
        if self.debuffs:
            sy += 45
            self._draw_text("⚠️ Active Effects:", self.font_small, COLOR_DANGER, padding, sy)
            sy += 30
            for d in self.debuffs:
                pygame.draw.rect(self.screen, COLOR_DANGER, (padding, sy, 140, 28), border_radius=6)
                self._draw_text(d.upper(), self.font_tiny, COLOR_BG, padding + 10, sy + 6)
                sy += 35

    def _draw_playing_main(self, sidebar_w: int, main_area_w: int, header_height: int):
        """Draw main center area with goals, event log, and BOTTOM CONTROLS"""
        mx = sidebar_w + 30
        my = header_height + 30
        
        # Goals
        self._draw_text("ACTIVE GOALS", self.font_medium, COLOR_PRIMARY, mx, my, glow=True)
        my += 45
        
        goal_w = (main_area_w - 80) // 2
        goal_h = 80
        
        goal_items = list(self.goals.values())
        for i, goal in enumerate(goal_items):
            gx = mx if i % 2 == 0 else mx + goal_w + 30
            gy = my + (i // 2) * (goal_h + 20)
            
            g_color = COLOR_SUCCESS if goal['completed'] else COLOR_PANEL
            border = COLOR_SUCCESS if goal['completed'] else COLOR_BORDER
            
            pygame.draw.rect(self.screen, g_color, (gx, gy, goal_w, goal_h), border_radius=12)
            pygame.draw.rect(self.screen, border, (gx, gy, goal_w, goal_h), 3, border_radius=12)
            
            status_icon = "✓" if goal['completed'] else "○"
            text_color = COLOR_BG if goal['completed'] else COLOR_TEXT
            self._draw_text(f"{status_icon} {goal['label']}", self.font_small, 
                          text_color, gx + 15, gy + 30)
        
        # Event Log
        msg_y = my + 220
        msg_bg_rect = pygame.Rect(mx, msg_y, main_area_w - 60, 100)
        pygame.draw.rect(self.screen, COLOR_PANEL, msg_bg_rect, border_radius=15)
        pygame.draw.rect(self.screen, COLOR_PRIMARY, msg_bg_rect, 2, border_radius=15)
        
        self._draw_text("EVENT LOG", self.font_tiny, COLOR_PRIMARY, mx + 20, msg_y + 15)
        
        lines = self.game_message.split('|')
        ly = msg_y + 45
        for line in lines[:2]:
            self._draw_text(line.strip(), self.font_small, COLOR_TEXT, mx + 20, ly)
            ly += 35
        
        # ============================================================
        # ACTIONS LEFT COUNTER & NEXT MONTH BUTTON - DIRECTLY BELOW EVENT LOG
        # ============================================================
        controls_y = msg_y + 120
        
        # ACTIONS LEFT COUNTER
        actions_x = mx
        actions_y = controls_y
        actions_width = 160
        actions_height = 90
        
        pygame.draw.rect(self.screen, COLOR_PANEL, 
                        (actions_x, actions_y, actions_width, actions_height), 
                        border_radius=15)
        pygame.draw.rect(self.screen, COLOR_BORDER, 
                        (actions_x, actions_y, actions_width, actions_height), 
                        2, border_radius=15)
        
        self._draw_text("ACTIONS LEFT", self.font_tiny, COLOR_TEXT_DIM, 
                       actions_x + actions_width//2, actions_y + 15, center=True)
        
        if self.actions_remaining == 3:
            actions_color = COLOR_SUCCESS
            status_text = "FULL"
        elif self.actions_remaining == 2:
            actions_color = COLOR_SUCCESS
            status_text = "GOOD"
        elif self.actions_remaining == 1:
            actions_color = COLOR_WARNING
            status_text = "LOW"
        else:
            actions_color = COLOR_DANGER
            status_text = "NONE"
        
        self._draw_text(f"{self.actions_remaining}", 
                       self.font_xl, actions_color, 
                       actions_x + actions_width//2, actions_y + 50, 
                       center=True, glow=True)
        self._draw_text(status_text, self.font_tiny, actions_color,
                       actions_x + actions_width//2, actions_y + 70, center=True)
        
        # NEXT MONTH BUTTON
        next_btn_width = 200
        next_btn_height = 90
        next_btn_x = mx + main_area_w - 60 - next_btn_width
        next_btn_y = controls_y
        
        for btn in self.cached_buttons[GameState.PLAYING]:
            if btn.button_id == "next_month":
                btn.rect.x = next_btn_x
                btn.rect.y = next_btn_y
                btn.rect.width = next_btn_width
                btn.rect.height = next_btn_height
                btn.original_y = next_btn_y
                btn.update_text("NEXT MONTH")
                btn.draw(self.screen, self.font_medium)
                break

    def _draw_playing_actions(self, action_panel_w: int, header_height: int):
        """Draw right action panel"""
        action_rect = pygame.Rect(SCREEN_WIDTH - action_panel_w, header_height, 
                                action_panel_w, SCREEN_HEIGHT - header_height - 100)
        pygame.draw.rect(self.screen, (20, 30, 50), action_rect)
        pygame.draw.line(self.screen, COLOR_PRIMARY, (action_rect.x, header_height), 
                        (action_rect.x, SCREEN_HEIGHT - 100), 2)
        
        self._draw_text("⚡ AVAILABLE ACTIONS", self.font_small, COLOR_PRIMARY, 
                       action_rect.x + 20, header_height + 20)
        
        # Handle dropdown logic
        if self.active_dropdown:
            mouse_pos = pygame.mouse.get_pos()
            mouse_over_button = False
            mouse_over_dropdown = False
            
            for btn in self.cached_buttons[GameState.PLAYING]:
                if hasattr(btn, 'action_type') and btn.action_type == self.active_dropdown:
                    if btn.rect.collidepoint(mouse_pos):
                        mouse_over_button = True
                        self.dropdown_last_hover_time = pygame.time.get_ticks()
                    
                    dropdown_x = btn.rect.x
                    
                    if btn.action_type in ['save', 'invest']:
                        option_w = 100
                        dropdown_w = option_w * 4 + 20
                        dropdown_h = 60
                        dropdown_y = btn.rect.y - dropdown_h - 5
                        
                        if dropdown_x + dropdown_w > SCREEN_WIDTH:
                            dropdown_x = SCREEN_WIDTH - dropdown_w - 10
                        if dropdown_y < 0:
                            dropdown_y = btn.rect.y + btn.rect.height + 5
                        
                        dropdown_rect = pygame.Rect(dropdown_x, dropdown_y, dropdown_w, dropdown_h)
                    else:
                        dropdown_w = 180
                        dropdown_h = 200
                        dropdown_y = btn.rect.y + btn.rect.height + 5
                        
                        if dropdown_x + dropdown_w > SCREEN_WIDTH:
                            dropdown_x = SCREEN_WIDTH - dropdown_w - 10
                        if dropdown_y + dropdown_h > SCREEN_HEIGHT - 100:
                            dropdown_y = btn.rect.y - dropdown_h - 5
                        
                        dropdown_rect = pygame.Rect(dropdown_x, dropdown_y, dropdown_w, dropdown_h)
                    
                    if dropdown_rect.collidepoint(mouse_pos):
                        mouse_over_dropdown = True
                        self.dropdown_last_hover_time = pygame.time.get_ticks()
                    break
            
            self.dropdown_hover = mouse_over_dropdown
            
            current_time = pygame.time.get_ticks()
            time_since_hover = current_time - self.dropdown_last_hover_time
            if not mouse_over_button and not mouse_over_dropdown and time_since_hover > self.dropdown_stay_duration:
                self.close_dropdown()
        
        # Check for dropdown activation on hover
        for btn in self.cached_buttons[GameState.PLAYING]:
            if hasattr(btn, 'action_type') and btn.visible and btn.enabled:
                mouse_pos = pygame.mouse.get_pos()
                if btn.rect.collidepoint(mouse_pos):
                    if self.active_dropdown != btn.action_type:
                        self.active_dropdown = btn.action_type
                        self.dropdown_last_hover_time = pygame.time.get_ticks()
        
        # Draw action buttons
        for btn in self.cached_buttons[GameState.PLAYING]:
            if btn.button_id not in ["next_month", "help", "chatbot"]:
                btn.draw(self.screen, self.font_tiny)
        
        # Draw dropdown
        if self.active_dropdown:
            dropdown_button = None
            for btn in self.cached_buttons[GameState.PLAYING]:
                if hasattr(btn, 'action_type') and btn.action_type == self.active_dropdown:
                    dropdown_button = btn
                    break
            
            if dropdown_button:
                self.draw_financial_dropdown(self.screen, dropdown_button)
        
        # Draw tooltips
        for btn in self.cached_buttons[GameState.PLAYING]:
            if btn.button_id not in ["next_month", "help", "chatbot"]:
                btn.draw_tooltip(self.screen, self.font_tiny)

    def _draw_help_panel(self, events):
        """Draw scrollable help panel overlay"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(220)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        panel_w, panel_h = 900, 650
        panel_x = (SCREEN_WIDTH - panel_w) // 2
        panel_y = (SCREEN_HEIGHT - panel_h) // 2
        
        # Handle mouse wheel scrolling
        for event in events:
            if event.type == pygame.MOUSEWHEEL:
                if self.show_help_panel:
                    self.help_scroll_offset -= event.y * 30
                    self.help_scroll_offset = max(0, min(self.help_scroll_offset, self.help_max_scroll))
        
        # Create a surface for the help content (for scrolling)
        content_height = 800
        content_surface = pygame.Surface((panel_w - 40, content_height), pygame.SRCALPHA)
        content_surface.fill((0, 0, 0, 0))
        
        # Draw panel background
        pygame.draw.rect(self.screen, COLOR_BG, (panel_x, panel_y, panel_w, panel_h), border_radius=20)
        pygame.draw.rect(self.screen, COLOR_PRIMARY, (panel_x, panel_y, panel_w, panel_h), 4, border_radius=20)
        
        # Title (fixed, not scrolling)
        self._draw_text("📚 GAME GUIDE", self.font_large, COLOR_PRIMARY, 
                       panel_x + panel_w // 2, panel_y + 40, center=True, glow=True)
        
        # Help content sections (scrollable)
        help_sections = [
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
        
        # Calculate max scroll
        section_height = 0
        for title, content in help_sections:
            lines = content.split('\n')
            section_height += 35 + len(lines) * 25 + 15
        self.help_max_scroll = max(0, section_height - (panel_h - 150))
        
        # Draw content on surface with scroll offset
        y = 20 - self.help_scroll_offset
        x = 30
        
        for title, content in help_sections:
            if y + 30 > 0 and y < content_height:
                # Draw title
                title_surf = self.font_small.render(title, True, COLOR_ACCENT)
                content_surface.blit(title_surf, (x, y))
                y += 35
                
                # Draw content lines
                lines = content.split('\n')
                for line in lines:
                    if y + 20 > 0 and y < content_height:
                        line_surf = self.font_tiny.render(line, True, COLOR_TEXT)
                        content_surface.blit(line_surf, (x + 25, y))
                    y += 25
                y += 15
            else:
                # Skip drawing but still calculate y position
                lines = content.split('\n')
                y += 35 + len(lines) * 25 + 15
        
        # Blit content surface onto screen with clipping
        self.screen.blit(content_surface, (panel_x + 20, panel_y + 100), 
                        area=(0, self.help_scroll_offset, panel_w - 40, panel_h - 150))
        
        # Draw scroll bar if needed
        if self.help_max_scroll > 0:
            scroll_bar_height = (panel_h - 150) * (panel_h - 150) / content_height
            scroll_bar_y = panel_y + 100 + (self.help_scroll_offset / self.help_max_scroll) * ((panel_h - 150) - scroll_bar_height)
            pygame.draw.rect(self.screen, COLOR_PANEL_HOVER, 
                           (panel_x + panel_w - 20, panel_y + 100, 8, panel_h - 150), 
                           border_radius=4)
            pygame.draw.rect(self.screen, COLOR_PRIMARY, 
                           (panel_x + panel_w - 20, scroll_bar_y, 8, scroll_bar_height), 
                           border_radius=4)
        
        # Close button (fixed, not scrolling)
        close_btn = Button(panel_x + panel_w // 2 - 100, panel_y + panel_h - 70, 
                          200, 50, "Close", COLOR_PRIMARY, text_color=COLOR_BG,
                          gradient=True, icon="✓")
        close_btn.callback = self._toggle_help
        
        mouse_pos = pygame.mouse.get_pos()
        close_btn.hover = close_btn.rect.collidepoint(mouse_pos)
        close_btn.draw(self.screen, self.font_medium)
        
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if close_btn.hover:
                    self._toggle_help()
                    break
    
    def _draw_event_modal(self, events):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        w, h = 600, 450
        x, y = (SCREEN_WIDTH - w)//2, (SCREEN_HEIGHT - h)//2
        
        pygame.draw.rect(self.screen, COLOR_PANEL, (x, y, w, h), border_radius=20)
        pygame.draw.rect(self.screen, COLOR_ACCENT, (x, y, w, h), 4, border_radius=20)
        
        self._draw_text(self.current_event.name, self.font_large, COLOR_ACCENT, 
                       x + w//2, y + 50, center=True, glow=True)
        
        lines = self._wrap_text(self.current_event.description, self.font_medium, w - 80)
        ty = y + 130
        for line in lines:
            self._draw_text(line, self.font_medium, COLOR_TEXT, x + w//2, ty, center=True)
            ty += 40
        
        impact_y = ty + 30
        if self.current_event.cost > 0:
            self._draw_text(f"💰 Cost: -${self.current_event.cost:,.0f}", self.font_medium, 
                          COLOR_DANGER, x + w//2, impact_y, center=True)
            impact_y += 35
        if self.current_event.stress_increase > 0:
            self._draw_text(f"😰 Stress: +{self.current_event.stress_increase}%", self.font_medium, 
                          COLOR_DANGER, x + w//2, impact_y, center=True)
        
        cont_btn = Button(x + w//2 - 100, y + h - 80, 200, 50, "Continue", 
                         COLOR_PRIMARY, text_color=COLOR_BG, gradient=True, icon="▶")
        cont_btn.callback = self.handle_event_close
        cont_btn.draw(self.screen, self.font_medium)
        
        mouse_pos = pygame.mouse.get_pos()
        cont_btn.hover = cont_btn.rect.collidepoint(mouse_pos)
        
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if cont_btn.hover:
                    self.handle_event_close()
    
    def draw_financial_dropdown(self, screen, button):
        if not hasattr(button, 'action_type'):
            return
        
        action_type = button.action_type
        
        # HORIZONTAL LAYOUT FOR ALL FINANCIAL ACTIONS
        option_w = 100
        option_h = 45
        dropdown_w = option_w * 4 + 20
        dropdown_h = option_h + 15
        
        dropdown_x = button.rect.x
        
        # POSITIONING: Invest & Save ABOVE, Withdraw & Pay Debt BELOW
        if action_type in ['invest', 'save']:
            dropdown_y = button.rect.y - dropdown_h - 5  # ABOVE
        else:  # withdraw, pay_debt
            dropdown_y = button.rect.y + button.rect.height + 5  # BELOW
        
        if dropdown_x + dropdown_w > SCREEN_WIDTH:
            dropdown_x = SCREEN_WIDTH - dropdown_w - 10
        
        # Keep dropdown on screen
        if dropdown_y < 0:
            dropdown_y = button.rect.y + button.rect.height + 5
        if dropdown_y + dropdown_h > SCREEN_HEIGHT - 100:
            dropdown_y = button.rect.y - dropdown_h - 5
        
        dropdown_rect = pygame.Rect(dropdown_x, dropdown_y, dropdown_w, dropdown_h)
        
        mouse_pos = pygame.mouse.get_pos()
        self.dropdown_hover = dropdown_rect.collidepoint(mouse_pos)
        
        if self.dropdown_hover or button.rect.collidepoint(mouse_pos):
            self.dropdown_last_hover_time = pygame.time.get_ticks()
        
        for i in range(dropdown_rect.height):
            ratio = i / dropdown_rect.height
            color = (
                int(COLOR_PANEL[0] * (1 - ratio * 0.3)),
                int(COLOR_PANEL[1] * (1 - ratio * 0.3)),
                int(COLOR_PANEL[2] * (1 - ratio * 0.3))
            )
            pygame.draw.line(screen, color, 
                        (dropdown_rect.x, dropdown_rect.y + i),
                        (dropdown_rect.x + dropdown_rect.width, dropdown_rect.y + i))
        
        pygame.draw.rect(screen, COLOR_PRIMARY, dropdown_rect, 2, border_radius=8)
        
        # Set amounts based on action type
        if action_type == 'save':
            amounts = [(100, "$100"), (500, "$500"), (1000, "$1k"), (None, "Custom")]
        elif action_type == 'invest':
            amounts = [(1000, "$1k"), (5000, "$5k"), (10000, "$10k"), (None, "Custom")]
        elif action_type == 'withdraw':
            amounts = [(500, "$500"), (1000, "$1k"), (5000, "$5k"), (None, "Custom")]
        elif action_type == 'pay_debt':
            amounts = [(1000, "$1k"), (5000, "$5k"), (10000, "$10k"), (None, "Custom")]
        else:
            amounts = [(1000, "$1k"), (3000, "$3k"), (5000, "$5k"), (None, "Custom")]
        
        # Draw options HORIZONTALLY
        for idx, (amount, label) in enumerate(amounts):
            opt_rect = pygame.Rect(dropdown_x + 5 + idx * option_w, 
                                dropdown_y + 5, 
                                option_w - 5, 
                                option_h - 5)
            opt_hover = opt_rect.collidepoint(mouse_pos)
            affordable = True
            if amount is not None:
                if action_type == 'save' and self.money < amount:
                    affordable = False
                elif action_type == 'invest' and self.money < amount:
                    affordable = False
                elif action_type == 'withdraw' and self.emergency_fund < amount:
                    affordable = False
                elif action_type == 'pay_debt' and (self.money < amount or self.debt < amount):
                    affordable = False
            
            if not affordable:
                bg_color = (40, 45, 55)
                text_color = (80, 85, 95)
            elif opt_hover:
                bg_color = COLOR_PRIMARY
                text_color = COLOR_BG
            else:
                bg_color = COLOR_PANEL_HOVER
                text_color = COLOR_TEXT
            
            pygame.draw.rect(screen, bg_color, opt_rect, border_radius=5)
            text_surf = self.font_tiny.render(label, True, text_color)
            text_rect = text_surf.get_rect(center=opt_rect.center)
            screen.blit(text_surf, text_rect)
            
            if opt_hover and affordable and pygame.mouse.get_pressed()[0]:
                if amount is None:
                    self.open_custom_input(action_type)
                else:
                    self.execute_financial_action(action_type, amount)
                return True
        
        return False
    
    def _draw_custom_input_modal(self, events):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        w, h = 500, 350
        x, y = (SCREEN_WIDTH - w)//2, (SCREEN_HEIGHT - h)//2
        
        pygame.draw.rect(self.screen, COLOR_BG, (x, y, w, h), border_radius=20)
        pygame.draw.rect(self.screen, COLOR_PRIMARY, (x, y, w, h), 4, border_radius=20)
        
        action_names = {
            'invest': '💰 Invest Custom Amount',
            'save': '💵 Save Custom Amount',
            'withdraw': '🏦 Withdraw Custom Amount',
            'pay_debt': '💳 Pay Debt Custom Amount'
        }
        title = action_names.get(self.custom_input_type, 'Enter Amount')
        self._draw_text(title, self.font_large, COLOR_PRIMARY, x + w//2, y + 40, center=True, glow=True)
        self._draw_text("Enter amount (Max: $100,000)", self.font_small, COLOR_TEXT_DIM, 
                       x + w//2, y + 100, center=True)
        
        input_rect = pygame.Rect(x + 50, y + 150, w - 100, 60)
        pygame.draw.rect(self.screen, COLOR_PANEL, input_rect, border_radius=10)
        pygame.draw.rect(self.screen, COLOR_PRIMARY, input_rect, 3, border_radius=10)
        
        display_text = "$" + self.custom_input_text if self.custom_input_text else "$0"
        text_surf = self.font_medium.render(display_text, True, COLOR_TEXT)
        text_rect = text_surf.get_rect(center=input_rect.center)
        self.screen.blit(text_surf, text_rect)
        
        confirm_btn = Button(x + 50, y + h - 70, 180, 50, "Confirm", 
                           COLOR_SUCCESS, text_color=COLOR_BG, gradient=True, icon="✓")
        cancel_btn = Button(x + w - 230, y + h - 70, 180, 50, "Cancel", 
                           COLOR_PANEL, icon="✗")
        
        confirm_btn.draw(self.screen, self.font_medium)
        cancel_btn.draw(self.screen, self.font_medium)
        
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.handle_custom_input_submit()
                elif event.key == pygame.K_ESCAPE:
                    self.show_custom_input = False
                    self.custom_input_text = ""
                elif event.key == pygame.K_BACKSPACE:
                    self.custom_input_text = self.custom_input_text[:-1]
                elif event.unicode.isdigit() or event.unicode == '.':
                    if len(self.custom_input_text) < 10:
                        self.custom_input_text += event.unicode
            
            mouse_pos = pygame.mouse.get_pos()
            confirm_btn.hover = confirm_btn.rect.collidepoint(mouse_pos)
            cancel_btn.hover = cancel_btn.rect.collidepoint(mouse_pos)
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if confirm_btn.hover:
                    self.handle_custom_input_submit()
                elif cancel_btn.hover:
                    self.show_custom_input = False
                    self.custom_input_text = ""

    def _draw_game_over(self, events):
        self._draw_gradient_background()
        
        pygame.draw.rect(self.screen, COLOR_PANEL, 
                        (SCREEN_WIDTH//2 - 450, 80, 900, 750), border_radius=30)
        pygame.draw.rect(self.screen, COLOR_PRIMARY, 
                        (SCREEN_WIDTH//2 - 450, 80, 900, 750), 4, border_radius=30)
        
        score = self.calculate_score()
        is_high_score = score > self.high_score
        title = "🏆 NEW HIGH SCORE! 🏆" if is_high_score else "GAME OVER"
        col = COLOR_WARNING if is_high_score else COLOR_TEXT
        
        self._draw_text(title, self.font_xl, col, SCREEN_WIDTH//2, 150, center=True, shadow=True, glow=True)
        self._draw_text(f"Final Score: {score:,}", self.font_large, COLOR_PRIMARY, 
                       SCREEN_WIDTH//2, 240, center=True)
        
        if is_high_score:
            self._draw_text("Congratulations! You've set a new record!", self.font_medium, 
                          COLOR_SUCCESS, SCREEN_WIDTH//2, 310, center=True)
        
        stats = [
            ("💰 Net Worth", f"${(self.money + self.investments + self.emergency_fund - self.debt):,.0f}"),
            ("😊 Happiness", f"{self.happiness:.0f}%"),
            ("🎯 Goals Met", f"{sum(1 for g in self.goals.values() if g['completed'])}/4"),
            ("📅 Months", f"{self.current_month}")
        ]
        
        sy = 380
        for label, val in stats:
            self._draw_text(label, self.font_medium, COLOR_TEXT_DIM, 
                          SCREEN_WIDTH//2 - 150, sy)
            self._draw_text(val, self.font_medium, COLOR_TEXT, 
                          SCREEN_WIDTH//2 + 150, sy)
            sy += 60
        
        if self.game_message:
            self._draw_text(self.game_message, self.font_medium, COLOR_DANGER, 
                          SCREEN_WIDTH//2, 600, center=True)
        
        for btn in self.cached_buttons[GameState.GAME_OVER]:
            btn.draw(self.screen, self.font_medium)
        
        for event in events:
            for btn in self.cached_buttons[GameState.GAME_OVER]:
                btn.handle_event(event)
    
    def run(self):
        """Main game loop"""
        running = True
        
        while running:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    running = False
                
                if self.state == GameState.PLAYING and not self.show_event_modal:
                    if event.type == pygame.MOUSEWHEEL:
                        self.scroll_offset -= event.y * 30
                        self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))
                        self._update_button_positions()
                        self.close_dropdown()
            
            self.screen.fill(COLOR_BG)
            
            if self.state == GameState.TITLE:
                self._draw_title(events)
            elif self.state == GameState.TUTORIAL:
                self._draw_tutorial(events)
            elif self.state == GameState.SETUP:
                self._draw_setup(events)
            elif self.state == GameState.PLAYING:
                self._draw_playing(events)
            elif self.state == GameState.GAME_OVER:
                self._draw_game_over(events)
            
            if self.show_help_panel:
                self._draw_help_panel(events)
            
            if self.show_event_modal:
                self._draw_event_modal(events)
            
            if self.show_custom_input:
                self._draw_custom_input_modal(events)
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = FinanceGame()
    game.run()