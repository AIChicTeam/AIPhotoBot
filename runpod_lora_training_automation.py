#!/usr/bin/env python3
"""
RunPod LoRA Training Automation Script
---------------------------------------

This script automates the process of training a LoRA model on a RunPod GPU instance.
It performs the following steps:

    1. Launch a GPU instance on RunPod via the API.
    2. Upload necessary files (dataset and training script) to the instance.
    3. Start the LoRA training process remotely.
    4. Asynchronously wait for the training process to complete.
    5. Download the trained model back to the local machine.
    6. Clean up remote files (dataset, training script, and model) from the instance.
    7. Shutdown the GPU instance on RunPod.

This script is designed to be stable, well-logged, and modular, so it can be easily
modified, scaled, or integrated into your main project.

Before running, ensure that:
    - You have a valid RunPod API key.
    - The RunPod API URL is correct.
    - All file paths (local and remote) are updated to reflect your environment.
    - SSH credentials (username and SSH key) are correctly configured.
"""

import asyncio
import logging
import subprocess
import sys
import requests

# -------------------------------------------------------------------------
# Configuration Section - Update these parameters for your environment.
# -------------------------------------------------------------------------

# RunPod API endpoint (update if needed)
RUNPOD_API_URL = "https://api.runpod.io"  # Replace with your actual RunPod API endpoint

# API key for authenticating with RunPod.
API_KEY = "YOUR_API_KEY"  # Replace with your RunPod API key

# Instance configuration payload for launching a GPU instance.
# Modify parameters such as 'instance_type' and 'image' as per your requirements.
INSTANCE_PAYLOAD = {
    "instance_type": "GPU",           # e.g., 'GPU'
    "image": "your_docker_image",     # Replace with your Docker image that includes the LoRA training environment
    # Additional parameters can be added here for further customization.
}

# Local file paths (update these paths to point to your actual files)
LOCAL_DATASET_PATH = "/local/path/to/dataset.zip"       # Path to your dataset on the local machine
LOCAL_TRAIN_SCRIPT = "/local/path/to/train_lora.py"       # Path to your LoRA training script

# Remote working directory configuration on the RunPod instance.
REMOTE_WORK_DIR = "/home/ubuntu/lora_training"           # Remote directory where files will be stored
REMOTE_DATASET_PATH = f"{REMOTE_WORK_DIR}/dataset.zip"    # Remote path for the uploaded dataset
REMOTE_TRAIN_SCRIPT = f"{REMOTE_WORK_DIR}/train_lora.py"  # Remote path for the training script
REMOTE_MODEL_PATH = f"{REMOTE_WORK_DIR}/trained_model.lora"  # Remote path where the trained model will be saved

# Local path where the trained model will be saved after downloading.
LOCAL_MODEL_SAVE_PATH = "/local/path/to/trained_model.lora"  # Update with your desired local save path

# SSH configuration for connecting to the RunPod instance (update accordingly)
SSH_USERNAME = "ubuntu"                                 # SSH username on the remote instance
SSH_KEY_PATH = "/path/to/your/ssh_key.pem"              # Path to your SSH private key

# Timing configurations
INSTANCE_READY_WAIT = 30         # Seconds to wait for the instance to become ready
TRAINING_CHECK_INTERVAL = 10     # Seconds between each check of the training process status

# -------------------------------------------------------------------------
# Logging Configuration
# -------------------------------------------------------------------------
# Configure logging to include time, log level, and message details.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)

# -------------------------------------------------------------------------
# RunPod API and Remote Instance Interaction Functions
# -------------------------------------------------------------------------

async def launch_instance():
    """
    Launch a GPU instance on RunPod using the RunPod API.

    Sends a POST request with the INSTANCE_PAYLOAD and expects a response
    containing 'instance_id' and 'instance_ip'. These values are required to
    further interact with the instance.

    Raises:
        Exception: If the API call fails or required data is missing.

    Returns:
        dict: A dictionary containing 'instance_id' and 'instance_ip'.
    """
    logging.info("Launching RunPod instance with GPU...")
    headers = {"Authorization": f"Bearer {API_KEY}"}
    try:
        response = requests.post(f"{RUNPOD_API_URL}/launch", json=INSTANCE_PAYLOAD, headers=headers)
        response.raise_for_status()  # Raise an error if the response status is not OK.
        data = response.json()

        instance_id = data.get("instance_id")
        instance_ip = data.get("instance_ip")
        if not instance_id or not instance_ip:
            raise ValueError("API response missing 'instance_id' or 'instance_ip'. Please check the API response and payload.")

        logging.info(f"Instance launched successfully. ID: {instance_id}, IP: {instance_ip}")
        return {"instance_id": instance_id, "instance_ip": instance_ip}
    except Exception as e:
        logging.error(f"Error launching instance: {e}")
        raise

