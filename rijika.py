import pygame
import sys
import random
import json
import os
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional, Callable

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 900
FPS = 60

# --- THEME COLORS (Modern Dark Dashboard) ---
COLOR_BG = (15, 23, 42)          # Slate 900
COLOR_PANEL = (30, 41, 59)       # Slate 800
COLOR_PANEL_HOVER = (51, 65, 85) # Slate 700
COLOR_PRIMARY = (56, 189, 248)   # Sky 400
COLOR_SUCCESS = (34, 197, 94)    # Green 500
COLOR_WARNING = (251, 191, 36)   # Amber 400
COLOR_DANGER = (248, 113, 113)   # Red 400
COLOR_TEXT = (241, 245, 249)     # Slate 100
COLOR_TEXT_DIM = (148, 163, 184) # Slate 400
COLOR_ACCENT = (168, 85, 247)    # Purple 500
COLOR_BORDER = (71, 85, 105)     # Slate 600

# Game Configuration
MONTHS_PER_GAME = 24  # Reduced from 36 to make game shorter (2 years instead of 3)
STARTING_HAPPINESS = 50
BURNOUT_STRESS = 100
BURNOUT_HAPPINESS = 10
ACTIONS_PER_MONTH = 3  # Limit number of actions per month

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
    """Optimized button class with better event handling"""
    
    def __init__(self, x: int, y: int, width: int, height: int, text: str, 
                 color=COLOR_PANEL, text_color=COLOR_TEXT, button_id: str = "", tooltip: str = ""):
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
        self.tooltip = tooltip  # Tooltip text to show on hover
        
        # Cache rendered text surfaces for performance
        self._text_cache = {}
        self._cache_dirty = True
        
    def _get_cached_text(self, font, color):
        """Cache rendered text surfaces to avoid re-rendering every frame"""
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
            
        # Determine visual style
        if not self.enabled:
            draw_color = (40, 45, 55)
            draw_text_color = (80, 85, 95)
            border_color = (60, 65, 75)
        elif self.hover:
            c = self.base_color
            # More dramatic hover effect
            draw_color = (min(c[0]+40, 255), min(c[1]+40, 255), min(c[2]+40, 255))
            draw_text_color = self.text_color
            border_color = COLOR_PRIMARY
        else:
            draw_color = self.base_color
            draw_text_color = self.text_color
            border_color = COLOR_BORDER

        # Draw Shadow (enhanced when hovered)
        if self.enabled:
            shadow_offset = 4 if self.hover else 2
            shadow_y = self.rect.y + shadow_offset + 2
            pygame.draw.rect(screen, (10, 10, 15), 
                           (self.rect.x + shadow_offset, shadow_y, self.rect.width, self.rect.height), 
                           border_radius=8)

        # Draw Button Body (slightly offset when hovered for 3D effect)
        button_y = self.rect.y - 2 if self.hover else self.rect.y
        button_rect = pygame.Rect(self.rect.x, button_y, self.rect.width, self.rect.height)
        pygame.draw.rect(screen, draw_color, button_rect, border_radius=8)
        
        # Draw Border (thicker when hovered)
        border_width = 3 if self.hover else 2
        if self.enabled:
            pygame.draw.rect(screen, border_color, button_rect, border_width, border_radius=8)
        
        # Render Text using cache
        lines, surfaces = self._get_cached_text(font, draw_text_color)
        total_height = len(lines) * font.get_linesize()
        start_y = button_rect.centery - total_height // 2
        
        for i, text_surface in enumerate(surfaces):
            text_rect = text_surface.get_rect(
                center=(button_rect.centerx, start_y + i * font.get_linesize() + font.get_linesize()//2)
            )
            screen.blit(text_surface, text_rect)
    
    def draw_tooltip(self, screen, font):
        """Draw tooltip if hovering and tooltip exists"""
        if not self.hover or not self.tooltip or not self.enabled:
            return
        
        # Create tooltip surface
        padding = 10
        tooltip_font = pygame.font.SysFont("Arial", 14)
        
        # Wrap tooltip text
        max_width = 300
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
        
        # Calculate tooltip dimensions
        line_height = tooltip_font.get_linesize()
        tooltip_width = max(tooltip_font.size(line)[0] for line in lines) + padding * 2
        tooltip_height = len(lines) * line_height + padding * 2
        
        # Position tooltip near mouse
        mouse_x, mouse_y = pygame.mouse.get_pos()
        tooltip_x = mouse_x + 15
        tooltip_y = mouse_y + 15
        
        # Keep tooltip on screen
        if tooltip_x + tooltip_width > screen.get_width():
            tooltip_x = mouse_x - tooltip_width - 15
        if tooltip_y + tooltip_height > screen.get_height():
            tooltip_y = mouse_y - tooltip_height - 15
        
        # Draw tooltip background
        tooltip_rect = pygame.Rect(tooltip_x, tooltip_y, tooltip_width, tooltip_height)
        pygame.draw.rect(screen, (20, 20, 30), tooltip_rect, border_radius=6)
        pygame.draw.rect(screen, COLOR_PRIMARY, tooltip_rect, 2, border_radius=6)
        
        # Draw tooltip text
        y = tooltip_y + padding
        for line in lines:
            text_surf = tooltip_font.render(line, True, COLOR_TEXT)
            screen.blit(text_surf, (tooltip_x + padding, y))
            y += line_height
            
    def handle_event(self, event) -> bool:
        """Returns True if button was clicked"""
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
        """Update button text and invalidate cache"""
        if self.text != new_text:
            self.text = new_text
            self._cache_dirty = True


class FinanceGame:
    """Main game class with optimized rendering and state management"""
    
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("FinanceQuest - Life Simulation Game")
        self.clock = pygame.time.Clock()
        
        # Optimize event handling - only allow needed events
        pygame.event.set_allowed([
            pygame.QUIT, 
            pygame.MOUSEBUTTONDOWN, 
            pygame.MOUSEMOTION,
            pygame.MOUSEWHEEL
        ])
        
        # Font cache
        self._init_fonts()
        
        # Game state
        self.state = GameState.TITLE
        self.tutorial_step = 0
        
        # Setup choices
        self.selected_class = None
        self.selected_education = None
        self.selected_difficulty = None
        
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
        
        # UI cache
        self.cached_buttons = {state: [] for state in GameState}
        self.need_button_update = True
        
        # Background surfaces (cache for performance)
        self._bg_cache = {}
        
        # Initialize configurations
        self._init_configs()
        self._init_ui_elements()
        
    def _init_fonts(self):
        """Initialize all fonts"""
        self.font_xl = pygame.font.SysFont("Arial", 64, bold=True)
        self.font_large = pygame.font.SysFont("Arial", 48, bold=True)
        self.font_medium = pygame.font.SysFont("Arial", 28)
        self.font_small = pygame.font.SysFont("Arial", 20)
        self.font_tiny = pygame.font.SysFont("Arial", 16)
    
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
        self.locked_action = None  # Action to repeat next month
        
        # Help system
        self.show_help_panel = False
        self.current_tooltip = ""
        
        # Avatar
        self.selected_avatar = "👤"
    
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
                "No debt", "💼"
            ),
            'middle': ClassConfig(
                "Middle Class", 15000, 1500, 500, 300, 5000,
                "Some starting debt", "👔"
            ),
            'lower': ClassConfig(
                "Lower Class", 2000, 800, 300, 150, 15000,
                "Significant debt burden", "🎒"
            )
        }
        
        self.education_configs = {
            'polytechnic': EducationConfig(
                "Polytechnic", 0, 3500,
                "Standard education level"
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
                "Fewer emergencies, stable markets"
            ),
            'normal': DifficultyConfig(
                "Normal Mode", 0.10, 1.0,
                "Balanced challenge"
            ),
            'hard': DifficultyConfig(
                "Hard Mode", 0.20, 1.5,
                "Frequent emergencies, volatile markets"
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
            EmergencyEvent("Medical Emergency", 
                        "You've been diagnosed with a serious health condition requiring immediate treatment.",
                        cost=8000, stress_increase=30),
            EmergencyEvent("Job Loss",
                        "Your company has downsized and you've been laid off. No income for 3 months.",
                        months_no_income=3, stress_increase=40),
            EmergencyEvent("Market Crash",
                        "The stock market has crashed! Your investments have lost significant value.",
                        investment_loss=0.4, stress_increase=25),
            EmergencyEvent("Home Emergency",
                        "Major repairs needed for your living space.",
                        cost=3500, stress_increase=15),
            EmergencyEvent("Family Emergency",
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
                  COLOR_PRIMARY, text_color=(10,15,30)),
            Button(SCREEN_WIDTH // 2 - 150, 590, 300, 70, "Skip Tutorial", COLOR_PANEL),
            Button(SCREEN_WIDTH - 150, 20, 130, 50, "❓ Help", COLOR_ACCENT)
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
                  COLOR_PANEL_HOVER, button_id="tut_prev"),
            Button(panel_rect.right - 230, btn_y, 180, 50, "Next", 
                  COLOR_PRIMARY, text_color=(10,15,30), button_id="tut_next"),
            Button(SCREEN_WIDTH - 250, 800, 200, 50, "Skip All", 
                  COLOR_PANEL, button_id="tut_skip")
        ]
        
        self.cached_buttons[GameState.TUTORIAL][0].callback = self._tut_prev
        self.cached_buttons[GameState.TUTORIAL][1].callback = self._tut_next
        self.cached_buttons[GameState.TUTORIAL][2].callback = self._tut_skip
    
    def _init_setup_buttons(self):
        """Initialize setup screen buttons"""
        self.cached_buttons[GameState.SETUP] = [
            Button(SCREEN_WIDTH // 2 - 120, 750, 240, 60, "Start Game", 
                  COLOR_SUCCESS, text_color=(10,20,10), button_id="setup_start"),
            Button(SCREEN_WIDTH // 2 - 80, 830, 160, 40, "Back", 
                  COLOR_PANEL, button_id="setup_back")
        ]
        
        self.cached_buttons[GameState.SETUP][0].callback = self.start_game
        self.cached_buttons[GameState.SETUP][1].callback = lambda: setattr(self, 'state', GameState.TITLE)
    
    def _init_game_over_buttons(self):
        """Initialize game over screen buttons"""
        self.cached_buttons[GameState.GAME_OVER] = [
            Button(SCREEN_WIDTH//2 - 220, 680, 200, 60, "Play Again", 
                  COLOR_SUCCESS, text_color=(10,30,10)),
            Button(SCREEN_WIDTH//2 + 20, 680, 200, 60, "Menu", COLOR_PANEL)
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
            
        # Next Month button (always visible)
        next_btn = Button(SCREEN_WIDTH - 220, 15, 200, 50, "Next Month", 
                         COLOR_SUCCESS, text_color=(10,30,10), button_id="next_month")
        next_btn.callback = self.next_month
        self.cached_buttons[GameState.PLAYING].append(next_btn)
        
        # Help button
        help_btn = Button(20, 15, 100, 50, "❓ Help", COLOR_ACCENT, button_id="help")
        help_btn.callback = self._toggle_help
        self.cached_buttons[GameState.PLAYING].append(help_btn)
        
    def _update_playing_buttons(self):
        """Update playing screen buttons based on current game state"""
        # Keep only the Next Month and Help buttons
        self.cached_buttons[GameState.PLAYING] = [
            btn for btn in self.cached_buttons[GameState.PLAYING] 
            if btn.button_id in ["next_month", "help"]
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
                              SCREEN_HEIGHT - header_height - 20)
        
        btn_w = (view_rect.width - 20) // 2
        btn_h = 50
        ay = 10
        
        # Financial Actions with tooltips
        fin_actions = [
            ("Invest $1k", lambda: self.invest_money(1000), self.money >= 1000, COLOR_PANEL, 
             "💰 Invest $1,000 into the market for potential returns"),
            ("Invest $5k", lambda: self.invest_money(5000), self.money >= 5000, COLOR_PANEL,
             "💰 Invest $5,000 for higher potential returns"),
            ("Withdraw $1k", lambda: self.withdraw_investment(1000), self.investments >= 1000, COLOR_PANEL,
             "💸 Cash out $1,000 from investments"),
            ("Withdraw All", lambda: self.withdraw_investment(self.investments), self.investments > 0, COLOR_PANEL,
             "💸 Cash out all investments"),
            ("Save $100", lambda: self.add_to_emergency_fund(100), self.money >= 100, COLOR_PANEL,
             "🏦 Add $100 to emergency fund for safety"),
            ("Pay Debt $1k", lambda: self.pay_off_debt(1000), self.money >= 1000 and self.debt > 0, COLOR_PANEL,
             "💳 Pay down $1,000 of debt and reduce stress"),
        ]
        ay = self._create_section_buttons("FINANCES", fin_actions, ay, btn_w, btn_h, view_rect)
        
        # Lifestyle (only if happiness < 80)
        if self.happiness < 80:
            lifestyle_actions = [
                (f"{c.name}\n${c.cost}", lambda k=k: self.take_life_choice(k), 
                 self.money >= c.cost, COLOR_PANEL,
                 f"😊 {c.name}: +{c.happiness} happiness, {c.stress} stress")
                for k, c in self.life_choices.items() if c.choice_type == 'leisure'
            ]
            if lifestyle_actions:
                ay = self._create_section_buttons("LIFESTYLE", lifestyle_actions, ay, btn_w, btn_h, view_rect)
        
        # Risky choices
        if self.stress < 60 or self.money > 5000:
            risk_actions = [
                (f"{c.name}\n${c.cost}", lambda k=k: self.take_life_choice(k), 
                 self.money >= c.cost, COLOR_PANEL_HOVER,
                 f"⚠️ {c.name}: Risky! {c.debuff_chance*100:.0f}% addiction chance")
                for k, c in self.life_choices.items() if c.choice_type == 'risky'
            ]
            if risk_actions:
                ay = self._create_section_buttons("RISK & VICE", risk_actions, ay, btn_w, btn_h, view_rect)
        
        # Utility/Education
        util_actions = []
        for k, c in self.life_choices.items():
            if c.choice_type in ['utility', 'education']:
                enabled = self._is_choice_available(k, c)
                col = COLOR_PRIMARY if c.choice_type == 'education' else COLOR_PANEL
                tooltip = f"📚 {c.name}: Increases income!" if c.choice_type == 'education' else f"🎁 {c.name}"
                util_actions.append((f"{c.name}\n${c.cost}", lambda k=k: self.take_life_choice(k), enabled, col, tooltip))
        
        if util_actions:
            ay = self._create_section_buttons("GROWTH & ASSETS", util_actions, ay, btn_w, btn_h, view_rect)
        
        # Health actions
        if self.debuffs:
            health_actions = []
            if 'addict' in self.debuffs:
                health_actions.append(("Rehab ($1.5k)", self.treat_addiction, self.money >= 1500, COLOR_DANGER,
                                      "🏥 Treatment for addiction - success depends on happiness"))
            if 'unhappy' in self.debuffs or 'distracted' in self.debuffs:
                health_actions.append(("Therapy ($800)", self.seek_therapy, self.money >= 800, COLOR_DANGER,
                                      "🧠 Clear debuffs and reduce stress"))
            
            if health_actions:
                ay = self._create_section_buttons("HEALTH", health_actions, ay, btn_w, btn_h, view_rect)
        
        # Update max scroll based on content height
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
        """Create buttons for a section and return new y position"""
        ay = start_y + 40
        
        for i, b_data in enumerate(buttons_data):
            label, callback, enabled, color, tooltip = b_data
            
            bx_rel = 0 if i % 2 == 0 else btn_w + 10
            by_rel = ay + (i // 2) * (btn_h + 10)
            
            screen_x = view_rect.x + bx_rel
            screen_y = view_rect.y + by_rel - self.scroll_offset
            original_y = view_rect.y + by_rel
            
            # Check if this action is locked
            is_locked = (self.locked_action and 
                        self.locked_action['callback'] == callback)
            
            # Add lock indicator to label if locked
            display_label = f"🔒 {label}" if is_locked else label
            
            btn = Button(screen_x, screen_y, btn_w, btn_h, display_label, color, 
                        button_id=f"action_{len(self.cached_buttons[GameState.PLAYING])}", 
                        tooltip=tooltip + "\n[Right-click to lock/unlock for next month]")
            btn.original_y = original_y
            btn.enabled = enabled and self.actions_remaining > 0
            btn.callback = callback
            btn.visible = True
            
            # Store original callback for locking
            btn.lock_data = {'name': label, 'callback': callback}
            
            self.cached_buttons[GameState.PLAYING].append(btn)
        
        rows = (len(buttons_data) + 1) // 2
        return ay + rows * (btn_h + 10) + 20
    
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
                              SCREEN_HEIGHT - header_height - 20)
        
        for btn in self.cached_buttons[GameState.PLAYING]:
            if btn.button_id != "next_month":
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
        """Toggle help panel"""
        self.show_help_panel = not self.show_help_panel
    
    def start_game(self):
        """Start a new game with selected configuration"""
        if not all([self.selected_class, self.selected_education, self.selected_difficulty]):
            return
            
        class_config = self.class_configs[self.selected_class]
        edu_config = self.education_configs[self.selected_education]
        
        # Initialize player stats
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
        
        # Reset game state
        self.debuffs = []
        self.months_no_income = 0
        self.has_vehicle = False
        self.current_education_level = self.selected_education
        self.has_university = self.selected_education in ['university', 'masters']
        self.has_masters = self.selected_education == 'masters'
        self.game_message = "Welcome to your financial journey! Good luck."
        
        # Set avatar
        self.selected_avatar = class_config.avatar_emoji
        
        # Action tracking
        self.actions_taken_this_month = 0
        self.actions_remaining = ACTIONS_PER_MONTH
        self.locked_action = None
        
        # Reset goals
        for goal in self.goals.values():
            goal['completed'] = False
        
        # Initialize playing UI
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
        
        # Apply locked action if exists
        if self.locked_action:
            messages.append(f"🔒 Auto: {self.locked_action['name']}")
            self.locked_action['callback']()
        
        # Process income
        messages.extend(self._process_income())
        
        # Process expenses
        self._process_expenses()
        
        # Process debt interest
        if self.debt > 0:
            self.debt *= 1.00417  # Monthly interest
        
        # Process investment returns
        if self.investments > 0:
            self._process_investments()
        
        # Process emergency fund interest
        if self.emergency_fund > 0:
            self.emergency_fund *= 1.00167  # Savings interest
        
        # Update well-being
        self._update_wellbeing(messages)
        
        # Random events
        self._check_random_events()
        
        # Increment month and reset actions
        self.current_month += 1
        self.actions_taken_this_month = 0
        self.actions_remaining = ACTIONS_PER_MONTH
        
        # Update UI
        self.game_message = " | ".join(messages) if messages else f"Month {self.current_month} complete."
        self.check_goals()
        self.need_button_update = True
        
        # Check game over conditions
        if self.money < -10000:
            self.end_game(False, "Bankrupt! Debt exceeded $10,000 limit.")
    
    def _process_income(self) -> List[str]:
        """Process monthly income and return messages"""
        messages = []
        
        if self.months_no_income == 0:
            income = self.monthly_income
            
            if 'distracted' in self.debuffs:
                income *= 0.8
                messages.append("Distracted: -20% income")
                
                # Chance of being fired
                if random.random() < 0.1:
                    self.months_no_income = 2
                    messages.append("Fired due to performance!")
                    self.stress += 30
            
            self.money += income
        else:
            self.months_no_income -= 1
            messages.append(f"No income ({self.months_no_income} months left)")
        
        return messages
    
    def _process_expenses(self):
        """Process monthly expenses"""
        total_expenses = self.rent + self.groceries + self.transport
        self.money -= total_expenses
    
    def _process_investments(self):
        """Process investment returns"""
        difficulty = self.difficulty_configs[self.selected_difficulty]
        monthly_return = (random.random() * 0.25 - 0.10) / 12 * difficulty.market_volatility
        self.investments *= (1 + monthly_return)
    
    def _update_wellbeing(self, messages: List[str]):
        """Update happiness and stress levels"""
        # Natural stress reduction
        self.stress = max(0, self.stress - 2)
        
        # Debt stress
        debt_to_income = self.debt / (self.monthly_income * 12) if self.monthly_income > 0 else 0
        if debt_to_income > 0.5:
            self.stress += 5
        
        # Emergency fund stress
        if self.emergency_fund < self.monthly_income * 3:
            self.stress += 2
        
        # Natural happiness decay
        self.happiness = max(0, self.happiness - 3)
        
        # Debuff effects
        if 'unhappy' in self.debuffs:
            messages.append("You are unhappy!")
        
        # Check for burnout
        if self.stress >= BURNOUT_STRESS or self.happiness <= BURNOUT_HAPPINESS:
            self._trigger_burnout()
        
        # Clamp values
        self.stress = min(100, self.stress)
        self.happiness = min(100, self.happiness)
    
    def _trigger_burnout(self):
        """Trigger burnout event"""
        burnout_event = EmergencyEvent(
            "BURNOUT!",
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
        """Check and trigger random events"""
        difficulty = self.difficulty_configs[self.selected_difficulty]
        
        # Emergency events
        if random.random() < difficulty.emergency_chance:
            event = random.choice(self.emergency_events)
            self.trigger_event(event)
        
        # Random debuffs
        debuff_chance = 0.5 - (self.happiness / 100) * 0.4
        if random.random() < debuff_chance and 'distracted' not in self.debuffs:
            self.debuffs.append('distracted')
            self.stress += 10
    
    def trigger_event(self, event: EmergencyEvent):
        """Trigger an emergency event"""
        self.current_event = event
        self.show_event_modal = True
    
    def handle_event_close(self):
        """Handle closing of event modal and apply effects"""
        if self.current_event:
            if self.current_event.cost > 0:
                self.money -= self.current_event.cost
            
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
        """Execute a life choice"""
        if self.actions_remaining <= 0:
            self.game_message = f"⚠️ No actions left! ({self.actions_taken_this_month}/{ACTIONS_PER_MONTH})"
            return
            
        choice = self.life_choices[choice_key]
        
        # Validate choice
        if not self._validate_life_choice(choice_key, choice):
            return
        
        self.money -= choice.cost
        self.actions_taken_this_month += 1
        self.actions_remaining -= 1
        
        # Handle education upgrades
        if choice.choice_type == 'education':
            self._handle_education_upgrade(choice_key, choice)
            return
        
        # Apply happiness and stress
        self.happiness = min(100, self.happiness + choice.happiness)
        self.stress = max(0, self.stress + choice.stress)
        
        # Handle risky choices
        if choice.choice_type == 'risky':
            if self._handle_risky_choice(choice_key, choice):
                return
        
        # Handle utility choices
        if choice_key == 'vehicle':
            self.has_vehicle = True
        
        self.game_message = f"✨ {choice.name}: Happiness +{choice.happiness:.0f} | Actions: {self.actions_remaining}/{ACTIONS_PER_MONTH}"
        self.need_button_update = True
    
    def _validate_life_choice(self, choice_key: str, choice: LifeChoice) -> bool:
        """Validate if a life choice can be taken"""
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
        """Handle education upgrade choices"""
        if choice_key == 'university':
            self.monthly_income += 1500
            self.has_university = True
            self.current_education_level = 'university'
            self.debt += choice.cost
            self.money += choice.cost
            self.happiness = min(100, self.happiness + 10)
            self.stress = min(100, self.stress + 15)
            self.game_message = "Degree Earned! Income +$1500/mo (Added to debt)"
        elif choice_key == 'masters':
            self.monthly_income += 1000
            self.has_masters = True
            self.current_education_level = 'masters'
            self.debt += choice.cost
            self.money += choice.cost
            self.happiness = min(100, self.happiness + 15)
            self.stress = min(100, self.stress + 20)
            self.game_message = "Masters Earned! Income +$1000/mo (Added to debt)"
        
        self.need_button_update = True
    
    def _handle_risky_choice(self, choice_key: str, choice: LifeChoice) -> bool:
        """Handle risky choice outcomes. Returns True if special outcome occurred."""
        if choice_key == 'gambling' and random.random() < choice.win_chance:
            self.money += choice.win_amount
            self.game_message = f"You won ${choice.win_amount:.0f}!"
            self.need_button_update = True
            return True
        
        if choice.debuff_chance > 0 and random.random() < choice.debuff_chance:
            if choice.debuff not in self.debuffs:
                self.debuffs.append(choice.debuff)
                self.game_message = f"Addicted to {choice.name}!"
                self.need_button_update = True
                return True
        
        return False
    
    def invest_money(self, amount: float):
        """Invest money"""
        if self.actions_remaining <= 0:
            self.game_message = f"⚠️ No actions left! ({self.actions_taken_this_month}/{ACTIONS_PER_MONTH})"
            return
            
        if self.money >= amount:
            self.money -= amount
            self.investments += amount
            self.actions_taken_this_month += 1
            self.actions_remaining -= 1
            self.game_message = f"💰 Invested ${amount:.0f} | Actions: {self.actions_remaining}/{ACTIONS_PER_MONTH}"
            self.need_button_update = True
    
    def withdraw_investment(self, amount: float):
        """Withdraw from investments"""
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
        """Add to emergency fund"""
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
        """Pay off debt"""
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
            self.need_button_update = True
    
    def treat_addiction(self):
        """Treat addiction"""
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
        else:
            self.game_message = f"❌ Treatment failed. Need higher happiness. | Actions: {self.actions_remaining}/{ACTIONS_PER_MONTH}"
        
        self.need_button_update = True
    
    def seek_therapy(self):
        """Seek therapy"""
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
        self.need_button_update = True
    
    def check_goals(self):
        """Check and update goal completion status"""
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
        """Calculate final game score"""
        net_worth = self.money + self.investments + self.emergency_fund - self.debt
        goal_bonus = sum(1 for g in self.goals.values() if g['completed']) * 5000
        happiness_bonus = self.happiness * 100
        month_bonus = self.current_month * 500
        
        return max(0, int(net_worth + goal_bonus + happiness_bonus + month_bonus))
    
    def end_game(self, completed: bool, reason: str = ''):
        """End the game and transition to game over screen"""
        score = self.calculate_score()
        
        if score > self.high_score:
            self.high_score = score
            self._save_high_score()
        
        self.game_message = reason or ('Game completed!' if completed else 'Game over!')
        self.state = GameState.GAME_OVER
    
    # --- Drawing Helper Methods ---
    
    def _draw_text(self, text: str, font, color, x: int, y: int, 
                  center: bool = False, shadow: bool = False):
        """Draw text with optional shadow"""
        if shadow:
            shadow_surf = font.render(text, True, (0, 0, 0))
            shadow_rect = shadow_surf.get_rect(center=(x + 2, y + 2) if center else (x + 2, y + 2))
            if not center:
                shadow_rect.topleft = (x + 2, y + 2)
            self.screen.blit(shadow_surf, shadow_rect)

        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(center=(x, y) if center else (x, y))
        if not center:
            text_rect.topleft = (x, y)
        self.screen.blit(text_surface, text_rect)
    
    def _draw_progress_bar(self, x: int, y: int, width: int, height: int, 
                          percentage: float, color, bg_color=COLOR_PANEL):
        """Draw a progress bar"""
        # Background
        pygame.draw.rect(self.screen, bg_color, (x, y, width, height), border_radius=height//2)
        # Fill
        fill_width = int(width * max(0, min(100, percentage)) / 100)
        if fill_width > 0:
            pygame.draw.rect(self.screen, color, (x, y, fill_width, height), border_radius=height//2)
        # Border
        pygame.draw.rect(self.screen, COLOR_BORDER, (x, y, width, height), 1, border_radius=height//2)
    
    def _wrap_text(self, text: str, font, max_width: int) -> List[str]:
        """Wrap text to fit within max_width"""
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
        """Draw title screen"""
        # Decorative background
        pygame.draw.circle(self.screen, (20, 30, 50), 
                         (SCREEN_WIDTH//2, SCREEN_HEIGHT//2), 400)
        
        # Title
        self._draw_text("FINANCE QUEST", self.font_xl, COLOR_PRIMARY, 
                       SCREEN_WIDTH // 2, 250, center=True, shadow=True)
        
        # Subtitle
        self._draw_text("Master Your Financial Future", self.font_medium, COLOR_TEXT_DIM, 
                       SCREEN_WIDTH // 2, 320, center=True)
        
        # High score display
        if self.high_score > 0:
            pygame.draw.rect(self.screen, COLOR_PANEL, 
                           (SCREEN_WIDTH//2 - 150, 380, 300, 50), border_radius=10)
            self._draw_text(f"High Score: {self.high_score:,}", self.font_medium, COLOR_WARNING, 
                          SCREEN_WIDTH // 2, 405, center=True)
        
        # Draw buttons
        for btn in self.cached_buttons[GameState.TITLE]:
            btn.draw(self.screen, self.font_medium)
        
        # Handle events
        for event in events:
            for btn in self.cached_buttons[GameState.TITLE]:
                btn.handle_event(event)

    def _draw_tutorial(self, events):
        """Draw tutorial screen"""
        tutorials = [
            ("Welcome to FinanceQuest!", 
             "Simulate 3 years of financial decisions. Build wealth, maintain well-being, and achieve your goals."),
            ("Core Mechanics", 
             "Every turn is one month. Manage income, expenses, and investments. Watch your Happiness and Stress!"),
            ("Well-Being System", 
             "High Stress causes Burnout. Low Happiness causes Debuffs. Keep a balance to succeed."),
            ("Winning", 
             "Complete the 4 main goals to earn bonus points. Your final score depends on Net Worth and happiness.")
        ]
        
        title, content = tutorials[self.tutorial_step]
        
        # Panel
        panel_rect = pygame.Rect(200, 150, SCREEN_WIDTH - 400, 500)
        pygame.draw.rect(self.screen, COLOR_PANEL, panel_rect, border_radius=20)
        pygame.draw.rect(self.screen, COLOR_BORDER, panel_rect, 2, border_radius=20)
        
        # Header
        pygame.draw.rect(self.screen, COLOR_PANEL_HOVER, 
                        (200, 150, SCREEN_WIDTH-400, 80), 
                        border_top_left_radius=20, border_top_right_radius=20)
        self._draw_text(f"Tutorial {self.tutorial_step + 1}/{len(tutorials)}", 
                       self.font_medium, COLOR_ACCENT, SCREEN_WIDTH // 2, 190, center=True)
        
        self._draw_text(title, self.font_large, COLOR_PRIMARY, 
                       SCREEN_WIDTH // 2, 280, center=True)
        
        # Wrapped text
        lines = self._wrap_text(content, self.font_medium, panel_rect.width - 100)
        y = 360
        for line in lines:
            self._draw_text(line, self.font_medium, COLOR_TEXT, 
                          SCREEN_WIDTH // 2, y, center=True)
            y += 40
        
        # Update button states
        next_text = "Next" if self.tutorial_step < 3 else "Start Setup"
        self.cached_buttons[GameState.TUTORIAL][1].update_text(next_text)
        self.cached_buttons[GameState.TUTORIAL][0].enabled = self.tutorial_step > 0
        
        # Draw buttons
        for btn in self.cached_buttons[GameState.TUTORIAL]:
            btn.draw(self.screen, self.font_small)
        
        # Handle events
        for event in events:
            for btn in self.cached_buttons[GameState.TUTORIAL]:
                btn.handle_event(event)

    def _draw_setup(self, events):
        """Draw setup screen"""
        self._draw_text("Character Setup", self.font_large, COLOR_PRIMARY, 
                       SCREEN_WIDTH // 2, 50, center=True)
        
        # Grid layout
        cols = 3
        section_width = 380
        gap = 40
        start_x = (SCREEN_WIDTH - (cols * section_width + (cols-1)*gap)) // 2
        
        # Draw class selection
        self._draw_class_selection(start_x, section_width, events)
        
        # Draw education selection
        self._draw_education_selection(start_x + section_width + gap, section_width, events)
        
        # Draw difficulty selection
        self._draw_difficulty_selection(start_x + (section_width + gap) * 2, section_width, events)
        
        # Update start button state
        self.cached_buttons[GameState.SETUP][0].enabled = all([
            self.selected_class, self.selected_education, self.selected_difficulty
        ])
        
        # Draw buttons
        for btn in self.cached_buttons[GameState.SETUP]:
            font = self.font_small if btn.button_id == "setup_back" else self.font_medium
            btn.draw(self.screen, font)
        
        # Handle events
        for event in events:
            for btn in self.cached_buttons[GameState.SETUP]:
                btn.handle_event(event)

    def _draw_class_selection(self, x: int, width: int, events):
        """Draw social class selection"""
        y = 120
        self._draw_text("Social Class", self.font_medium, COLOR_ACCENT, 
                       x + width//2, y, center=True)
        y += 40
        
        for key, config in self.class_configs.items():
            color = COLOR_PRIMARY if self.selected_class == key else COLOR_PANEL
            text_color = (10,15,30) if self.selected_class == key else COLOR_TEXT
            
            btn = Button(x, y, width, 100, 
                        f"{config.avatar_emoji} {config.name}\nStart: ${config.starting_money:,.0f}\nDebt: ${config.debt:,.0f}", 
                        color, text_color, button_id=f"class_{key}")
            btn.draw(self.screen, self.font_small)
            
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if btn.rect.collidepoint(event.pos):
                        self.selected_class = key
            
            y += 110

    def _draw_education_selection(self, x: int, width: int, events):
        """Draw education selection"""
        y = 120
        self._draw_text("Education", self.font_medium, COLOR_ACCENT, 
                       x + width//2, y, center=True)
        y += 40
        
        for key, config in self.education_configs.items():
            color = COLOR_PRIMARY if self.selected_education == key else COLOR_PANEL
            text_color = (10,15,30) if self.selected_education == key else COLOR_TEXT
            
            cost_text = "Free" if config.cost == 0 else f"Cost: ${config.cost:,}"
            btn = Button(x, y, width, 100, 
                        f"{config.name}\nIncome: ${config.income:,.0f}/mo\n{cost_text}", 
                        color, text_color, button_id=f"edu_{key}")
            btn.draw(self.screen, self.font_small)
            
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if btn.rect.collidepoint(event.pos):
                        self.selected_education = key
            
            y += 110

    def _draw_difficulty_selection(self, x: int, width: int, events):
        """Draw difficulty selection"""
        y = 120
        self._draw_text("Difficulty", self.font_medium, COLOR_ACCENT, 
                       x + width//2, y, center=True)
        y += 40
        
        for key, config in self.difficulty_configs.items():
            color = COLOR_PRIMARY if self.selected_difficulty == key else COLOR_PANEL
            text_color = (10,15,30) if self.selected_difficulty == key else COLOR_TEXT
            
            btn = Button(x, y, width, 100, 
                        f"{config.name}\n{config.description}", 
                        color, text_color, button_id=f"diff_{key}")
            btn.draw(self.screen, self.font_small)
            
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if btn.rect.collidepoint(event.pos):
                        self.selected_difficulty = key
            
            y += 110

    def _draw_playing(self, events):
        """Draw main playing screen"""
        # Update buttons if needed
        if self.need_button_update:
            self._update_playing_buttons()
        
        self._update_button_positions()
        
        # Draw header
        self._draw_playing_header()
        
        # Define layout
        header_height = 80
        sidebar_w = 350
        action_panel_w = 400
        main_area_w = SCREEN_WIDTH - sidebar_w - action_panel_w
        
        # Draw sections
        self._draw_playing_sidebar(sidebar_w, header_height)
        self._draw_playing_main(sidebar_w, main_area_w, header_height)
        self._draw_playing_actions(action_panel_w, header_height)
        
        # Handle events
        for event in events:
            # Handle right-click for locking actions
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:  # Right click
                mouse_pos = event.pos
                for btn in self.cached_buttons[GameState.PLAYING]:
                    if btn.visible and btn.rect.collidepoint(mouse_pos) and hasattr(btn, 'lock_data'):
                        # Toggle lock
                        if self.locked_action and self.locked_action['callback'] == btn.lock_data['callback']:
                            self.locked_action = None
                            self.game_message = "🔓 Action unlocked"
                        else:
                            self.locked_action = btn.lock_data
                            self.game_message = f"🔒 Locked: {btn.lock_data['name']} (will auto-execute next month)"
                        self.need_button_update = True
                        break
            
            # Handle help and next month buttons first (they're always visible)
            for btn in self.cached_buttons[GameState.PLAYING]:
                if btn.button_id in ["next_month", "help"]:
                    btn.handle_event(event)
            
            # Then handle action buttons
            for btn in self.cached_buttons[GameState.PLAYING]:
                if btn.button_id not in ["next_month", "help"]:
                    btn.handle_event(event)
        
        # Handle mouse motion for all buttons
        mouse_pos = pygame.mouse.get_pos()
        for btn in self.cached_buttons[GameState.PLAYING]:
            if btn.visible:
                btn.hover = btn.rect.collidepoint(mouse_pos)

    def _draw_playing_header(self):
        """Draw playing screen header"""
        header_height = 80
        pygame.draw.rect(self.screen, COLOR_PANEL, (0, 0, SCREEN_WIDTH, header_height))
        pygame.draw.line(self.screen, COLOR_BORDER, (0, header_height), 
                        (SCREEN_WIDTH, header_height), 1)
        
        net_worth = self.money + self.investments + self.emergency_fund - self.debt
        
        # Avatar display
        avatar_size = 50
        pygame.draw.circle(self.screen, COLOR_PRIMARY, (90, 40), avatar_size // 2 + 5)
        self._draw_text(self.selected_avatar, self.font_large, COLOR_TEXT, 90, 40, center=True)
        
        self._draw_text("FINANCE QUEST", self.font_large, COLOR_PRIMARY, 150, 15)
        
        # Stats widgets
        widgets = [
            ("MONTH", f"{self.current_month}/{MONTHS_PER_GAME}", COLOR_TEXT),
            ("CASH", f"${self.money:,.0f}", 
             COLOR_SUCCESS if self.money > 0 else COLOR_DANGER),
            ("NET WORTH", f"${net_worth:,.0f}", 
             COLOR_PRIMARY if net_worth > 0 else COLOR_WARNING),
        ]
        
        wx = 550
        for label, val, col in widgets:
            self._draw_text(label, self.font_tiny, COLOR_TEXT_DIM, wx, 15)
            self._draw_text(val, self.font_medium, col, wx, 35)
            wx += 200
        
        # Actions remaining display (prominent)
        actions_x = SCREEN_WIDTH - 400
        actions_color = COLOR_SUCCESS if self.actions_remaining > 1 else COLOR_WARNING if self.actions_remaining == 1 else COLOR_DANGER
        pygame.draw.rect(self.screen, COLOR_PANEL_HOVER, (actions_x, 15, 150, 50), border_radius=8)
        pygame.draw.rect(self.screen, actions_color, (actions_x, 15, 150, 50), 2, border_radius=8)
        self._draw_text("ACTIONS", self.font_tiny, COLOR_TEXT_DIM, actions_x + 75, 25, center=True)
        self._draw_text(f"{self.actions_remaining}/{ACTIONS_PER_MONTH}", self.font_medium, actions_color, 
                       actions_x + 75, 45, center=True)

    def _draw_playing_sidebar(self, sidebar_w: int, header_height: int):
        """Draw left sidebar with detailed stats"""
        sidebar_rect = pygame.Rect(0, header_height, sidebar_w, SCREEN_HEIGHT - header_height)
        pygame.draw.rect(self.screen, (12, 20, 35), sidebar_rect)
        pygame.draw.line(self.screen, COLOR_BORDER, (sidebar_w, header_height), 
                        (sidebar_w, SCREEN_HEIGHT))
        
        sy = header_height + 20
        padding = 30
        
        # Well-being section
        self._draw_text("WELL-BEING", self.font_small, COLOR_TEXT_DIM, padding, sy)
        sy += 30
        self._draw_text(f"Happiness: {self.happiness:.0f}%", self.font_small, COLOR_TEXT, padding, sy)
        self._draw_progress_bar(padding, sy+25, sidebar_w - 60, 10, self.happiness, COLOR_SUCCESS)
        sy += 50
        self._draw_text(f"Stress: {self.stress:.0f}%", self.font_small, COLOR_TEXT, padding, sy)
        self._draw_progress_bar(padding, sy+25, sidebar_w - 60, 10, self.stress, COLOR_DANGER)
        
        sy += 60
        pygame.draw.line(self.screen, COLOR_PANEL_HOVER, (padding, sy), (sidebar_w - padding, sy))
        sy += 20
        
        # Finances section
        self._draw_text("FINANCES", self.font_small, COLOR_TEXT_DIM, padding, sy)
        sy += 30
        
        fin_items = [
            ("Income", f"+${self.monthly_income:,.0f}/mo", COLOR_SUCCESS),
            ("Expenses", f"-${(self.rent+self.groceries+self.transport):,.0f}/mo", COLOR_DANGER),
            ("Debt", f"${self.debt:,.0f}", COLOR_DANGER),
            ("Investments", f"${self.investments:,.0f}", COLOR_PRIMARY),
            ("Emergency Fund", f"${self.emergency_fund:,.0f}", COLOR_WARNING),
        ]
        
        for label, val, col in fin_items:
            self._draw_text(label, self.font_small, COLOR_TEXT, padding, sy)
            self._draw_text(val, self.font_small, col, sidebar_w - padding - 100, sy)
            sy += 30
        
        sy += 20
        pygame.draw.line(self.screen, COLOR_PANEL_HOVER, (padding, sy), (sidebar_w - padding, sy))
        sy += 20
        
        # Status section
        self._draw_text("STATUS", self.font_small, COLOR_TEXT_DIM, padding, sy)
        sy += 30
        edu_name = self.education_configs[self.current_education_level].name
        self._draw_text("Education:", self.font_small, COLOR_TEXT, padding, sy)
        self._draw_text(edu_name, self.font_small, COLOR_ACCENT, padding + 100, sy)
        
        # Debuffs
        if self.debuffs:
            sy += 40
            self._draw_text("Active Effects:", self.font_small, COLOR_DANGER, padding, sy)
            sy += 25
            for d in self.debuffs:
                pygame.draw.rect(self.screen, COLOR_DANGER, (padding, sy, 120, 24), border_radius=4)
                self._draw_text(d.upper(), self.font_tiny, (50,0,0), padding + 10, sy + 4)
                sy += 30

    def _draw_playing_main(self, sidebar_w: int, main_area_w: int, header_height: int):
        """Draw main center area with goals and messages"""
        mx = sidebar_w + 20
        my = header_height + 20
        
        # Goals
        self._draw_text("CURRENT GOALS", self.font_small, COLOR_TEXT_DIM, mx, my)
        my += 30
        
        goal_w = (main_area_w - 60) // 2
        goal_h = 70
        
        goal_items = list(self.goals.values())
        for i, goal in enumerate(goal_items):
            gx = mx if i % 2 == 0 else mx + goal_w + 20
            gy = my + (i // 2) * (goal_h + 15)
            
            g_color = COLOR_SUCCESS if goal['completed'] else COLOR_PANEL_HOVER
            border = COLOR_SUCCESS if goal['completed'] else COLOR_BORDER
            
            pygame.draw.rect(self.screen, g_color if goal['completed'] else COLOR_PANEL, 
                           (gx, gy, goal_w, goal_h), border_radius=10)
            pygame.draw.rect(self.screen, border, (gx, gy, goal_w, goal_h), 2, border_radius=10)
            
            status_icon = "✔" if goal['completed'] else "○"
            text_color = (10,30,10) if goal['completed'] else COLOR_TEXT
            self._draw_text(f"{status_icon} {goal['label']}", self.font_small, 
                          text_color, gx + 15, gy + 25)
        
        # Message log
        msg_y = my + 200
        msg_bg_rect = pygame.Rect(mx, msg_y, main_area_w - 40, 100)
        pygame.draw.rect(self.screen, COLOR_PANEL, msg_bg_rect, border_radius=10)
        pygame.draw.rect(self.screen, COLOR_PRIMARY, msg_bg_rect, 1, border_radius=10)
        
        self._draw_text("EVENT LOG", self.font_tiny, COLOR_PRIMARY, mx + 15, msg_y + 10)
        
        lines = self.game_message.split('|')
        ly = msg_y + 35
        for line in lines:
            self._draw_text(line.strip(), self.font_medium, COLOR_TEXT, mx + 15, ly)
            ly += 25

    def _draw_playing_actions(self, action_panel_w: int, header_height: int):
        """Draw right action panel"""
        action_rect = pygame.Rect(SCREEN_WIDTH - action_panel_w, header_height, 
                                 action_panel_w, SCREEN_HEIGHT - header_height)
        pygame.draw.rect(self.screen, (20, 28, 45), action_rect)
        pygame.draw.line(self.screen, COLOR_BORDER, (action_rect.x, header_height), 
                        (action_rect.x, SCREEN_HEIGHT))
        
        # Draw action buttons
        for btn in self.cached_buttons[GameState.PLAYING]:
            btn.draw(self.screen, self.font_tiny)
        
        # Draw tooltips on top (last so they appear over everything)
        for btn in self.cached_buttons[GameState.PLAYING]:
            btn.draw_tooltip(self.screen, self.font_tiny)

    def _draw_help_panel(self, events):
        """Draw help panel overlay"""
        # Semi-transparent background
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Help panel
        panel_w, panel_h = 800, 600
        panel_x = (SCREEN_WIDTH - panel_w) // 2
        panel_y = (SCREEN_HEIGHT - panel_h) // 2
        
        pygame.draw.rect(self.screen, COLOR_BG, (panel_x, panel_y, panel_w, panel_h), border_radius=15)
        pygame.draw.rect(self.screen, COLOR_PRIMARY, (panel_x, panel_y, panel_w, panel_h), 3, border_radius=15)
        
        # Title
        self._draw_text("📚 QUICK REFERENCE GUIDE", self.font_large, COLOR_PRIMARY, 
                       panel_x + panel_w // 2, panel_y + 40, center=True)
        
        # Help content
        help_sections = [
            ("🎯 Goal", "Complete 24 months with high net worth and happiness!"),
            ("⚡ Actions", f"You have {ACTIONS_PER_MONTH} actions per month. Use them wisely!"),
            ("💰 Money Tips", "• Invest early for compound returns\n• Keep 3 months income as emergency fund\n• Pay off high-interest debt first"),
            ("😊 Well-being", "• Low happiness causes debuffs\n• High stress leads to burnout\n• Balance work and life!"),
            ("🎓 Education", "• Increases monthly income permanently\n• Costs added to debt\n• Higher education = higher income"),
            ("⚠️ Warning Signs", "• Red money = trouble ahead\n• Orange stress bar = burnout risk\n• Debuffs reduce your income"),
        ]
        
        y = panel_y + 100
        x = panel_x + 40
        
        for title, content in help_sections:
            self._draw_text(title, self.font_small, COLOR_ACCENT, x, y)
            y += 30
            
            lines = content.split('\n')
            for line in lines:
                self._draw_text(line, self.font_tiny, COLOR_TEXT, x + 20, y)
                y += 22
            
            y += 10
        
        # Close button
        close_btn = Button(panel_x + panel_w // 2 - 100, panel_y + panel_h - 70, 
                          200, 50, "Close", COLOR_PRIMARY, text_color=(10,20,30))
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
        """Draw emergency event modal"""
        # Dim background
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Modal box
        w, h = 600, 400
        x, y = (SCREEN_WIDTH - w)//2, (SCREEN_HEIGHT - h)//2
        
        pygame.draw.rect(self.screen, COLOR_BG, (x, y, w, h), border_radius=15)
        pygame.draw.rect(self.screen, COLOR_ACCENT, (x, y, w, h), 2, border_radius=15)
        
        # Title
        self._draw_text(self.current_event.name, self.font_large, COLOR_ACCENT, 
                       x + w//2, y + 50, center=True)
        
        # Description
        lines = self._wrap_text(self.current_event.description, self.font_medium, w - 60)
        ty = y + 120
        for line in lines:
            self._draw_text(line, self.font_medium, COLOR_TEXT, x + w//2, ty, center=True)
            ty += 35
        
        # Impact
        impact_y = ty + 30
        if self.current_event.cost > 0:
            self._draw_text(f"Cost: -${self.current_event.cost:,.0f}", self.font_medium, 
                          COLOR_DANGER, x+w//2, impact_y, center=True)
            impact_y += 30
        if self.current_event.stress_increase > 0:
            self._draw_text(f"Stress: +{self.current_event.stress_increase}%", self.font_medium, 
                          COLOR_DANGER, x+w//2, impact_y, center=True)
        
        # Continue button
        cont_btn = Button(x + w//2 - 100, y + h - 80, 200, 50, "Continue", 
                         COLOR_PRIMARY, text_color=(10,20,30))
        cont_btn.callback = self.handle_event_close
        cont_btn.draw(self.screen, self.font_medium)
        
        # Handle hover and clicks
        mouse_pos = pygame.mouse.get_pos()
        cont_btn.hover = cont_btn.rect.collidepoint(mouse_pos)
        
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if cont_btn.hover:
                    self.handle_event_close()

    def _draw_game_over(self, events):
        """Draw game over screen"""
        # Panel
        pygame.draw.rect(self.screen, COLOR_PANEL, 
                        (SCREEN_WIDTH//2 - 400, 100, 800, 700), border_radius=20)
        pygame.draw.rect(self.screen, COLOR_BORDER, 
                        (SCREEN_WIDTH//2 - 400, 100, 800, 700), 2, border_radius=20)
        
        # Title
        score = self.calculate_score()
        title = "NEW HIGH SCORE!" if score > self.high_score else "GAME OVER"
        col = COLOR_WARNING if score > self.high_score else COLOR_TEXT
        
        self._draw_text(title, self.font_xl, col, SCREEN_WIDTH//2, 180, center=True, shadow=True)
        self._draw_text(f"Final Score: {score:,}", self.font_large, COLOR_PRIMARY, 
                       SCREEN_WIDTH//2, 260, center=True)
        
        # Stats
        stats = [
            ("Net Worth", f"${(self.money + self.investments + self.emergency_fund - self.debt):,.0f}"),
            ("Happiness", f"{self.happiness:.0f}%"),
            ("Goals Met", f"{sum(1 for g in self.goals.values() if g['completed'])}/4"),
            ("Months", f"{self.current_month}")
        ]
        
        sy = 350
        for label, val in stats:
            self._draw_text(label, self.font_medium, COLOR_TEXT_DIM, 
                          SCREEN_WIDTH//2 - 100, sy)
            self._draw_text(val, self.font_medium, COLOR_TEXT, 
                          SCREEN_WIDTH//2 + 100, sy)
            sy += 50
        
        # Message
        if self.game_message:
            self._draw_text(self.game_message, self.font_medium, COLOR_DANGER, 
                          SCREEN_WIDTH//2, 600, center=True)
        
        # Draw buttons
        for btn in self.cached_buttons[GameState.GAME_OVER]:
            btn.draw(self.screen, self.font_medium)
        
        # Handle events
        for event in events:
            for btn in self.cached_buttons[GameState.GAME_OVER]:
                btn.handle_event(event)
    
    def run(self):
        """Main game loop"""
        running = True
        
        while running:
            # Event processing
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    running = False
                
                # Handle scrolling in playing state
                if self.state == GameState.PLAYING and not self.show_event_modal:
                    if event.type == pygame.MOUSEWHEEL:
                        self.scroll_offset -= event.y * 30
                        self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))
                        self._update_button_positions()
            
            # Clear screen
            self.screen.fill(COLOR_BG)
            
            # Draw current state
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
            
            # Draw help panel if showing
            if self.show_help_panel and self.state == GameState.PLAYING:
                self._draw_help_panel(events)
            
            # Draw event modal if showing
            if self.show_event_modal:
                self._draw_event_modal(events)
            
            # Update display
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = FinanceGame()
    game.run()