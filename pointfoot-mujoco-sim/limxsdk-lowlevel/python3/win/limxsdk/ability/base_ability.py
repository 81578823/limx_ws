"""Base ability module"""
import logging
import threading
import time
import limxsdk.datatypes as datatypes
import limxsdk.robot.Robot as Robot
from typing import Dict, Any

class BaseAbility:
    """Abstract base class for all abilities"""
    
    def __init__(self, name: str, type: str, manager: "AbilityManager"):
        self.name = name
        self.type = type
        self.manager = manager
        self.active = False
        self.running = False
        self.thread = None
        self.logger = logging.getLogger(f"Ability.{name}")
        self.config = {}
        
        self.logger.info(str(self.manager.name))
        
    def initialize(self, config: dict) -> bool:
        """Initialize the ability with configuration"""
        self.config = config
        self.logger.info(f"Initializing ability: {self.name}")
        return True
      
    def get_imu_data(self) -> datatypes.ImuData:
        return self.manager.imu_data
      
    def get_robot_state(self) -> datatypes.RobotState:
        return self.manager.robot_state
      
    def get_robot_instance(self) -> Robot:
        return self.manager.robot
    
    def start(self) -> None:
        """Start the ability in a separate thread"""
        if self.active:
            self.logger.warning(f"Ability already active: {self.name}")
            return
            
        self.active = True
        self.running = True
        self.thread = threading.Thread(target=self._run, name=f"ability-{self.name}")
        self.thread.daemon = True
        self.thread.start()
        self.logger.info(f"Ability started: {self.name}")
    
    def stop(self) -> None:
        """Stop the ability thread"""
        if not self.active:
            self.logger.warning(f"Ability not active: {self.name}")
            return
            
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        self.active = False
        self.logger.info(f"Ability stopped: {self.name}")
    
    def _run(self) -> None:
        """Main execution loop for the ability thread"""
        try:
            self.manager.robot.publishDiagnostic(f"ability/{self.name}", "start", 0, 0)
            self.on_start()
            self.on_main()
            self.manager.robot.publishDiagnostic(f"ability/{self.name}", "stop", 0, 0)
        except Exception as e:
            self.logger.error(f"Ability failed: {str(e)}")
            self.manager.robot.publishDiagnostic(f"ability/{self.name}", "start", -1, 2, f"Ability failed: {str(e)}")
        finally:
            self.on_stop()
            self.running = False
            self.active = False
    
    def on_start(self) -> None:
        """Called when ability starts (override in subclasses)"""
        pass
    
    def on_stop(self) -> None:
        """Called when ability stops (override in subclasses)"""
        pass
    
    def on_main(self, timestamp: float, dt: float) -> None:
        """Main control loop (must be implemented by subclasses)"""
        raise NotImplementedError("Subclasses must implement on_main() method")