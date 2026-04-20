"""
Save/Load System
Handles game state persistence using JSON
"""

import json
import os
from datetime import datetime
from typing import Optional, List, Dict
from pathlib import Path

from classes.promotion import Promotion
from classes.wrestler import Wrestler
from classes.enums import Philosophy


class SaveManager:
    """Handles saving and loading game data"""
    
    def __init__(self, save_directory: str = "saves"):
        self.save_directory = save_directory
        self._ensure_save_directory()
    
    def _ensure_save_directory(self):
        """Create save directory if it doesn't exist"""
        Path(self.save_directory).mkdir(parents=True, exist_ok=True)
    
    def _get_save_path(self, save_name: str) -> str:
        """Get full path for a save file"""
        safe_name = "".join(c for c in save_name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '_')
        return os.path.join(self.save_directory, f"{safe_name}.json")
    
    def save_game(self, game_state: dict, save_name: str) -> bool:
        """Save the current game state to a JSON file"""
        try:
            save_path = self._get_save_path(save_name)
            
            game_state["_metadata"] = {
                "save_name": save_name,
                "save_date": datetime.now().isoformat(),
                "version": "0.2.0",
            }
            
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(game_state, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Game saved successfully: {save_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving game: {e}")
            return False
    
    def load_game(self, save_name: str) -> Optional[dict]:
        """Load a game state from a JSON file"""
        try:
            save_path = self._get_save_path(save_name)
            
            if not os.path.exists(save_path):
                print(f"❌ Save file not found: {save_path}")
                return None
            
            with open(save_path, 'r', encoding='utf-8') as f:
                game_state = json.load(f)
            
            print(f"✅ Game loaded successfully: {save_path}")
            return game_state
            
        except json.JSONDecodeError as e:
            print(f"❌ Error reading save file (corrupted?): {e}")
            return None
        except Exception as e:
            print(f"❌ Error loading game: {e}")
            return None
    
    def list_saves(self) -> List[Dict]:
        """List all available save files"""
        saves = []
        
        try:
            if not os.path.exists(self.save_directory):
                return saves
                
            for filename in os.listdir(self.save_directory):
                if filename.endswith('.json'):
                    save_path = os.path.join(self.save_directory, filename)
                    
                    try:
                        with open(save_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        metadata = data.get("_metadata", {})
                        promotion_data = data.get("promotion", {})
                        
                        saves.append({
                            "filename": filename,
                            "save_name": metadata.get("save_name", filename[:-5]),
                            "save_date": metadata.get("save_date", "Unknown"),
                            "promotion_name": promotion_data.get("name", "Unknown"),
                            "philosophy": promotion_data.get("philosophy", "Unknown"),
                            "week": promotion_data.get("current_week", 1),
                            "year": promotion_data.get("current_year", 1),
                        })
                    except Exception:
                        saves.append({
                            "filename": filename,
                            "save_name": filename[:-5],
                            "save_date": "Unknown",
                            "promotion_name": "CORRUPTED",
                            "philosophy": "Unknown",
                        })
        except Exception as e:
            print(f"Error listing saves: {e}")
        
        saves.sort(key=lambda x: x.get("save_date", ""), reverse=True)
        return saves
    
    def delete_save(self, save_name: str) -> bool:
        """Delete a save file"""
        try:
            save_path = self._get_save_path(save_name)
            
            if os.path.exists(save_path):
                os.remove(save_path)
                print(f"✅ Save deleted: {save_name}")
                return True
            else:
                print(f"❌ Save not found: {save_name}")
                return False
                
        except Exception as e:
            print(f"❌ Error deleting save: {e}")
            return False
    
    def save_exists(self, save_name: str) -> bool:
        """Check if a save file exists"""
        save_path = self._get_save_path(save_name)
        return os.path.exists(save_path)


class GameState:
    """
    Manages the complete game state.
    Acts as a container for all game objects.
    """
    
    def __init__(self):
        # Core
        self.promoter_name: str = ""
        self.promotion = None
        
        # Systems
        self.creative_control = None
        self.progression = None
        self.ai_director = None
        self.championship_manager = None
        
        # Data
        self.free_agents: List[Wrestler] = []
        self.rival_promotions: List[dict] = []
        self.game_settings: dict = {}
        
        # Save manager
        self.save_manager = SaveManager()
    
    def to_dict(self) -> dict:
        """Convert entire game state to dictionary"""
        result = {
            "promoter_name": self.promoter_name,
            "promotion": self.promotion.to_dict() if self.promotion else None,
            "free_agents": [w.to_dict() for w in self.free_agents],
            "rival_promotions": self.rival_promotions,
            "game_settings": self.game_settings,
        }
        
        # Save creative control
        if self.creative_control and hasattr(self.creative_control, 'to_dict'):
            result["creative_control"] = self.creative_control.to_dict()
        
        # Save progression
        if self.progression and hasattr(self.progression, 'to_dict'):
            result["progression"] = self.progression.to_dict()
        
        # Save AI director
        if self.ai_director and hasattr(self.ai_director, 'to_dict'):
            result["ai_director"] = self.ai_director.to_dict()
        
        # Save championship manager
        if self.championship_manager and hasattr(self.championship_manager, 'to_dict'):
            result["championship_manager"] = self.championship_manager.to_dict()
        
        return result
    
    def from_dict(self, data: dict):
        """Load game state from dictionary"""
        self.promoter_name = data.get("promoter_name", "")
        
        # Load promotion
        promotion_data = data.get("promotion")
        if promotion_data:
            self.promotion = Promotion.from_dict(promotion_data)
        
        # Load free agents
        self.free_agents = [
            Wrestler.from_dict(w) for w in data.get("free_agents", [])
        ]
        
        # Load basic data
        self.rival_promotions = data.get("rival_promotions", [])
        self.game_settings = data.get("game_settings", {})
        
        # Load progression
        progression_data = data.get("progression")
        if progression_data:
            try:
                from classes.progression import ProgressionSystem
                self.progression = ProgressionSystem.from_dict(progression_data)
            except Exception as e:
                print(f"Warning: Could not load progression: {e}")
                self.progression = None
        
        # Load creative control
        cc_data = data.get("creative_control")
        if cc_data:
            try:
                from systems.creative_control import CreativeControlSystem
                self.creative_control = CreativeControlSystem.from_dict(cc_data)
            except Exception as e:
                print(f"Warning: Could not load creative control: {e}")
                self.creative_control = None
        
        # Load AI director
        ai_data = data.get("ai_director")
        if ai_data:
            try:
                from ai.director import AIDirector
                self.ai_director = AIDirector.from_dict(ai_data)
            except Exception as e:
                print(f"Warning: Could not load AI director: {e}")
                self.ai_director = None
        
        # Load championship manager
        champ_data = data.get("championship_manager")
        if champ_data:
            try:
                from classes.championship import ChampionshipManager
                self.championship_manager = ChampionshipManager.from_dict(champ_data)
            except Exception as e:
                print(f"Warning: Could not load championship manager: {e}")
                self.championship_manager = None
    
    def save(self, save_name: str) -> bool:
        """Save current game state"""
        return self.save_manager.save_game(self.to_dict(), save_name)
    
    def load(self, save_name: str) -> bool:
        """Load game state from save"""
        data = self.save_manager.load_game(save_name)
        if data:
            self.from_dict(data)
            return True
        return False
    
    def list_saves(self) -> List[dict]:
        """List available saves"""
        return self.save_manager.list_saves()
    
    def ensure_all_systems(self):
        """Make sure all game systems are initialized"""
        # Progression
        if not hasattr(self, 'progression') or self.progression is None:
            from classes.progression import ProgressionSystem
            self.progression = ProgressionSystem()
        
        # AI Director
        if not hasattr(self, 'ai_director') or self.ai_director is None:
            from ai.director import AIDirector
            cc_enabled = self.game_settings.get("creative_control_enabled", False)
            cc_difficulty = self.game_settings.get("creative_control_difficulty", "Normal")
            self.ai_director = AIDirector(
                creative_control_enabled=cc_enabled,
                creative_control_difficulty=cc_difficulty,
            )
        
        # Championship Manager
        if not hasattr(self, 'championship_manager') or self.championship_manager is None:
            from classes.championship import ChampionshipManager
            self.championship_manager = ChampionshipManager()
            self.championship_manager.setup_default_accolades()
        
        # Free Agents
        if not hasattr(self, 'free_agents') or not self.free_agents or len(self.free_agents) < 10:
            from data.wrestler_generator import generate_free_agents
            level = self.progression.level if self.progression else 1
            self.free_agents = generate_free_agents(50, level)
