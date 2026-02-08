import pygame
import sys
import random
import json
import os
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional

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
MONTHS_PER_GAME = 36
STARTING_HAPPINESS = 50
BURNOUT_STRESS = 100
BURNOUT_HAPPINESS = 10

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
    def __init__(self, x, y, width, height, text, color=COLOR_PANEL, text_color=COLOR_TEXT, button_id=""):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.base_color = color
        self.text_color = text_color
        self.hover = False
        self.enabled = True
        self.callback = None
        self.button_id = button_id
        self.visible = True
        self.original_y = y  # Store original position for scrolling
        
    def draw(self, screen, font):
        if not self.visible:
            return
            
        # Determine visual style
        if not self.enabled:
            draw_color = (40, 45, 55)
            draw_text_color = (80, 85, 95)
            border_color = (60, 65, 75)
        elif self.hover:
            # Lighten color for hover
            c = self.base_color
            draw_color = (min(c[0]+20, 255), min(c[1]+20, 255), min(c[2]+20, 255))
            draw_text_color = self.text_color
            border_color = COLOR_PRIMARY
        else:
            draw_color = self.base_color
            draw_text_color = self.text_color
            border_color = COLOR_BORDER

        # Draw Shadow
        if self.enabled:
            pygame.draw.rect(screen, (10, 10, 15), (self.rect.x + 2, self.rect.y + 4, self.rect.width, self.rect.height), border_radius=8)

        # Draw Button Body
        pygame.draw.rect(screen, draw_color, self.rect, border_radius=8)
        
        # Draw Border
        if self.enabled:
            pygame.draw.rect(screen, border_color, self.rect, 2, border_radius=8)
        
        # Render Text
        lines = self.text.split('\n')
        total_height = len(lines) * font.get_linesize()
        start_y = self.rect.centery - total_height // 2
        
        for i, line in enumerate(lines):
            text_surface = font.render(line, True, draw_text_color)
            text_rect = text_surface.get_rect(center=(self.rect.centerx, start_y + i * font.get_linesize() + font.get_linesize()//2))
            screen.blit(text_surface, text_rect)
            
    def handle_event(self, event):
        if not self.visible or not self.enabled:
            return False

        mouse_pos = pygame.mouse.get_pos()
        
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(mouse_pos)
        
        # Trigger immediately on Mouse Down
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.hover and event.button == 1:
                if self.callback:
                    self.callback()
                return True
                
        return False

class FinanceGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("FinanceQuest - Life Simulation Game")
        self.clock = pygame.time.Clock()
        
        # Optimize event handling
        pygame.event.set_allowed([
            pygame.QUIT, 
            pygame.MOUSEBUTTONDOWN, 
            pygame.MOUSEBUTTONUP, 
            pygame.MOUSEMOTION,
            pygame.MOUSEWHEEL
        ])
        
        # Fonts
        self.font_xl = pygame.font.SysFont("Arial", 64, bold=True)
        self.font_large = pygame.font.SysFont("Arial", 48, bold=True)
        self.font_medium = pygame.font.SysFont("Arial", 28)
        self.font_small = pygame.font.SysFont("Arial", 20)
        self.font_tiny = pygame.font.SysFont("Arial", 16)
        
        # Game state
        self.state = GameState.TITLE
        self.tutorial_step = 0
        
        # Setup choices
        self.selected_class = None
        self.selected_education = None
        self.selected_difficulty = None
        
        # Player stats
        self.money = 0.0
        self.monthly_income = 0.0
        self.debt = 0.0
        self.investments = 0.0
        self.emergency_fund = 0.0
        self.happiness = STARTING_HAPPINESS
        self.stress = 0.0
        self.current_month = 0
        
        # Expenses
        self.rent = 0.0
        self.groceries = 0.0
        self.transport = 0.0
        
        # Game state variables
        self.debuffs = []
        self.months_no_income = 0
        self.has_vehicle = False
        self.current_education_level = 'polytechnic'
        self.has_university = False
        self.has_masters = False
        self.game_message = ""
        self.high_score = self.load_high_score()
        
        # Goals
        self.goals = {
            'netWorth': {'target': 50000, 'completed': False, 'label': 'Net Worth $50k'},
            'emergencyFund': {'target': 10000, 'completed': False, 'label': 'Save $10k Fund'},
            'debtFree': {'completed': False, 'label': 'Become Debt-Free'},
            'happiness': {'target': 70, 'completed': False, 'label': '70+ Happiness'}
        }
        
        # Event modal
        self.show_event_modal = False
        self.current_event = None
        
        # Scroll offset for actions
        self.scroll_offset = 0
        
        # Cached UI elements
        self.cached_buttons = {
            'title': [],
            'tutorial': [],
            'setup': [],
            'playing': [],
            'game_over': []
        }
        self.need_button_update = True
        
        # Initialize configurations
        self.init_configs()
        self.init_ui_elements()
        
    def init_configs(self):
        self.class_configs = {
            'upper': ClassConfig(
                "Upper Class", 50000, 2500, 800, 400, 0,
                "No debt"
            ),
            'middle': ClassConfig(
                "Middle Class", 15000, 1500, 500, 300, 5000,
                "Some starting debt"
            ),
            'lower': ClassConfig(
                "Lower Class", 2000, 800, 300, 150, 15000,
                "Significant debt burden"
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
    
    def init_ui_elements(self):
        """Initialize all UI buttons once, reuse them"""
        self.init_title_buttons()
        self.init_tutorial_buttons()
        self.init_setup_buttons()
        self.init_game_over_buttons()
        
    def init_title_buttons(self):
        """Initialize title screen buttons"""
        self.cached_buttons['title'] = [
            Button(SCREEN_WIDTH // 2 - 150, 500, 300, 70, "New Game", COLOR_PRIMARY, text_color=(10,15,30)),
            Button(SCREEN_WIDTH // 2 - 150, 590, 300, 70, "Skip Tutorial", COLOR_PANEL)
        ]
        
        # Set callbacks
        self.cached_buttons['title'][0].callback = lambda: setattr(self, 'state', GameState.TUTORIAL)
        self.cached_buttons['title'][1].callback = lambda: setattr(self, 'state', GameState.SETUP)
    
    def init_tutorial_buttons(self):
        """Initialize tutorial screen buttons"""
        panel_rect = pygame.Rect(200, 150, SCREEN_WIDTH - 400, 500)
        btn_y = panel_rect.bottom - 90
        
        self.cached_buttons['tutorial'] = [
            Button(panel_rect.left + 50, btn_y, 180, 50, "Previous", COLOR_PANEL_HOVER, button_id="tut_prev"),
            Button(panel_rect.right - 230, btn_y, 180, 50, "Next", COLOR_PRIMARY, text_color=(10,15,30), button_id="tut_next"),
            Button(SCREEN_WIDTH - 250, 800, 200, 50, "Skip All", COLOR_PANEL, button_id="tut_skip")
        ]
        
        # Set callbacks
        self.cached_buttons['tutorial'][0].callback = self.tut_prev
        self.cached_buttons['tutorial'][1].callback = self.tut_next
        self.cached_buttons['tutorial'][2].callback = self.tut_skip
    
    def init_setup_buttons(self):
        """Initialize setup screen buttons"""
        self.cached_buttons['setup'] = [
            Button(SCREEN_WIDTH // 2 - 120, 750, 240, 60, "Start Game", COLOR_SUCCESS, text_color=(10,20,10), button_id="setup_start"),
            Button(SCREEN_WIDTH // 2 - 80, 830, 160, 40, "Back", COLOR_PANEL, button_id="setup_back")
        ]
        
        # Set callbacks
        self.cached_buttons['setup'][0].callback = self.start_game
        self.cached_buttons['setup'][1].callback = lambda: setattr(self, 'state', GameState.TITLE)
    
    def init_game_over_buttons(self):
        """Initialize game over screen buttons"""
        self.cached_buttons['game_over'] = [
            Button(SCREEN_WIDTH//2 - 220, 680, 200, 60, "Play Again", COLOR_SUCCESS, text_color=(10,30,10)),
            Button(SCREEN_WIDTH//2 + 20, 680, 200, 60, "Menu", COLOR_PANEL)
        ]
        
        # Set callbacks
        self.cached_buttons['game_over'][0].callback = lambda: setattr(self, 'state', GameState.SETUP)
        self.cached_buttons['game_over'][1].callback = lambda: setattr(self, 'state', GameState.TITLE)
    
    def init_playing_buttons(self):
        """Initialize playing screen buttons (called when entering playing state)"""
        if self.cached_buttons['playing']:
            return  # Already initialized
            
        header_height = 80
        action_panel_w = 400
        sidebar_w = 350
        view_rect = pygame.Rect(sidebar_w + (SCREEN_WIDTH - sidebar_w - action_panel_w) + 10, 
                              header_height + 10, 
                              action_panel_w - 20, 
                              SCREEN_HEIGHT - header_height - 20)
        
        # Create buttons for playing screen
        self.cached_buttons['playing'] = []
        button_id = 0
        
        # Next Month button (always visible)
        next_btn = Button(SCREEN_WIDTH - 220, 15, 200, 50, "Next Month ⏭", COLOR_SUCCESS, text_color=(10,30,10), button_id="next_month")
        next_btn.callback = self.next_month
        self.cached_buttons['playing'].append(next_btn)
        
        # Note: The action sidebar buttons are created dynamically in update_playing_buttons()
        # because they need to be updated based on game state
        
    def update_playing_buttons(self):
        """Update playing screen buttons based on current game state"""
        # Remove old dynamic buttons
        self.cached_buttons['playing'] = [btn for btn in self.cached_buttons['playing'] if btn.button_id == "next_month"]
        
        # Create action buttons based on current state
        self.create_action_buttons()
        self.need_button_update = False
    
    def create_action_buttons(self):
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
        
        # Start positions
        ay = 10
        
        # 1. Financial Actions
        fin_actions = [
            ("Invest $1k", lambda: self.invest_money(1000), self.money >= 1000, COLOR_PANEL, "invest_1k"),
            ("Invest $5k", lambda: self.invest_money(5000), self.money >= 5000, COLOR_PANEL, "invest_5k"),
            ("Withdraw $1k", lambda: self.withdraw_investment(1000), self.investments >= 1000, COLOR_PANEL, "withdraw_1k"),
            ("Withdraw All", lambda: self.withdraw_investment(self.investments), self.investments > 0, COLOR_PANEL, "withdraw_all"),
            ("Save $100", lambda: self.add_to_emergency_fund(100), self.money >= 100, COLOR_PANEL, "save_100"),
            ("Pay Debt $1k", lambda: self.pay_off_debt(1000), self.money >= 1000 and self.debt > 0, COLOR_PANEL, "pay_debt_1k"),
        ]
        
        ay = self.create_section_buttons("MANAGE FINANCES", fin_actions, ay, btn_w, btn_h, view_rect)
        
        # 2. Lifestyle (only if happiness is low)
        if self.happiness < 80:
            lifestyle_actions = []
            for k, c in self.life_choices.items():
                if c.choice_type == 'leisure':
                    lifestyle_actions.append((f"{c.name}\n${c.cost}", 
                                            lambda k=k: self.take_life_choice(k), 
                                            self.money >= c.cost, 
                                            COLOR_PANEL, 
                                            f"leisure_{k}"))
            
            if lifestyle_actions:
                ay = self.create_section_buttons("LIFESTYLE", lifestyle_actions, ay, btn_w, btn_h, view_rect)
        
        # 3. Risky (only show if stress is low or money is high)
        if self.stress < 60 or self.money > 5000:
            risk_actions = []
            for k, c in self.life_choices.items():
                if c.choice_type == 'risky':
                    risk_actions.append((f"{c.name}\n${c.cost}", 
                                        lambda k=k: self.take_life_choice(k), 
                                        self.money >= c.cost, 
                                        COLOR_PANEL_HOVER, 
                                        f"risky_{k}"))
            
            if risk_actions:
                ay = self.create_section_buttons("RISK & VICE", risk_actions, ay, btn_w, btn_h, view_rect)
        
        # 4. Utility/Education
        util_actions = []
        for k, c in self.life_choices.items():
            if c.choice_type in ['utility', 'education']:
                enabled = self.money >= c.cost
                if k == 'vehicle' and self.has_vehicle: enabled = False
                if k == 'university' and self.has_university: enabled = False
                if k == 'masters' and (self.has_masters or not self.has_university): enabled = False
                
                col = COLOR_PRIMARY if c.choice_type == 'education' else COLOR_PANEL
                util_actions.append((f"{c.name}\n${c.cost}", 
                                   lambda k=k: self.take_life_choice(k), 
                                   enabled, 
                                   col, 
                                   f"util_{k}"))
        
        if util_actions:
            ay = self.create_section_buttons("GROWTH & ASSETS", util_actions, ay, btn_w, btn_h, view_rect)
        
        # 5. Health (only if debuffs exist)
        if self.debuffs:
            health_actions = []
            if 'addict' in self.debuffs:
                health_actions.append(("Rehab ($1.5k)", 
                                      lambda: self.treat_addiction(), 
                                      self.money>=1500, 
                                      COLOR_DANGER, 
                                      "rehab"))
            if 'unhappy' in self.debuffs or 'distracted' in self.debuffs:
                health_actions.append(("Therapy ($800)", 
                                      lambda: self.seek_therapy(), 
                                      self.money>=800, 
                                      COLOR_DANGER, 
                                      "therapy"))
            
            if health_actions:
                self.create_section_buttons("HEALTH", health_actions, ay, btn_w, btn_h, view_rect)
    
    def create_section_buttons(self, title, buttons_data, start_y, btn_w, btn_h, view_rect):
        """Create buttons for a section and return new y position"""
        # Add title (just for spacing)
        ay = start_y + 40
        
        # Create buttons in grid
        for i, b_data in enumerate(buttons_data):
            label, callback, enabled, color, btn_id = b_data
            
            bx_rel = 0 if i % 2 == 0 else btn_w + 10
            by_rel = ay + (i // 2) * (btn_h + 10)
            
            # Absolute screen coordinates
            screen_x = view_rect.x + bx_rel
            screen_y = view_rect.y + by_rel - self.scroll_offset
            
            # Store original position for scrolling
            original_y = view_rect.y + by_rel
            
            btn = Button(screen_x, screen_y, btn_w, btn_h, label, color, button_id=btn_id)
            btn.original_y = original_y
            btn.enabled = enabled
            btn.callback = callback
            btn.visible = True
            
            self.cached_buttons['playing'].append(btn)
        
        # Calculate new y position
        rows = (len(buttons_data) + 1) // 2
        return ay + rows * (btn_h + 10) + 20
    
    def update_button_positions(self):
        """Update button positions based on scroll offset"""
        if not self.cached_buttons['playing']:
            return
            
        header_height = 80
        action_panel_w = 400
        sidebar_w = 350
        main_area_w = SCREEN_WIDTH - sidebar_w - action_panel_w
        view_rect = pygame.Rect(sidebar_w + main_area_w + 10, 
                              header_height + 10, 
                              action_panel_w - 20, 
                              SCREEN_HEIGHT - header_height - 20)
        
        for btn in self.cached_buttons['playing']:
            if btn.button_id != "next_month":  # Skip the fixed next month button
                # Calculate new position based on scroll
                new_y = btn.original_y - self.scroll_offset
                btn.rect.y = new_y
                
                # Check visibility
                btn.visible = (new_y + btn.rect.height > view_rect.y and 
                             new_y < view_rect.bottom)
    
    def load_high_score(self):
        try:
            if os.path.exists('highscore.json'):
                with open('highscore.json', 'r') as f:
                    data = json.load(f)
                    return data.get('high_score', 0)
        except:
            pass
        return 0
    
    def save_high_score(self):
        try:
            with open('highscore.json', 'w') as f:
                json.dump({'high_score': self.high_score}, f)
        except:
            pass
    
    def start_game(self):
        if not all([self.selected_class, self.selected_education, self.selected_difficulty]):
            return
            
        class_config = self.class_configs[self.selected_class]
        edu_config = self.education_configs[self.selected_education]
        
        self.money = class_config.starting_money
        self.monthly_income = edu_config.income  # Now using education's income
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
        
        # Reset goals state
        self.goals['netWorth']['completed'] = False
        self.goals['emergencyFund']['completed'] = False
        self.goals['debtFree']['completed'] = False
        self.goals['happiness']['completed'] = False
        
        # Initialize playing buttons
        self.init_playing_buttons()
        self.need_button_update = True
        self.state = GameState.PLAYING
    
    def tut_prev(self):
        if self.tutorial_step > 0:
            self.tutorial_step -= 1
    
    def tut_next(self):
        if self.tutorial_step < 3:
            self.tutorial_step += 1
        else:
            self.state = GameState.SETUP
            self.tutorial_step = 0
    
    def tut_skip(self):
        self.state = GameState.SETUP
        self.tutorial_step = 0
    
    def next_month(self):
        if self.current_month >= MONTHS_PER_GAME:
            self.end_game(True)
            return
        
        messages = []
        
        # Income
        if self.months_no_income == 0:
            income = self.monthly_income
            
            if 'distracted' in self.debuffs:
                income *= 0.8
                messages.append("Distracted: -20% income")
                
                if random.random() < 0.1:
                    self.months_no_income = 2
                    messages.append("Fired due to performance!")
                    self.stress += 30
            
            self.money += income
        else:
            self.months_no_income -= 1
            messages.append(f"No income ({self.months_no_income} months left)")
        
        # Expenses
        total_expenses = self.rent + self.groceries + self.transport
        self.money -= total_expenses
        
        # Debt interest
        if self.debt > 0:
            self.debt *= 1.00417
        
        # Investment returns
        if self.investments > 0:
            difficulty = self.difficulty_configs[self.selected_difficulty]
            monthly_return = (random.random() * 0.25 - 0.10) / 12 * difficulty.market_volatility
            self.investments *= (1 + monthly_return)
        
        # Emergency fund interest
        if self.emergency_fund > 0:
            self.emergency_fund *= 1.00167
        
        # Stress and happiness
        self.stress = max(0, self.stress - 2)
        
        debt_to_income = self.debt / (self.monthly_income * 12) if self.monthly_income > 0 else 0
        if debt_to_income > 0.5:
            self.stress += 5
        
        if self.emergency_fund < self.monthly_income * 3:
            self.stress += 2
        
        self.happiness = max(0, self.happiness - 3)
        
        if 'unhappy' in self.debuffs:
            messages.append("You are unhappy!")
        
        # Random events
        difficulty = self.difficulty_configs[self.selected_difficulty]
        if random.random() < difficulty.emergency_chance:
            event = random.choice(self.emergency_events)
            self.trigger_event(event)
        
        # Random debuff
        debuff_chance = 0.5 - (self.happiness / 100) * 0.4
        if random.random() < debuff_chance and 'distracted' not in self.debuffs:
            self.debuffs.append('distracted')
            messages.append("You feel distracted")
            self.stress += 10
        
        # Burnout check
        if self.stress >= BURNOUT_STRESS or self.happiness <= BURNOUT_HAPPINESS:
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
        
        self.stress = min(100, self.stress)
        self.happiness = min(100, self.happiness)
        self.current_month += 1
        
        if messages:
            self.game_message = " | ".join(messages)
        else:
            self.game_message = f"Month {self.current_month} complete."
        
        self.check_goals()
        
        # Mark that buttons need update
        self.need_button_update = True
        
        # Check game over
        if self.money < -10000:
            self.end_game(False, "Bankrupt! Debt exceeded $10,000 limit.")
    
    def trigger_event(self, event):
        self.current_event = event
        self.show_event_modal = True
    
    def handle_event_close(self):
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
    
    def take_life_choice(self, choice_key):
        choice = self.life_choices[choice_key]
        
        if choice.one_time and self.has_vehicle and choice_key == 'vehicle':
            self.game_message = "You already own a vehicle!"
            return
        
        # Check education prerequisites
        if choice_key == 'university':
            if self.has_university:
                self.game_message = "You already have a degree!"
                return
        
        if choice_key == 'masters':
            if self.has_masters:
                self.game_message = "Already have a master's!"
                return
            if not self.has_university:
                self.game_message = "Need University degree first!"
                return
        
        if self.money < choice.cost:
            self.game_message = "Not enough money!"
            return
        
        self.money -= choice.cost
        
        # Handle education upgrades
        if choice.choice_type == 'education':
            if choice_key == 'university':
                self.monthly_income += 1500
                self.has_university = True
                self.current_education_level = 'university'
                self.debt += choice.cost
                self.money += choice.cost
                self.happiness = min(100, self.happiness + 10)
                self.stress = min(100, self.stress + 15)
                self.game_message = f"Degree Earned! Income +$1500/mo (Added to debt)"
                self.need_button_update = True
                return
            elif choice_key == 'masters':
                self.monthly_income += 1000
                self.has_masters = True
                self.current_education_level = 'masters'
                self.debt += choice.cost
                self.money += choice.cost
                self.happiness = min(100, self.happiness + 15)
                self.stress = min(100, self.stress + 20)
                self.game_message = f"Masters Earned! Income +$1000/mo (Added to debt)"
                self.need_button_update = True
                return
        
        self.happiness = min(100, self.happiness + choice.happiness)
        self.stress = max(0, self.stress + choice.stress)
        
        # Handle risky choices
        if choice.choice_type == 'risky':
            if choice_key == 'gambling' and random.random() < choice.win_chance:
                self.money += choice.win_amount
                self.game_message = f"You won ${choice.win_amount:.0f}!"
                self.need_button_update = True
                return
            
            if choice.debuff_chance > 0 and random.random() < choice.debuff_chance:
                if choice.debuff not in self.debuffs:
                    self.debuffs.append(choice.debuff)
                    self.game_message = f"Addicted to {choice.name}!"
                    self.need_button_update = True
                    return
        
        if choice_key == 'vehicle':
            self.has_vehicle = True
            self.need_button_update = True
        
        self.game_message = f"{choice.name}: Happiness +{choice.happiness:.0f}"
        self.need_button_update = True
    
    def invest_money(self, amount):
        if self.money >= amount:
            self.money -= amount
            self.investments += amount
            self.game_message = f"Invested ${amount:.0f}"
            self.need_button_update = True
    
    def withdraw_investment(self, amount):
        withdrawal = min(amount, self.investments)
        if withdrawal > 0:
            self.investments -= withdrawal
            self.money += withdrawal
            self.game_message = f"Withdrew ${withdrawal:.0f}"
            self.need_button_update = True
        else:
            self.game_message = "No investments!"
    
    def add_to_emergency_fund(self, amount):
        max_contribution = min(100, amount)
        if self.money >= max_contribution:
            self.money -= max_contribution
            self.emergency_fund += max_contribution
            self.game_message = f"Saved ${max_contribution:.0f}"
            self.need_button_update = True
    
    def pay_off_debt(self, amount):
        payment = min(amount, self.debt, self.money)
        if payment > 0:
            self.money -= payment
            self.debt -= payment
            self.stress = max(0, self.stress - 5)
            self.game_message = f"Paid ${payment:.0f} debt"
            self.need_button_update = True
    
    def treat_addiction(self):
        cost = 1500
        if self.money < cost:
            self.game_message = "Need $1500 for treatment"
            return
        
        success_chance = self.happiness / 100
        self.money -= cost
        
        if random.random() < success_chance:
            self.debuffs = [d for d in self.debuffs if d != 'addict']
            self.happiness = min(100, self.happiness + 10)
            self.game_message = "Addiction cured!"
        else:
            self.game_message = "Treatment failed. Need higher happiness."
        
        self.need_button_update = True
    
    def seek_therapy(self):
        cost = 800
        if self.money < cost:
            self.game_message = "Need $800 for therapy"
            return
        
        self.money -= cost
        self.debuffs = [d for d in self.debuffs if d not in ['unhappy', 'distracted']]
        self.stress = max(0, self.stress - 20)
        self.happiness = min(100, self.happiness + 15)
        self.game_message = "Therapy successful!"
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
    
    def calculate_score(self):
        net_worth = self.money + self.investments + self.emergency_fund - self.debt
        goal_bonus = sum(1 for g in self.goals.values() if g['completed']) * 5000
        happiness_bonus = self.happiness * 100
        month_bonus = self.current_month * 500
        
        return max(0, int(net_worth + goal_bonus + happiness_bonus + month_bonus))
    
    def end_game(self, completed, reason=''):
        score = self.calculate_score()
        
        if score > self.high_score:
            self.high_score = score
            self.save_high_score()
        
        self.game_message = reason or ('Game completed!' if completed else 'Game over!')
        self.state = GameState.GAME_OVER
    
    def draw_text(self, text, font, color, x, y, center=False, shadow=False):
        if shadow:
            shadow_surf = font.render(text, True, (0, 0, 0))
            if center:
                shadow_rect = shadow_surf.get_rect(center=(x + 2, y + 2))
            else:
                shadow_rect = shadow_surf.get_rect(topleft=(x + 2, y + 2))
            self.screen.blit(shadow_surf, shadow_rect)

        text_surface = font.render(text, True, color)
        if center:
            text_rect = text_surface.get_rect(center=(x, y))
        else:
            text_rect = text_surface.get_rect(topleft=(x, y))
        self.screen.blit(text_surface, text_rect)
    
    def draw_progress_bar(self, x, y, width, height, percentage, color, bg_color=COLOR_PANEL):
        # Background
        pygame.draw.rect(self.screen, bg_color, (x, y, width, height), border_radius=height//2)
        # Fill
        fill_width = int(width * max(0, min(100, percentage)) / 100)
        if fill_width > 0:
            pygame.draw.rect(self.screen, color, (x, y, fill_width, height), border_radius=height//2)
        # Border
        pygame.draw.rect(self.screen, COLOR_BORDER, (x, y, width, height), 1, border_radius=height//2)
    
    def run(self):
        running = True
        
        while running:
            # Event processing
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    running = False
                
                # Handle scrolling
                if self.state == GameState.PLAYING and not self.show_event_modal:
                    if event.type == pygame.MOUSEWHEEL:
                        self.scroll_offset -= event.y * 30
                        self.scroll_offset = max(0, min(self.scroll_offset, 1200))
                        self.update_button_positions()
            
            self.screen.fill(COLOR_BG)
            
            # Draw based on state
            if self.state == GameState.TITLE:
                self.draw_title(events)
            elif self.state == GameState.TUTORIAL:
                self.draw_tutorial(events)
            elif self.state == GameState.SETUP:
                self.draw_setup(events)
            elif self.state == GameState.PLAYING:
                self.draw_playing(events)
            elif self.state == GameState.GAME_OVER:
                self.draw_game_over(events)
            
            if self.show_event_modal:
                self.draw_event_modal(events)
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

    # --- DRAWING FUNCTIONS ---

    def draw_title(self, events):
        # Decorative Background
        pygame.draw.circle(self.screen, (20, 30, 50), (SCREEN_WIDTH//2, SCREEN_HEIGHT//2), 400)
        
        # Title
        title = "FINANCE QUEST"
        self.draw_text(title, self.font_xl, COLOR_PRIMARY, SCREEN_WIDTH // 2, 250, center=True, shadow=True)
        
        subtitle = "Master Your Financial Future"
        self.draw_text(subtitle, self.font_medium, COLOR_TEXT_DIM, SCREEN_WIDTH // 2, 320, center=True)
        
        # High score
        if self.high_score > 0:
            hs_text = f"High Score: {self.high_score:,}"
            pygame.draw.rect(self.screen, COLOR_PANEL, (SCREEN_WIDTH//2 - 150, 380, 300, 50), border_radius=10)
            self.draw_text(hs_text, self.font_medium, COLOR_WARNING, SCREEN_WIDTH // 2, 405, center=True)
        
        # Draw cached buttons
        for btn in self.cached_buttons['title']:
            btn.draw(self.screen, self.font_medium)
        
        # Handle events for cached buttons
        for event in events:
            for btn in self.cached_buttons['title']:
                btn.handle_event(event)

    def draw_tutorial(self, events):
        tutorials = [
            ("Welcome to FinanceQuest!", "Simulate 3 years of financial decisions. Build wealth, maintain well-being, and achieve your goals."),
            ("Core Mechanics", "Every turn is one month. Manage income, expenses, and investments. Watch your Happiness and Stress!"),
            ("Well-Being System", "High Stress causes Burnout. Low Happiness causes Debuffs. Keep a balance to succeed."),
            ("Winning", "Complete the 4 main goals to earn bonus points. Your final score depends on Net Worth and happiness.")
        ]
        
        title, content = tutorials[self.tutorial_step]
        
        # Card
        panel_rect = pygame.Rect(200, 150, SCREEN_WIDTH - 400, 500)
        pygame.draw.rect(self.screen, COLOR_PANEL, panel_rect, border_radius=20)
        pygame.draw.rect(self.screen, COLOR_BORDER, panel_rect, 2, border_radius=20)
        
        # Header
        pygame.draw.rect(self.screen, COLOR_PANEL_HOVER, (200, 150, SCREEN_WIDTH-400, 80), border_top_left_radius=20, border_top_right_radius=20)
        self.draw_text(f"Tutorial {self.tutorial_step + 1}/{len(tutorials)}", self.font_medium, COLOR_ACCENT, SCREEN_WIDTH // 2, 190, center=True)
        
        self.draw_text(title, self.font_large, COLOR_PRIMARY, SCREEN_WIDTH // 2, 280, center=True)
        
        # Wrapped Text
        words = content.split()
        lines = []
        current_line = []
        for word in words:
            current_line.append(word)
            if self.font_medium.size(' '.join(current_line))[0] > panel_rect.width - 100:
                current_line.pop()
                lines.append(' '.join(current_line))
                current_line = [word]
        lines.append(' '.join(current_line))
        
        y = 360
        for line in lines:
            self.draw_text(line, self.font_medium, COLOR_TEXT, SCREEN_WIDTH // 2, y, center=True)
            y += 40
        
        # Update button text for next/prev
        next_text = "Next" if self.tutorial_step < 3 else "Start Setup"
        self.cached_buttons['tutorial'][1].text = next_text
        
        # Enable/disable previous button
        self.cached_buttons['tutorial'][0].enabled = self.tutorial_step > 0
        
        # Draw cached buttons
        for btn in self.cached_buttons['tutorial']:
            btn.draw(self.screen, self.font_small)
        
        # Handle events
        for event in events:
            for btn in self.cached_buttons['tutorial']:
                btn.handle_event(event)

    def draw_setup(self, events):
        self.draw_text("Character Setup", self.font_large, COLOR_PRIMARY, SCREEN_WIDTH // 2, 50, center=True)
        
        # Grid Layout
        cols = 3
        section_width = 380
        gap = 40
        start_x = (SCREEN_WIDTH - (cols * section_width + (cols-1)*gap)) // 2
        
        # --- Class Section ---
        y = 120
        self.draw_text("Social Class", self.font_medium, COLOR_ACCENT, start_x + section_width//2, y, center=True)
        y += 40
        for key, config in self.class_configs.items():
            color = COLOR_PRIMARY if self.selected_class == key else COLOR_PANEL
            text_color = (10,15,30) if self.selected_class == key else COLOR_TEXT
            
            # Social class shows starting money and debt (no income)
            btn = Button(start_x, y, section_width, 100, 
                        f"{config.name}\nStart: ${config.starting_money:,.0f}\nDebt: ${config.debt:,.0f}", 
                        color, text_color, button_id=f"class_{key}")
            btn.draw(self.screen, self.font_small)
            
            # Handle click
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if btn.rect.collidepoint(event.pos):
                        self.selected_class = key
                        break
            
            y += 110

        # --- Education Section ---
        x = start_x + section_width + gap
        y = 120
        self.draw_text("Education", self.font_medium, COLOR_ACCENT, x + section_width//2, y, center=True)
        y += 40
        for key, config in self.education_configs.items():
            color = COLOR_PRIMARY if self.selected_education == key else COLOR_PANEL
            text_color = (10,15,30) if self.selected_education == key else COLOR_TEXT
            
            # Education shows income and cost
            cost_text = "Free" if config.cost == 0 else f"Cost: ${config.cost:,}"
            income_text = f"Income: ${config.income:,.0f}/mo"
            btn = Button(x, y, section_width, 100, 
                        f"{config.name}\n{income_text}\n{cost_text}", 
                        color, text_color, button_id=f"edu_{key}")
            btn.draw(self.screen, self.font_small)
            
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if btn.rect.collidepoint(event.pos):
                        self.selected_education = key
                        break
            y += 110

        # --- Difficulty Section ---
        x = start_x + (section_width + gap) * 2
        y = 120
        self.draw_text("Difficulty", self.font_medium, COLOR_ACCENT, x + section_width//2, y, center=True)
        y += 40
        for key, config in self.difficulty_configs.items():
            color = COLOR_PRIMARY if self.selected_difficulty == key else COLOR_PANEL
            text_color = (10,15,30) if self.selected_difficulty == key else COLOR_TEXT
            
            btn = Button(x, y, section_width, 100, 
                        f"{config.name}\n{config.description}", 
                        color, text_color, button_id=f"diff_{key}")
            btn.draw(self.screen, self.font_small)
            
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if btn.rect.collidepoint(event.pos):
                        self.selected_difficulty = key
                        break
            y += 110

        # Update start button state
        self.cached_buttons['setup'][0].enabled = all([self.selected_class, self.selected_education, self.selected_difficulty])
        
        # Draw cached buttons
        for btn in self.cached_buttons['setup']:
            btn.draw(self.screen, self.font_small if btn.button_id == "setup_back" else self.font_medium)
        
        # Handle events for cached buttons
        for event in events:
            for btn in self.cached_buttons['setup']:
                btn.handle_event(event)

    def draw_playing(self, events):
        # Update buttons if needed
        if self.need_button_update:
            self.update_playing_buttons()
        
        # Update button positions for scrolling
        self.update_button_positions()
        
        # --- TOP HEADER (Global Stats) ---
        header_height = 80
        pygame.draw.rect(self.screen, COLOR_PANEL, (0, 0, SCREEN_WIDTH, header_height))
        pygame.draw.line(self.screen, COLOR_BORDER, (0, header_height), (SCREEN_WIDTH, header_height), 1)
        
        net_worth = self.money + self.investments + self.emergency_fund - self.debt
        
        # Top Stats
        stats_y = 20
        self.draw_text("FINANCE QUEST", self.font_large, COLOR_PRIMARY, 30, 15)
        
        # Stat Widgets in Header
        widgets = [
            ("MONTH", f"{self.current_month}/{MONTHS_PER_GAME}", COLOR_TEXT),
            ("CASH", f"${self.money:,.0f}", COLOR_SUCCESS if self.money > 0 else COLOR_DANGER),
            ("NET WORTH", f"${net_worth:,.0f}", COLOR_PRIMARY if net_worth > 0 else COLOR_WARNING),
        ]
        
        wx = 450
        for label, val, col in widgets:
            self.draw_text(label, self.font_tiny, COLOR_TEXT_DIM, wx, 15)
            self.draw_text(val, self.font_medium, col, wx, 35)
            wx += 200

        # --- LAYOUT DEFINITIONS ---
        sidebar_w = 350
        action_panel_w = 400
        main_area_w = SCREEN_WIDTH - sidebar_w - action_panel_w
        
        sidebar_rect = pygame.Rect(0, header_height, sidebar_w, SCREEN_HEIGHT - header_height)
        action_rect = pygame.Rect(SCREEN_WIDTH - action_panel_w, header_height, action_panel_w, SCREEN_HEIGHT - header_height)
        main_rect = pygame.Rect(sidebar_w, header_height, main_area_w, SCREEN_HEIGHT - header_height)

        # --- LEFT SIDEBAR (Detailed Stats) ---
        pygame.draw.rect(self.screen, (12, 20, 35), sidebar_rect)
        pygame.draw.line(self.screen, COLOR_BORDER, (sidebar_w, header_height), (sidebar_w, SCREEN_HEIGHT))
        
        sy = header_height + 20
        padding = 30
        
        # Happiness & Stress
        self.draw_text("WELL-BEING", self.font_small, COLOR_TEXT_DIM, padding, sy)
        sy += 30
        self.draw_text(f"Happiness: {self.happiness:.0f}%", self.font_small, COLOR_TEXT, padding, sy)
        self.draw_progress_bar(padding, sy+25, sidebar_w - 60, 10, self.happiness, COLOR_SUCCESS)
        sy += 50
        self.draw_text(f"Stress: {self.stress:.0f}%", self.font_small, COLOR_TEXT, padding, sy)
        self.draw_progress_bar(padding, sy+25, sidebar_w - 60, 10, self.stress, COLOR_DANGER)
        
        sy += 60
        pygame.draw.line(self.screen, COLOR_PANEL_HOVER, (padding, sy), (sidebar_w - padding, sy))
        sy += 20
        
        # Finances List
        self.draw_text("FINANCES", self.font_small, COLOR_TEXT_DIM, padding, sy)
        sy += 30
        fin_items = [
            ("Income", f"+${self.monthly_income:,.0f}/mo", COLOR_SUCCESS),
            ("Expenses", f"-${(self.rent+self.groceries+self.transport):,.0f}/mo", COLOR_DANGER),
            ("Debt", f"${self.debt:,.0f}", COLOR_DANGER),
            ("Investments", f"${self.investments:,.0f}", COLOR_PRIMARY),
            ("Emergency Fund", f"${self.emergency_fund:,.0f}", COLOR_WARNING),
        ]
        
        for label, val, col in fin_items:
            self.draw_text(label, self.font_small, COLOR_TEXT, padding, sy)
            self.draw_text(val, self.font_small, col, sidebar_w - padding - 100, sy)
            sy += 30
            
        sy += 20
        pygame.draw.line(self.screen, COLOR_PANEL_HOVER, (padding, sy), (sidebar_w - padding, sy))
        sy += 20
        
        # Education & Status
        self.draw_text("STATUS", self.font_small, COLOR_TEXT_DIM, padding, sy)
        sy += 30
        edu_name = self.education_configs[self.current_education_level].name
        self.draw_text("Education:", self.font_small, COLOR_TEXT, padding, sy)
        self.draw_text(edu_name, self.font_small, COLOR_ACCENT, padding + 100, sy)
        
        if self.debuffs:
            sy += 40
            self.draw_text("Active Effects:", self.font_small, COLOR_DANGER, padding, sy)
            sy += 25
            for d in self.debuffs:
                pygame.draw.rect(self.screen, COLOR_DANGER, (padding, sy, 120, 24), border_radius=4)
                self.draw_text(d.upper(), self.font_tiny, (50,0,0), padding + 10, sy + 4)
                sy += 30

        # --- CENTER MAIN AREA ---
        # Goal Cards
        mx = main_rect.x + 20
        my = header_height + 20
        
        self.draw_text("CURRENT GOALS", self.font_small, COLOR_TEXT_DIM, mx, my)
        my += 30
        
        goal_w = (main_area_w - 60) // 2
        goal_h = 70
        
        goal_items = list(self.goals.values())
        for i, goal in enumerate(goal_items):
            gx = mx if i % 2 == 0 else mx + goal_w + 20
            gy = my + (i // 2) * (goal_h + 15)
            
            g_color = COLOR_SUCCESS if goal['completed'] else COLOR_PANEL_HOVER
            border = COLOR_SUCCESS if goal['completed'] else COLOR_BORDER
            
            pygame.draw.rect(self.screen, g_color if goal['completed'] else COLOR_PANEL, (gx, gy, goal_w, goal_h), border_radius=10)
            pygame.draw.rect(self.screen, border, (gx, gy, goal_w, goal_h), 2, border_radius=10)
            
            status_icon = "✔" if goal['completed'] else "○"
            self.draw_text(f"{status_icon} {goal['label']}", self.font_small, COLOR_TEXT if not goal['completed'] else (10,30,10), gx + 15, gy + 25)

        # Message Log Area
        msg_y = my + 200
        msg_bg_rect = pygame.Rect(mx, msg_y, main_area_w - 40, 100)
        pygame.draw.rect(self.screen, COLOR_PANEL, msg_bg_rect, border_radius=10)
        pygame.draw.rect(self.screen, COLOR_PRIMARY, msg_bg_rect, 1, border_radius=10)
        
        self.draw_text("EVENT LOG", self.font_tiny, COLOR_PRIMARY, mx + 15, msg_y + 10)
        
        # Center message in box
        lines = self.game_message.split('|')
        ly = msg_y + 35
        for line in lines:
            self.draw_text(line.strip(), self.font_medium, COLOR_TEXT, mx + 15, ly)
            ly += 25

        # --- RIGHT SIDEBAR (Actions) ---
        pygame.draw.rect(self.screen, (20, 28, 45), action_rect)
        pygame.draw.line(self.screen, COLOR_BORDER, (action_rect.x, header_height), (action_rect.x, SCREEN_HEIGHT))
        
        # Draw action buttons
        for btn in self.cached_buttons['playing']:
            btn.draw(self.screen, self.font_tiny)
        
        # Handle events for all playing buttons
        for event in events:
            for btn in self.cached_buttons['playing']:
                btn.handle_event(event)

    def draw_event_modal(self, events):
        # Dim Background
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Modal Box
        w, h = 600, 400
        x, y = (SCREEN_WIDTH - w)//2, (SCREEN_HEIGHT - h)//2
        
        pygame.draw.rect(self.screen, COLOR_BG, (x, y, w, h), border_radius=15)
        pygame.draw.rect(self.screen, COLOR_ACCENT, (x, y, w, h), 2, border_radius=15)
        
        # Title
        self.draw_text(self.current_event.name, self.font_large, COLOR_ACCENT, x + w//2, y + 50, center=True)
        
        # Description
        words = self.current_event.description.split()
        lines = []
        curr = []
        for word in words:
            curr.append(word)
            if self.font_medium.size(' '.join(curr))[0] > w - 60:
                curr.pop()
                lines.append(' '.join(curr))
                curr = [word]
        lines.append(' '.join(curr))
        
        ty = y + 120
        for line in lines:
            self.draw_text(line, self.font_medium, COLOR_TEXT, x + w//2, ty, center=True)
            ty += 35
            
        # Impact
        impact_y = ty + 30
        if self.current_event.cost > 0:
            self.draw_text(f"Cost: -${self.current_event.cost:,.0f}", self.font_medium, COLOR_DANGER, x+w//2, impact_y, center=True)
            impact_y += 30
        if self.current_event.stress_increase > 0:
            self.draw_text(f"Stress: +{self.current_event.stress_increase}%", self.font_medium, COLOR_DANGER, x+w//2, impact_y, center=True)
        
        # Button - FIXED: Create a new button each time and handle its events
        cont_btn = Button(x + w//2 - 100, y + h - 80, 200, 50, "Continue", COLOR_PRIMARY, text_color=(10,20,30))
        cont_btn.callback = self.handle_event_close
        
        # Draw the button
        cont_btn.draw(self.screen, self.font_medium)
        
        # Handle hover
        mouse_pos = pygame.mouse.get_pos()
        cont_btn.hover = cont_btn.rect.collidepoint(mouse_pos)
        
        # Handle clicks directly
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if cont_btn.hover:
                    self.handle_event_close()
                    break

    def draw_game_over(self, events):
        # Background
        pygame.draw.rect(self.screen, COLOR_PANEL, (SCREEN_WIDTH//2 - 400, 100, 800, 700), border_radius=20)
        pygame.draw.rect(self.screen, COLOR_BORDER, (SCREEN_WIDTH//2 - 400, 100, 800, 700), 2, border_radius=20)
        
        title = "NEW HIGH SCORE!" if self.calculate_score() > self.high_score else "GAME OVER"
        col = COLOR_WARNING if self.calculate_score() > self.high_score else COLOR_TEXT
        
        self.draw_text(title, self.font_xl, col, SCREEN_WIDTH//2, 180, center=True, shadow=True)
        
        score = self.calculate_score()
        self.draw_text(f"Final Score: {score:,}", self.font_large, COLOR_PRIMARY, SCREEN_WIDTH//2, 260, center=True)
        
        # Stats Grid
        stats = [
            ("Net Worth", f"${(self.money + self.investments + self.emergency_fund - self.debt):,.0f}"),
            ("Happiness", f"{self.happiness:.0f}%"),
            ("Goals Met", f"{sum(1 for g in self.goals.values() if g['completed'])}/4"),
            ("Months", f"{self.current_month}")
        ]
        
        sy = 350
        for label, val in stats:
            self.draw_text(label, self.font_medium, COLOR_TEXT_DIM, SCREEN_WIDTH//2 - 100, sy)
            self.draw_text(val, self.font_medium, COLOR_TEXT, SCREEN_WIDTH//2 + 100, sy)
            sy += 50
            
        # Message
        if self.game_message:
            self.draw_text(self.game_message, self.font_medium, COLOR_DANGER, SCREEN_WIDTH//2, 600, center=True)
            
        # Draw cached buttons
        for btn in self.cached_buttons['game_over']:
            btn.draw(self.screen, self.font_medium)
        
        # Handle events
        for event in events:
            for btn in self.cached_buttons['game_over']:
                btn.handle_event(event)

if __name__ == "__main__":
    game = FinanceGame()
    game.run()