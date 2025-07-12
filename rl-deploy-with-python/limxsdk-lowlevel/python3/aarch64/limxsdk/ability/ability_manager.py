"""Ability Manager base class module"""
import logging
from functools import partial
import limxsdk.datatypes as datatypes
import limxsdk.robot.Robot as Robot
import limxsdk.robot.RobotType as RobotType
from typing import Dict, Any
from .registry import get_ability_class

class AbilityManager:
    """Abstract base class for managing abilities"""
    
    def __init__(self, name: str = "ability_manager"):
        self.name = name
        self.robot = None
        self.imu_data = None
        self.robot_state = None
        self.logger = logging.getLogger(f"Ability.{name}")
        
        # Create partial functions for callbacks
        self.partial_imu_data_callback = partial(self.imu_data_callback)
        self.partial_robot_state_callback = partial(self.robot_state_callback)
        
        self.abilities = {}  # Loaded abilities {ability_name: ability_instance}
    
    def load_ability(self, name: str, ability_type: str, config: dict) -> bool:
        """Load and initialize an ability"""
        ability_class = get_ability_class(ability_type)
        if not ability_class:
            self.logger.error(f"Unknown ability type: {ability_type}")
            return False
            
        ability = ability_class(name, ability_type, self)
        
        if ability.initialize(config):
            self.abilities[name] = ability
            self.logger.info(f"Ability loaded: {name} ({ability_type})")
            self.robot.publishDiagnostic(f"ability/{name}", "load", 0, 0)
            return True
        else:
            self.logger.error(f"Failed to initialize ability: {name}")
            self.robot.publishDiagnostic(f"ability/{name}", "load", -1, 2, f"Failed to initialize ability: {name}")
            return False
    
    def start_ability(self, name: str) -> bool:
        """Start a loaded ability"""
        if name not in self.abilities:
            self.logger.error(f"Ability not loaded: {name}")
            self.robot.publishDiagnostic(f"ability/{name}", "start", -1, 2, f"Ability not loaded: {name}")
            return False
            
        self.abilities[name].start()
        return True
    
    def stop_ability(self, name: str) -> bool:
        """Stop a running ability"""
        if name not in self.abilities:
            self.logger.error(f"Ability not loaded: {name}")
            self.robot.publishDiagnostic(f"ability/{name}", "stop", -1, 2, f"Ability not loaded: {name}")
            return False
            
        self.abilities[name].stop()
        return True
    
    def start_all_abilities(self) -> None:
        """Start all loaded abilities"""
        for name in self.abilities:
            self.start_ability(name)
    
    def stop_all_abilities(self) -> None:
        """Stop all running abilities"""
        for name in list(self.abilities.keys()):
            self.stop_ability(name)
        
    def init(self, robot_ip: str, robot_type: str) -> bool:
        """Initialize the ability manager and configure the connected robot."""
    
        # Map robot type string to RobotType enum
        try:
            robot_type_map = {
                "Humanoid": RobotType.Humanoid,
                "PointFoot": RobotType.PointFoot,
                "Wheellegged": RobotType.Wheellegged
            }
            robot_enum = robot_type_map[robot_type]
            self.robot = Robot(robot_enum)
        except KeyError:
            self.logger.error(f"Unsupported robot type: {robot_type}. "
                              f"Supported types: {list(robot_type_map.keys())}")
            return False
        
        # Initialize robot connection
        try:
            if not self.robot.init(robot_ip):
                self.logger.error(f"Failed to connect to robot at {robot_ip}. "
                                f"Check network configuration and robot status.")
                return False
        except Exception as e:
            self.logger.error(f"Robot initialization error: {str(e)}")
            return False
        
        # Create partial functions for sensor data callbacks
        self.robot.subscribeImuData(self.partial_imu_data_callback)
        self.robot.subscribeRobotState(self.partial_robot_state_callback)
        
        self.logger.info(f"Successfully established connection with {robot_type} robot at {robot_ip}")
        return True
    
    def imu_data_callback(self, imu: datatypes.ImuData):
        """Callback for IMU sensor data updates"""
        self.imu_data = imu
    
    def robot_state_callback(self, robot_state: datatypes.RobotState):
        """Callback for robot state updates"""
        self.robot_state = robot_state