def upload_files(instance_ip):
    """
    Upload local dataset and training script to the remote RunPod instance using SCP.

    This function:
      1. Creates the remote working directory.
      2. Uploads the dataset file.
      3. Uploads the training script.

    Args:
        instance_ip (str): The IP address of the RunPod instance.

    Raises:
        subprocess.CalledProcessError: If any command (SSH/SCP) fails.
    """
    try:
        logging.info("Creating remote working directory...")
        # Create the remote directory using SSH
        cmd_mkdir = [
            "ssh", "-i", SSH_KEY_PATH,
            f"{SSH_USERNAME}@{instance_ip}",
            f"mkdir -p {REMOTE_WORK_DIR}"
        ]
        subprocess.run(cmd_mkdir, check=True)

        logging.info("Uploading dataset to remote instance...")
        # Upload the dataset using SCP
        cmd_scp_dataset = [
            "scp", "-i", SSH_KEY_PATH,
            LOCAL_DATASET_PATH,
            f"{SSH_USERNAME}@{instance_ip}:{REMOTE_DATASET_PATH}"
        ]
        subprocess.run(cmd_scp_dataset, check=True)

        logging.info("Uploading training script to remote instance...")
        # Upload the training script using SCP
        cmd_scp_script = [
            "scp", "-i", SSH_KEY_PATH,
            LOCAL_TRAIN_SCRIPT,
            f"{SSH_USERNAME}@{instance_ip}:{REMOTE_TRAIN_SCRIPT}"
        ]
        subprocess.run(cmd_scp_script, check=True)

        logging.info("Files uploaded successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error uploading files: {e}")
        raise

