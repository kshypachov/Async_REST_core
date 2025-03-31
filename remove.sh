#!/bin/bash

# Змінні для конфігурації
PROJECT_DIR="FastAPI_trembita_service"
VENV_DIR="venv"
SERVICE_NAME="fastapi_trembita_service"
CONFIG_FILE="config.ini"

# Функція для зчитування параметрів з config.ini
function get_config_value() {
    local section=$1
    local key=$2
    local config_file=$3
    local value=$(awk -F "=" '/\['"$section"'\]/{a=1}a==1&&$1~/'"$key"'/{gsub(/[ \t]+$/, "", $2); print $2; exit}' $config_file)
    echo $value
}

# Отримання параметрів бази даних з config.ini
DB_NAME=$(get_config_value "database" "name" $CONFIG_FILE)
DB_USER=$(get_config_value "database" "username" $CONFIG_FILE)
DB_PASSWORD=$(get_config_value "database" "password" $CONFIG_FILE)

# Перевірка, чи скрипт запускається з папки FastAPI_trembita_service
if [ "$(basename "$PWD")" != "$PROJECT_DIR" ]; then
    echo "Будь ласка, запустіть цей скрипт з директорії $PROJECT_DIR."
    exit 1
fi

# Зупинка та видалення системного сервісу
echo "Зупинка та видалення системного сервісу..."
sudo systemctl stop $SERVICE_NAME
sudo systemctl disable $SERVICE_NAME
sudo rm /etc/systemd/system/$SERVICE_NAME.service
sudo systemctl daemon-reload
sudo systemctl reset-failed

# Видалення віртуального середовища
if [ -d "$VENV_DIR" ]; then
    echo "Видалення віртуального середовища..."
    rm -rf "$VENV_DIR"
else
    echo "Віртуальне середовище не знайдено."
fi

# Перехід на один рівень вище для видалення клонованого репозиторію
cd ..

# Видалення клонованого репозиторію
if [ -d "$PROJECT_DIR" ]; then
    echo "Видалення клонованого репозиторію..."
    rm -rf "$PROJECT_DIR"
else
    echo "Клонований репозиторій не знайдено."
fi

# Видалення бази даних та користувача
echo "Видалення бази даних та користувача..."
sudo mysql -e "DROP DATABASE IF EXISTS $DB_NAME;"
sudo mysql -e "DROP USER IF EXISTS '$DB_USER'@'%';"
sudo mysql -e "FLUSH PRIVILEGES;"

echo "Видалення завершено!"
