# Running HealthAIoT With 1 or 2 Workers

## What Runs Where

- Broker/scheduler: runs `scheduler.py` on your laptop or an EC2 broker instance, listens on port `5002`.
- Worker: runs `worker/app.py` on each EC2 worker instance, listens on port `5000`.
- Scheduler model: the included `vm_selector_model.pth` is trained for exactly two workers using 8 input features: CPU, memory, receive bandwidth, and send bandwidth for worker 1 and worker 2.

## 2-Worker Run

Start `worker/app.py` on both worker machines.

On the broker machine, set both worker public IPs and start the scheduler:

```bash
export HEALTHAIOT_WORKER_IPS="WORKER_1_PUBLIC_IP,WORKER_2_PUBLIC_IP"
python3 scheduler.py
```

PowerShell equivalent:

```powershell
$env:HEALTHAIOT_WORKER_IPS="WORKER_1_PUBLIC_IP,WORKER_2_PUBLIC_IP"
python scheduler.py
```

Open:

```text
http://BROKER_PUBLIC_IP:5002/
```

For local broker testing, use:

```text
http://127.0.0.1:5002/
```

## 1-Worker Run

The scheduler code now supports this with `HEALTHAIOT_WORKER_IPS` containing one IP. In this mode, the broker bypasses the 2-worker scheduler model and routes directly to the single worker, while still recording temporal and worker metric stats.

```bash
export HEALTHAIOT_WORKER_IPS="WORKER_1_PUBLIC_IP"
python3 scheduler.py
```

PowerShell equivalent:

```powershell
$env:HEALTHAIOT_WORKER_IPS="WORKER_1_PUBLIC_IP"
python scheduler.py
```

Use this mode when you want a baseline latency comparison against the 2-worker scheduler system.

## EC2 Worker Setup

1. Launch one or two Ubuntu EC2 instances.
2. Choose an instance type with at least 2 GB RAM. `t3.small` or similar is a reasonable classroom/demo baseline.
3. Create or select a key pair.
4. Configure the worker security group:
   - SSH `22`: allow only your IP.
   - Flask worker `5000`: allow the broker machine IP. For quick testing only, you can temporarily allow your IP.
5. Connect over SSH:

```bash
ssh -i your-key.pem ubuntu@WORKER_PUBLIC_IP
```

6. Install dependencies on each worker:

```bash
sudo apt update
sudo apt install -y python3 python3-pip
pip3 install Flask psutil joblib numpy scikit-learn imbalanced-learn requests
pip3 install torch --index-url https://download.pytorch.org/whl/cpu
```

7. Package files from the project root on your local machine:

```bash
tar -czvf worker.tar.gz worker/app.py worker/best_model.pth worker/scaler.pkl disease_model/__init__.py disease_model/model_utils.py
scp -i your-key.pem worker.tar.gz ubuntu@WORKER_PUBLIC_IP:/home/ubuntu/
```

8. Extract and run on each worker:

```bash
tar -xzvf worker.tar.gz
python3 worker/app.py
```

9. Confirm each worker responds:

```bash
curl http://WORKER_PUBLIC_IP:5000/status
```

## EC2 Broker Setup

If you also run the broker on EC2:

1. Launch a broker Ubuntu EC2 instance.
2. Security group:
   - SSH `22`: allow only your IP.
   - Web app `5002`: allow your IP or your test clients.
   - Outbound traffic: allow the broker to call worker port `5000`.
3. Copy the full repository to the broker, install the conda environment or Python packages, set `HEALTHAIOT_WORKER_IPS`, then run `python3 scheduler.py`.

## Simulation

To generate load after the broker is running, edit `simulation.py`:

```python
BROKER_URL = "http://BROKER_PUBLIC_IP:5002/"
NUM_REQUESTS = 1000
CONCURRENT_THREADS = 20
```

Then run:

```bash
python3 simulation.py
```

After the run, copy or keep the generated JSON files and rerun:

```bash
python results/generate_cloud_scheduler_results.py
```

## Useful AWS References

- EC2 connection options: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/connect.html
- SSH to Linux EC2: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/connect-to-linux-instance.html
- Security groups: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/creating-security-group.html
