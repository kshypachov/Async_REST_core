#!/bin/bash

# Змінні для конфігурації
REPO_URL="https://github.com/kshypachov/Async_REST_core.git"
PROJECT_DIR="Async_REST_core"
VENV_DIR="venv"
DB_USER="your_db_user"
DB_PASSWORD="your_db_password"
DB_NAME="your_db_name"
DB_HOST="localhost" # Використовується localhost для встановлення MariaDB на цьому сервері
DB_PORT="3306"      # Порт за замовчуванням для MariaDB
SERVICE_NAME="async_rest_trembita"
APP_MODULE="main:app" # Вкажіть правильний модуль додатку

# Встановлення системних залежностей
echo "Встановлення системних залежностей..."
sudo apt-get update
sudo apt-get install -y curl libmariadb-dev gcc python3 python3-venv python3-dev git

# Налаштування репозиторію MariaDB
echo "Налаштування репозиторію MariaDB..."
curl -LsS https://r.mariadb.com/downloads/mariadb_repo_setup | sudo bash

# Встановлення MariaDB сервера
echo "Встановлення MariaDB сервера..."
sudo apt-get install -y mariadb-server

# Запуск та налаштування MariaDB
echo "Запуск та налаштування MariaDB..."
sudo systemctl start mariadb
sudo systemctl enable mariadb

# Створення бази даних та користувача
echo "Створення бази даних та користувача..."
sudo mysql -e "CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
sudo mysql -e "CREATE USER IF NOT EXISTS '$DB_USER'@'%' IDENTIFIED BY '$DB_PASSWORD';"
sudo mysql -e "GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'%';"
sudo mysql -e "FLUSH PRIVILEGES;"

# Клонування репозиторію
echo "Клонування репозиторію..."
git clone $REPO_URL
cd $PROJECT_DIR

# Створення та активація віртуального середовища
echo "Створення та активація віртуального середовища..."
python3 -m venv $VENV_DIR
source $VENV_DIR/bin/activate   # Для Windows: venv\Scripts\activate

# Встановлення залежностей Python
echo "Встановлення залежностей Python..."
pip install --upgrade pip
pip install -r requirements.txt

# Налаштування конфігурації бази даних
echo "Налаштування конфігурації бази даних..."
sed -i "s/^sqlalchemy.url = .*/sqlalchemy.url = mysql+aiomysql:\/\/$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT\/$DB_NAME/" alembic.ini
sed -i "s/^host = .*/host = $DB_HOST/" config.ini
sed -i "s/^port = .*/port = $DB_PORT/" config.ini
sed -i "s/^name = .*/name = $DB_NAME/" config.ini
sed -i "s/^username = .*/username = $DB_USER/" config.ini
sed -i "s/^password = .*/password = $DB_PASSWORD/" config.ini

# Створення структури бази даних
echo "Створення структури бази даних..."
alembic revision --autogenerate -m "Init migration"
alembic upgrade head

# Створення unit файлу для systemd
echo "Створення unit файлу для systemd..."
sudo bash -c "cat > /etc/systemd/system/$SERVICE_NAME.service" << EOL
[Unit]
Description=$SERVICE_NAME service
After=network.target

[Service]
User=$USER
WorkingDirectory=$PWD
ExecStart=$PWD/$VENV_DIR/bin/uvicorn $APP_MODULE --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOL

# Перезапуск systemd та запуск сервісу
echo "Перезапуск systemd та запуск сервісу..."
sudo systemctl daemon-reload
sudo systemctl start $SERVICE_NAME
sudo systemctl enable $SERVICE_NAME

echo "Встановлення завершено! Сервіс $SERVICE_NAME запущено та додано в автозапуск."
