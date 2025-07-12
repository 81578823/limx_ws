import click
import logging
import time
import os
import json
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import urlparse, parse_qs
from .config import load_config, get_config
from .registry import load_ability_from_script
from .ability_manager import AbilityManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Ability")

# Global variable: After the daemon starts, this server provides HTTP interfaces
server = None
# Global ability manager, initialized once within the daemon process
ability_manager = AbilityManager()

# ------------------ HTTP Request Handler ------------------
class AbilityRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler class for processing all incoming HTTP requests"""
    
    # Disable default logging output
    def log_message(self, format, *args):
        return
    
    def _send_response(self, data, status_code=200):
        """Send a JSON response"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def do_GET(self):
        """Handle GET requests"""
        path = urlparse(self.path).path
        
        if path == '/abilities/list':
            self._handle_list_abilities()
        else:
            self._send_response({"error": "Not Found"}, 404)
    
    def do_POST(self):
        """Handle POST requests"""
        path = urlparse(self.path).path
        content_length = int(self.headers['Content-Length']) if 'Content-Length' in self.headers else 0
        post_data = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else ''
        
        if path.startswith('/abilities/') and path.endswith('/start'):
            ability_name = path.split('/')[2]
            self._handle_start_ability(ability_name)
        elif path.startswith('/abilities/') and path.endswith('/stop'):
            ability_name = path.split('/')[2]
            self._handle_stop_ability(ability_name)
        elif path == '/abilities/switch':
            # Parse query parameters
            query = urlparse(self.path).query
            params = parse_qs(query)
            stop_list = params.get('stop', [])
            start_list = params.get('start', [])
            
            # If POST data is in JSON format, try to get parameters from it
            try:
                json_data = json.loads(post_data)
                stop_list = json_data.get('stop', [])
                start_list = json_data.get('start', [])
            except:
                pass
            
            # Handle cases where parameters are lists or strings
            stop_list = stop_list[0].split() if stop_list and isinstance(stop_list[0], str) else stop_list
            start_list = start_list[0].split() if start_list and isinstance(start_list[0], str) else start_list
            
            self._handle_switch_abilities(stop_list, start_list)
        else:
            self._send_response({"error": "Not Found"}, 404)
    
    def _handle_list_abilities(self):
        """Handle requests to get the list of abilities"""
        abilities = []
        for name, ability in ability_manager.abilities.items():
            abilities.append({
                "name": name,
                "running": ability.active
            })
        self._send_response({"abilities": abilities})
    
    def _handle_start_ability(self, ability_name):
        """Handle requests to start an ability"""
        if ability_manager.start_ability(ability_name):
            self._send_response({"status": "success", "message": f"Ability {ability_name} started successfully"})
        else:
            self._send_response({"status": "error", "message": f"Ability {ability_name} does not exist or failed to start"}, 400)
    
    def _handle_stop_ability(self, ability_name):
        """Handle requests to stop an ability"""
        if ability_manager.stop_ability(ability_name):
            self._send_response({"status": "success", "message": f"Ability {ability_name} stopped successfully"})
        else:
            self._send_response({"status": "error", "message": f"Ability {ability_name} does not exist or failed to stop"}, 400)
    
    def _handle_switch_abilities(self, stop_list, start_list):
        """Handle requests to switch abilities"""
        results = []
        
        # Process stop operations first
        for name in stop_list:
            success = ability_manager.stop_ability(name)
            status = "success" if success else "error"
            message = f"Ability {name} stopped successfully" if success else f"Failed to stop ability {name}"
            
            results.append({
                "name": name,
                "action": "stop",
                "status": status,
                "message": message
            })
        
        # Then process start operations
        for name in start_list:
            success = ability_manager.start_ability(name)
            status = "success" if success else "error"
            message = f"Ability {name} started successfully" if success else f"Failed to start ability {name}"
            
            results.append({
                "name": name,
                "action": "start",
                "status": status,
                "message": message
            })
        
        self._send_response({"results": results})

