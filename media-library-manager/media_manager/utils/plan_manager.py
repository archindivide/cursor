"""Plan manager for saving and loading action plans."""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


class PlanManager:
    """Manage saving and loading of action plans."""
    
    def __init__(self, logger=None):
        """
        Initialize plan manager.
        
        Args:
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def save_duplicate_plan(self, duplicates: Dict[str, List[Path]], organized: Dict[str, Dict], 
                           output_file: Path, source_directory: str) -> bool:
        """
        Save duplicate detection results to a plan file.
        
        Args:
            duplicates: Dictionary mapping hash to list of file paths
            organized: Organized duplicate information with keep/remove decisions
            output_file: Path to output plan file
            source_directory: Source directory that was scanned
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert Path objects to strings for JSON serialization
            plan_data = {
                'version': '1.0',
                'type': 'duplicate_removal',
                'timestamp': datetime.now().isoformat(),
                'source_directory': str(source_directory),
                'duplicates': {},
                'organized': {}
            }
            
            # Save raw duplicates (hash -> list of paths)
            for file_hash, file_paths in duplicates.items():
                plan_data['duplicates'][file_hash] = [str(p) for p in file_paths]
            
            # Save organized duplicates (with keep/remove decisions)
            for file_hash, info in organized.items():
                # Handle case where keep might be None (shouldn't happen, but be safe)
                keep_path = str(info['keep']) if info['keep'] else ''
                plan_data['organized'][file_hash] = {
                    'keep': keep_path,
                    'remove': [str(p) for p in info['remove']],
                    'count': info['count']
                }
            
            # Ensure output directory exists (only if there's a parent directory)
            parent = output_file.parent
            # Only create directory if parent has parts (not current directory)
            if parent and parent.parts:
                try:
                    parent.mkdir(parents=True, exist_ok=True)
                except OSError:
                    # Directory already exists or creation failed, continue anyway
                    pass
            
            # Write JSON file
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(plan_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved duplicate plan to: {output_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving duplicate plan: {e}")
            return False
    
    def load_duplicate_plan(self, plan_file: Path) -> Optional[Dict[str, Any]]:
        """
        Load duplicate detection results from a plan file.
        
        Args:
            plan_file: Path to plan file
        
        Returns:
            Dictionary with plan data or None if error
        """
        try:
            if not plan_file.exists():
                self.logger.error(f"Plan file not found: {plan_file}")
                return None
            
            with open(plan_file, 'r', encoding='utf-8') as f:
                plan_data = json.load(f)
            
            # Validate plan structure
            if plan_data.get('type') != 'duplicate_removal':
                self.logger.error(f"Invalid plan type: {plan_data.get('type')}")
                return None
            
            # Convert string paths back to Path objects
            organized = {}
            for file_hash, info in plan_data.get('organized', {}).items():
                keep_path = Path(info['keep']) if info.get('keep') and info['keep'].strip() else None
                organized[file_hash] = {
                    'keep': keep_path,
                    'remove': [Path(p) for p in info['remove']],
                    'count': info['count']
                }
            
            plan_data['organized'] = organized
            
            self.logger.info(f"Loaded duplicate plan from: {plan_file}")
            self.logger.info(f"Plan created: {plan_data.get('timestamp')}")
            self.logger.info(f"Source directory: {plan_data.get('source_directory')}")
            
            return plan_data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing plan file JSON: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error loading duplicate plan: {e}")
            return None
    
    def save_organization_plan(self, plans: List[Dict], output_file: Path, 
                               source_directory: str, output_directory: str) -> bool:
        """
        Save file organization plans to a file.
        
        Args:
            plans: List of move plans
            output_file: Path to output plan file
            source_directory: Source directory that was scanned
            output_directory: Output directory for organized files
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert Path objects to strings for JSON serialization
            plan_data = {
                'version': '1.0',
                'type': 'file_organization',
                'timestamp': datetime.now().isoformat(),
                'source_directory': str(source_directory),
                'output_directory': str(output_directory),
                'plans': []
            }
            
            for plan in plans:
                plan_entry = {
                    'from': str(plan['from']),
                    'to': str(plan['to']),
                    'media_type': plan.get('media_type', 'unknown'),
                    'changed': plan.get('changed', False),
                    'associated': [
                        {
                            'from': str(a['from']),
                            'to': str(a['to'])
                        }
                        for a in plan.get('associated', [])
                    ]
                }
                plan_data['plans'].append(plan_entry)
            
            # Ensure output directory exists (only if there's a parent directory)
            parent = output_file.parent
            # Only create directory if parent has parts (not current directory)
            if parent and parent.parts:
                try:
                    parent.mkdir(parents=True, exist_ok=True)
                except OSError:
                    # Directory already exists or creation failed, continue anyway
                    pass
            
            # Write JSON file
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(plan_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved organization plan to: {output_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving organization plan: {e}")
            return False
    
    def load_organization_plan(self, plan_file: Path) -> Optional[Dict[str, Any]]:
        """
        Load file organization plans from a plan file.
        
        Args:
            plan_file: Path to plan file
        
        Returns:
            Dictionary with plan data or None if error
        """
        try:
            if not plan_file.exists():
                self.logger.error(f"Plan file not found: {plan_file}")
                return None
            
            with open(plan_file, 'r', encoding='utf-8') as f:
                plan_data = json.load(f)
            
            # Validate plan structure
            if plan_data.get('type') != 'file_organization':
                self.logger.error(f"Invalid plan type: {plan_data.get('type')}")
                return None
            
            # Convert string paths back to Path objects
            plans = []
            for plan_entry in plan_data.get('plans', []):
                plan = {
                    'from': Path(plan_entry['from']),
                    'to': Path(plan_entry['to']),
                    'media_type': plan_entry.get('media_type', 'unknown'),
                    'changed': plan_entry.get('changed', False),
                    'associated': [
                        {
                            'from': Path(a['from']),
                            'to': Path(a['to'])
                        }
                        for a in plan_entry.get('associated', [])
                    ]
                }
                plans.append(plan)
            
            plan_data['plans'] = plans
            plan_data['output_directory'] = Path(plan_data.get('output_directory', '.'))
            
            self.logger.info(f"Loaded organization plan from: {plan_file}")
            self.logger.info(f"Plan created: {plan_data.get('timestamp')}")
            
            return plan_data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing plan file JSON: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error loading organization plan: {e}")
            return None
    
    def get_default_plan_path(self, plan_type: str, base_directory: Optional[Path] = None) -> Path:
        """
        Get default path for a plan file.
        
        Args:
            plan_type: Type of plan ('duplicate_removal', 'file_organization')
            base_directory: Base directory for saving plans (defaults to current directory)
        
        Returns:
            Path to plan file
        """
        if base_directory is None:
            base_directory = Path.cwd()
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if plan_type == 'duplicate_removal':
            filename = f"duplicate_plan_{timestamp}.json"
        elif plan_type == 'file_organization':
            filename = f"organization_plan_{timestamp}.json"
        else:
            filename = f"plan_{timestamp}.json"
        
        return base_directory / filename

