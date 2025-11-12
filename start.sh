export PATH=$PATH:~/.local/bin
source ./venv/bin/activate

pm2 start "flask run --host=0.0.0.0 --port=5000"
tail -f ~/.pm2/logs/*
sudo services restart postgresql