def run_training(instance_ip):
    """
    Start the LoRA training process on the remote RunPod instance via SSH.

    Constructs the command to execute the training script remotely with the necessary
    arguments (dataset path and output model path). The process is initiated asynchronously.

    Args:
        instance_ip (str): The IP address of the remote instance.

    Returns:
        subprocess.Popen: Handle to the training process.
    """
    # Construct the command string. Modify parameters if your training script requires different arguments.
    training_command = f"python {REMOTE_TRAIN_SCRIPT} --dataset {REMOTE_DATASET_PATH} --output {REMOTE_MODEL_PATH}"
    logging.info(f"Starting training process with command: {training_command}")

    # Build the SSH command to execute the training process remotely.
    ssh_cmd = [
        "ssh", "-i", SSH_KEY_PATH,
        f"{SSH_USERNAME}@{instance_ip}",
        training_command
    ]
    
    # Launch the command asynchronously (non-blocking)
    process = subprocess.Popen(ssh_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return process

async def wait_for_training(process):
    """
    Asynchronously monitor the remote training process until it completes.

    Periodically checks the status of the training process. If the process ends with
    a non-zero exit code, logs the error details.

    Args:
        process (subprocess.Popen): The subprocess running the training command.

    Raises:
        Exception: If the training process fails (non-zero exit code).
    """
    logging.info("Waiting for the training process to complete...")
    while True:
        ret = process.poll()  # Check if the process has terminated
        if ret is not None:
            if ret == 0:
                logging.info("Training process completed successfully.")
            else:
                # Retrieve stdout and stderr for detailed error logging
                stdout, stderr = process.communicate()
                logging.error(f"Training process exited with code {ret}.")
                logging.error(f"STDOUT: {stdout.decode('utf-8')}")
                logging.error(f"STDERR: {stderr.decode('utf-8')}")
                raise Exception("Training process failed. Check the logs for details.")
            break
        # Wait for a specified interval before re-checking
        await asyncio.sleep(TRAINING_CHECK_INTERVAL)

def download_model(instance_ip):
    """
    Download the trained LoRA model from the remote instance using SCP.

    Transfers the trained model file from the remote instance (REMOTE_MODEL_PATH)
    to the local machine (LOCAL_MODEL_SAVE_PATH).

    Args:
        instance_ip (str): The IP address of the remote instance.

    Raises:
        subprocess.CalledProcessError: If the SCP command fails.
    """
    try:
        logging.info("Downloading the trained model from remote instance...")
        # Construct the SCP command to download the model
        cmd_scp_model = [
            "scp", "-i", SSH_KEY_PATH,
            f"{SSH_USERNAME}@{instance_ip}:{REMOTE_MODEL_PATH}",
            LOCAL_MODEL_SAVE_PATH
        ]
        subprocess.run(cmd_scp_model, check=True)
        logging.info(f"Model downloaded successfully to: {LOCAL_MODEL_SAVE_PATH}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error downloading model: {e}")
        raise

def cleanup_instance(instance_ip):
    """
    Clean up the remote instance by removing the dataset, training script, and model files.

    Executes an SSH command to delete the specified files from the remote working directory.
    This is important to free up space and maintain security after the training is complete.

    Args:
        instance_ip (str): The IP address of the remote instance.
    """
    cleanup_command = f"rm -f {REMOTE_DATASET_PATH} {REMOTE_TRAIN_SCRIPT} {REMOTE_MODEL_PATH}"
    logging.info("Cleaning up remote instance files...")
    ssh_cmd = [
        "ssh", "-i", SSH_KEY_PATH,
        f"{SSH_USERNAME}@{instance_ip}",
        cleanup_command
    ]
    try:
        subprocess.run(ssh_cmd, check=True)
        logging.info("Remote cleanup completed successfully.")
    except subprocess.CalledProcessError as e:
        logging.warning(f"Cleanup encountered issues: {e}")

def shutdown_instance(instance_id):
    """
    Shutdown the RunPod instance using the RunPod API.

    Sends a POST request to the shutdown endpoint with the instance_id.
    This function should be called regardless of previous errors to avoid unnecessary costs.

    Args:
        instance_id (str): The unique identifier of the instance to be shutdown.
    """
    logging.info(f"Shutting down instance with ID: {instance_id}")
    headers = {"Authorization": f"Bearer {API_KEY}"}
    try:
        response = requests.post(f"{RUNPOD_API_URL}/shutdown/{instance_id}", headers=headers)
        response.raise_for_status()
        logging.info("Instance shutdown successfully.")
    except Exception as e:
        logging.error(f"Error shutting down instance: {e}")

# -------------------------------------------------------------------------
# Main Execution Workflow
# -------------------------------------------------------------------------

async def main():
    """
    Main asynchronous workflow that orchestrates the full process:
    
        1. Launch the RunPod instance.
        2. Wait for the instance to be ready.
        3. Upload necessary files (dataset and training script).
        4. Start the training process.
        5. Monitor the training process until completion.
        6. Download the trained model.
        7. Clean up remote files.
        8. Shutdown the instance.

    This function includes robust error handling to ensure that the instance is shutdown
    even if any part of the process fails.
    """
    instance_data = None
    try:
        # Step 1: Launch RunPod GPU instance.
        instance_data = await launch_instance()
        instance_id = instance_data["instance_id"]
        instance_ip = instance_data["instance_ip"]

        # Step 2: Wait for the instance to be fully ready.
        logging.info(f"Waiting {INSTANCE_READY_WAIT} seconds for instance readiness...")
        await asyncio.sleep(INSTANCE_READY_WAIT)

        # Step 3: Upload local files to the remote instance.
        upload_files(instance_ip)

        # Step 4: Start the remote training process.
        training_process = run_training(instance_ip)

        # Step 5: Asynchronously wait for training to finish.
        await wait_for_training(training_process)

        # Step 6: Download the trained model back to the local machine.
        download_model(instance_ip)

        # Step 7: Clean up files on the remote instance.
        cleanup_instance(instance_ip)

    except Exception as e:
        logging.error(f"An error occurred during the workflow: {e}")
    finally:
        # Step 8: Shutdown the instance to avoid unnecessary charges.
        if instance_data:
            shutdown_instance(instance_data["instance_id"])
        else:
            logging.warning("Instance was not launched; skipping shutdown.")

# -------------------------------------------------------------------------
# Entry Point of the Script
# -------------------------------------------------------------------------
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.warning("Script interrupted by user. Exiting gracefully...")
        sys.exit(0)
