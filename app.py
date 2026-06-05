from omegaconf import DictConfig, OmegaConf 
import hydra
from flask import Flask,  render_template, request, Response
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from OpenFAIR import MessageCache, MetricsLogger, KafkaMessageConsumer, ContainerManager
import logging
import time
import requests
import json


DASHBOARD_NAME = "DASH"

init_config = None

###
## Configure Werkzeug logger to filter out vehicle-status requests
## These are too many and clutter the logs
logger = logging.getLogger('werkzeug')
# change the name of the logger:
logger.name = 'DASHBOARD'
original_handle = logger.handle
def custom_handle(record):
    substrings_to_ignore = ['vehicle-status', 'stop-attack', 'start-attack', 'logs']

    for substring in substrings_to_ignore:
        if substring in record.getMessage():
            return

    return original_handle(record)

logger.handle = custom_handle
###

def processing_message(topic, msg):
    """
    Process a Kafka message based on its topic type.

    Args:
        topic (str): The topic from which the message was received.
        msg (dict): The deserialized message data.
    """
    try:
        if topic.endswith("_anomalies"):
            # app.logger.debug(f"ANOMALIES ({topic})")
            msg_cache.add("anomalies", msg)
            msg_cache.add("all", msg)
        elif topic.endswith("_normal_data"):
            # app.logger.debug(f"DIAGNOSTICS ({topic})")
            msg_cache.add("diagnostics", msg)
            msg_cache.add("all", msg)
        elif topic.endswith("_statistics"):
            # app.logger.debug(f"STATISTICS ({topic})")
            metrics_logger.process_stat_message(msg)
        else:
            app.logger.warning(f"Uncategorized message from topic {topic}: {msg}")
    except Exception as e:
        app.logger.error(f"Error processing message from topic {topic}: {e}")


