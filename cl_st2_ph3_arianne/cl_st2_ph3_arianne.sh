#!/bin/bash

# Usage:
# Verify Permissions: chmod +x cl_st2_ph3_arianne.sh
# Launch the background process: nohup bash cl_st2_ph3_arianne.sh > process_output.log 2>&1 &
# Monitor Progress:
#  Check the specific file processing log: tail -f ipcc_text_denoising.log
#  Check for any system/bash errors: tail -f process_output.log

ipcc_text_denoising() {
  source "$HOME"/my_env/bin/activate
  if [ -z "$VIRTUAL_ENV" ]; then
      echo "Error: Virtual environment not activated!"
      exit 1
  fi
  python ipcc_text_denoising.py
}

stop_instance() {
  # Do not forget to:
  # - have 'aws-cli' installed on the EC2 instance
  # - have the IAM role 'S3-Admin-Access' attached to the EC2 instance

  instance_id=$(aws ec2 describe-instances --filters "Name=private-dns-name,Values=$(hostname --fqdn)" --query "Reservations[*].Instances[*].InstanceId" --output text)
  aws ec2 stop-instances --instance-ids "$instance_id"
  echo "Instance $instance_id stopped."
}

ipcc_text_denoising
stop_instance