# ------------------ Daemon process related logic ------------------
def start_daemon(config_path):
    """Start the daemon process: load configuration, initialize abilities, and start the HTTP service"""
    # 1. Load configuration
    if not load_config(config_path):
        logger.error("Configuration loading failed, daemon process startup aborted")
        return
      
    # Get directory of config file for relative path resolution
    config_dir = os.path.dirname(os.path.abspath(config_path))

    # 2. Load abilities from configuration
    config = get_config()

    # 3. Initialize the ability manager
    robot_ip = os.getenv("ROBOT_IP", config.get("robot_ip", "127.0.0.1"))
    robot_type = config.get("robot_type", "Humanoid")
    if not ability_manager.init(robot_ip, robot_type):
        logger.error("Ability manager initialization failed, daemon process startup aborted")
        return
      
    for name, params in config.get("abilities", {}).items():
        ability_type = params["type"]
        script_path = params["script_path"]
        ability_config = params.get("config", {})
        
        # Resolve relative path to absolute path based on config file location
        if not os.path.isabs(script_path):
            resolved_path = os.path.join(config_dir, script_path)
            script_path = resolved_path

        try:
            load_ability_from_script(script_path)

            if ability_manager.load_ability(name, ability_type, ability_config):
                logger.info(f"Ability script loaded successfully: {script_path}")
            else:
                logger.error(f"Ability loading failed: {name}")
        except Exception as e:
            logger.error(f"Error loading ability {name}: {str(e)}")
      
        autostart = params.get("autostart", False)
        if autostart:
            if ability_manager.start_ability(name):
                logger.info(f"Automated startup succeeded for ability '{name}' ")
            else:
                logger.error(f"Automated startup failed for ability '{name}' ")

    # 4. Start the HTTP service to provide external interfaces
    global server
    try:
        server = ThreadingHTTPServer(('0.0.0.0', 11558), AbilityRequestHandler)
        server.serve_forever()
    except Exception as e:
        logger.error(f"Failed to start HTTP server: {str(e)}")
    finally:
        # Clean up resources
        if server:
            server.server_close()

# ------------------ Command line interface definitions ------------------
# Custom command group to control the order of commands in help
class OrderedGroup(click.Group):
    def list_commands(self, ctx):
        # Define the order of commands here
        return ['load', 'list', 'start', 'switch', 'stop']
      
@click.group(cls=OrderedGroup)
def cli():
    """Ability Framework Command Line Tool"""
    pass


@cli.command("load")
@click.option('--config', default='config/abilities.yaml', help='Configuration file path')
def daemon(config):
    """Start the daemon process (load abilities, provide HTTP interfaces)"""
    start_daemon(config)


@cli.command("list")
def list_abilities():
    """Query loaded abilities via HTTP interface (daemon must be running)"""
    import urllib.request
    try:
        with urllib.request.urlopen("http://127.0.0.1:11558/abilities/list") as response:
            data = json.loads(response.read().decode('utf-8'))
            click.echo("Loaded abilities:")
            for item in data["abilities"]:
                status = "Running" if item["running"] else "Stopped"
                click.echo(f"- {item['name']} ({status})")
    except urllib.error.URLError as e:
        click.echo(f"Failed to connect to daemon: {str(e)}, please start the daemon first with `python -m limxsdk.ability.cli daemon`")


@cli.command("start")
@click.argument('ability_name')
def start_ability_cli(ability_name):
    """Start an ability via HTTP interface (daemon must be running)"""
    import urllib.request
    try:
        req = urllib.request.Request(f"http://127.0.0.1:11558/abilities/{ability_name}/start", method='POST')
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            click.echo(data.get("message", "Operation failed"))
    except urllib.error.URLError as e:
        click.echo(f"Failed to connect to daemon: {str(e)}, please start the daemon first with `python -m limxsdk.ability.cli daemon`")


@cli.command("stop")
@click.argument('ability_name')
def stop_ability_cli(ability_name):
    """Stop an ability via HTTP interface (daemon must be running)"""
    import urllib.request
    try:
        req = urllib.request.Request(f"http://127.0.0.1:11558/abilities/{ability_name}/stop", method='POST')
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            click.echo(data.get("message", "Operation failed"))
    except urllib.error.URLError as e:
        click.echo(f"Failed to connect to daemon: {str(e)}, please start the daemon first with `python -m limxsdk.ability.cli daemon`")


@cli.command("switch")
@click.argument('stop', required=False)
@click.argument('start', required=False)
def switch_abilities(stop, start):
    """
    Switch abilities: stop specified abilities and start specified abilities via HTTP interface (daemon must be running)
    
    Example:
      python -m limxsdk.ability.cli switch "ability1 ability2" "ability3 ability4"
    """
    import urllib.request
    import urllib.parse
    
    if not stop and not start:
        click.echo("Error: At least one ability to stop or start must be specified")
        return
    
    try:
        # Prepare the request with query parameters
        params = {}
        if stop:
            params["stop"] = stop
        if start:
            params["start"] = start
            
        query_string = urllib.parse.urlencode(params)
        url = f"http://127.0.0.1:11558/abilities/switch?{query_string}"
        
        req = urllib.request.Request(url, method='POST')
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            results = data.get("results", [])
            
            # Group results by action for better display
            stop_results = [r for r in results if r["action"] == "stop"]
            start_results = [r for r in results if r["action"] == "start"]
            
            if stop_results:
                click.echo("\nStopping abilities:")
                for result in stop_results:
                    status = "✓" if result["status"] == "success" else "✗"
                    click.echo(f"  {status} {result['message']}")
            
            if start_results:
                click.echo("\nStarting abilities:")
                for result in start_results:
                    status = "✓" if result["status"] == "success" else "✗"
                    click.echo(f"  {status} {result['message']}")
    except urllib.error.URLError as e:
        click.echo(f"Failed to connect to daemon: {str(e)}, please start the daemon first with `python -m limxsdk.ability.cli daemon`")


if __name__ == '__main__':
    cli()