@hydra.main(config_path="config", config_name="default", version_base="1.2")
def create_app(cfg: DictConfig) -> None:
    global app, msg_cache, metrics_logger, init_config

    if cfg.override != "":
        try:
            # Load the variant specified from the command line
            config_overrides = OmegaConf.load(hydra.utils.get_original_cwd() + f'/config/overrides/{cfg.override}.yaml')
            # Merge configurations, with the variant overriding the base config
            cfg = OmegaConf.merge(cfg, config_overrides)
        except Exception as e:
            print('Unsuccesfully tried to use the configuration override: ',cfg.override, " Error: ", e)
            assert False

    init_config = OmegaConf.to_container(cfg, resolve=True)

    msg_cache = MessageCache(cfg.dashboard.message_cache_len)
    metrics_logger = MetricsLogger(cfg)

    # Create a Flask app instance
    # associate processing message routine and logger:
    app = Flask(__name__)
    app.process_message_routine = processing_message
    app.logger.name = DASHBOARD_NAME
    app.logger.setLevel(cfg.logging_level.upper())
    # pretty print the cfg OmegaDict
    app.logger.info(OmegaConf.to_yaml(cfg))

    @app.route('/health', methods=['GET'])
    def health():
        return {"status": "ok"}, 200

    # Create a ConainerManager instance
    container_manager = ContainerManager(cfg)

    # Create a MessageConsumer instance
    message_consumer = KafkaMessageConsumer(parent=app, cfg=cfg)
    message_consumer.start()


    @app.route('/', methods=['GET'])
    def home():
        """
        Render the home page.

        Returns:
            str: The HTML for the home page.
        """

        rendering_params = {
            "botmaster_buttons" : container_manager.vehicle_names
        }
        
        for vehicle_name in container_manager.vehicle_names:
            for vehicle in init_config['vehicles']:
                if list(vehicle.keys())[0] == vehicle_name:
                    rendering_params[vehicle_name] = list(vehicle.values())[0]
        
        return render_template('index.html', rendering_params=rendering_params)
    

    @app.route('/vehicle-status', methods=['POST'])
    def vehicle_status():
        data = request.get_json()
        vehicle_name = data['vehicle_name']
        return container_manager.get_vehicle_status(vehicle_name)


    @app.route('/start-automatic-attacks', methods=['POST'])
    def start_automatic_attacks():
        return container_manager.start_automatic_attacks()
    

    @app.route('/stop-automatic-attacks', methods=['POST'])
    def stop_automatic_attacks():
        return container_manager.stop_automatic_attacks()


    @app.route("/start-attack", methods=["POST"], )
    def start_attack():
        data = request.get_json()
        chosen_vehicle = data['vehicle_name']
        attacking_vehicle = chosen_vehicle.split("_")[0]
        return container_manager.start_attack_from_vehicle(attacking_vehicle, origin="MANUAL")
    

    @app.route("/stop-attack", methods=["POST"])
    def stop_attack():
        data = request.get_json()
        chosen_vehicle = data['vehicle_name']
        origin = data['origin']
        attacking_vehicle = chosen_vehicle.split("_")[0]
        return container_manager.stop_attack_from_vehicle(attacking_vehicle, origin)
    
    @app.route("/reset-noise", methods=["POST"])
    def reset_noise():
        data = request.get_json()
        chosen_vehicle = data['vehicle_name'].split("_")[0]
        Bp_std = data['Bp_std']
        Mp_std = data['Mp_std']

        return container_manager.reset_noise(chosen_vehicle, Bp_std, Mp_std)
    

    @app.route("/start-preconf-attack", methods=["POST"])
    def start_preconf_attack():
        return container_manager.start_preconf_attack()
    

    @app.route("/stop-preconf-attack", methods=["POST"])
    def stop_preconf_attack():
        return container_manager.stop_preconf_attack()

    @app.route("/produce-all", methods=["POST"])
    def produce_all():
        payload = request.get_json(silent=True) or {}
        if "default_vehicle_config" in payload and "vehicles" in payload:
            container_manager.producer_manager.update_vehicle_configs(
                payload["default_vehicle_config"], payload["vehicles"]
            )
        return container_manager.produce_all()


    @app.route("/stop-producing-all", methods=["POST"])
    def stop_produce_all():
        return container_manager.stop_producing_all()


    @app.route("/consume-all", methods=["POST"])
    def consume_all():
        payload = request.get_json(silent=True) or {}
        if "default_consumer_config" in payload and "vehicles" in payload:
            container_manager.consumer_manager.update_consumer_configs(
                payload["default_consumer_config"], payload["vehicles"]
            )
        return container_manager.consume_all()
    

    @app.route("/stop-consuming-all", methods=["POST"])
    def stop_consuming_all():
        return container_manager.stop_consuming_all()


    @app.route('/start-federated-learning', methods=['POST'])
    def start_federated_learning():
        return container_manager.start_federated_learning()
    

    @app.route('/stop-federated-learning', methods=['POST'])
    def stop_federated_learning():
        return container_manager.stop_federated_learning()


    @app.route('/start-wandb', methods=['POST'])
    def start_wandb():
        config_from_frontend = request.get_json(force=True)
        config = OmegaConf.to_container(OmegaConf.merge(init_config, config_from_frontend))
        manager_ip = container_manager.containers_ips['wandber']
        url = f'http://{manager_ip}:5000/command'
        response = requests.post(
                        url, 
                        json={
                            "command": "start_wandb",
                            "params": config
                            }
                    )
        return response.json()
        


    @app.route('/start-security-manager', methods=['POST'])
    def start_security_manager():
        init_sm_config = init_config['security_manager']
        config_from_frontend = request.get_json(force=True)
        frontend_sm_config = config_from_frontend['security_manager']
        sm_config = OmegaConf.to_container(OmegaConf.merge(init_sm_config, frontend_sm_config))
        sm_config['dashboard_endpoint'] = container_manager.containers_ips['dashboard']+":"+str(init_config['dashboard']['port'])
        manager_ip = container_manager.containers_ips['wandber']
        url = f'http://{manager_ip}:5000/command'
        response = requests.post(
                        url, 
                        json={
                            "command": "start_security_manager",
                            "params": sm_config
                            }
                    )
        return response.json()

    @app.route('/stop-security-manager', methods=['POST'])
    def stop_security_manager():
        manager_ip = container_manager.containers_ips['wandber']
        url = f'http://{manager_ip}:5000/command'
        response = requests.post(
                        url, 
                        json={
                            "command": "stop_security_manager",
                            "params": {}
                            }
                    )
        return response.json()


    @app.route('/create-vehicles', methods=['POST'])
    def create_vehicles():
        return container_manager.create_vehicles()
    

    @app.route('/delete-vehicles', methods=['POST'])
    def delete_vehicles():
        return container_manager.delete_vehicles()
    

    @app.route('/stop-wandb', methods=['POST'])
    def stop_wandb():
        manager_ip = container_manager.containers_ips['wandber']
        url = f'http://{manager_ip}:5000/command'
        # wandber now runs wandb.finish() synchronously with up to a 120 s
        # internal timeout, so we need enough headroom here.  150 s gives a
        # 30 s buffer on top of wandber's own limit.
        response = requests.post(
                        url, 
                        json={
                            "command": "stop_wandb",
                            "params": {}
                            },
                        timeout=150
                    )
        return response.json()

    @app.route('/real-all-data')
    def get_all_real_data():
        """
        Render the page displaying the last 100 real messages.

        Returns:
            str: The HTML for the real data visualization page.
        """
        return render_template('realdatavisualization.html', messages=msg_cache.cache["all"])


    @app.route('/start-mitigation', methods=['POST'])
    def start_mitigation():
        manager_ip = container_manager.containers_ips['wandber']
        url = f'http://{manager_ip}:5000/command'
        response = requests.post(
                        url, 
                        json={
                            "command": "start_mitigation",
                            "params": {}
                            }
                    )
        return response.json()
    

    @app.route('/stop-mitigation', methods=['POST'])
    def stop_mitigation():
        manager_ip = container_manager.containers_ips['wandber']
        url = f'http://{manager_ip}:5000/command'
        response = requests.post(
                        url, 
                        json={
                            "command": "stop_mitigation",
                            "params": {}
                            }
                    )
        return response.json()
    

    @app.route('/start-experiment', methods=['POST'])
    def start_experiment():
        logger.info("Starting experiment")
              
        logger.info("\n\nStarting producers...")
        container_manager.produce_all()
        time.sleep(4)
        logger.info("\n\nStarting consumers...")
        container_manager.consume_all()
        time.sleep(5)        
        logger.info("\n\nStarting security manager...")
        container_manager.start_security_manager()
        time.sleep(2)
        logger.info("\n\nStarting federated learning...")
        container_manager.start_federated_learning()
        time.sleep(3)
        logger.info("\n\nStarting wandb...")
        container_manager.start_wandb()
        time.sleep(3)
        logger.info("\n\nStarting automatic attacks...")
        container_manager.start_automatic_attacks()
        
        return "Automatically started the experiment", 200


    @app.route('/shutdown', methods=['POST'])
    def shutdown():
        container_manager.stop_automatic_attacks()
        time.sleep(2)
        container_manager.stop_federated_learning()
        time.sleep(2)
        container_manager.stop_consuming_all()
        time.sleep(2)
        container_manager.stop_producing_all()
        time.sleep(2)
        # stop_wandb() is now fully synchronous on the wandber side — it
        # blocks until wandb.finish() completes (or times out at 120 s).
        # The call itself has a 150 s HTTP timeout so we never get stuck.
        try:
            stop_wandb()
        except Exception as e:
            app.logger.warning(f"stop_wandb failed during shutdown (non-fatal): {e}")
        return 'CAN SHUTDOWN NOW...', 200
    

    @app.route('/logs/<container_name>')
    def logs(container_name):
        try:
            c = container_manager.client.containers.get(container_name)
            if c.status != 'running':
                return f"[ERROR] Container {container_name} is not running\n", 500, {'Content-Type': 'text/plain; charset=utf-8'}        
            since = request.args.get("since", type=float)  # Unix timestamp in millis
            if since:
                output = c.logs(since=since).decode('utf-8', errors='replace')
            else:
                output = c.logs(tail=100).decode('utf-8', errors='replace')
            return output, 200, {'Content-Type': 'text/plain; charset=utf-8'}
        except Exception as e:
            logger.error(f"Error getting logs for container {container_name}: {e}")
            return f"[ERROR] {e}\n", 500, {'Content-Type': 'text/plain; charset=utf-8'}

    # Run the Flask app
    app.run(host=cfg.dashboard.host, port=cfg.dashboard.port)   
    


if __name__ == "__main__":
    create_app()
