# Інсталяція сервісу вручну

Також існує можливість встановлення вебсервісу вручну, без застосування скрипта.
Для початку роботи потрібно мати чисту систему Ubuntu, всі необхідні пакети та репозиторії будуть підключені в ході виконання встановлення.

**Для того, щоб встановити даний вебсервіс вручну необхідно:**

### 1. Встановити необхідні пакети:

```bash
sudo apt-get update
sudo apt-get install -y curl libmariadb-dev gcc python3 python3-venv python3-dev git
```
**Важливо** Якщо версія Python нижче 3.10, сервіс працювати не буде.

### 2. Додати репозиторій MariaDB:

```bash
curl -LsS https://r.mariadb.com/downloads/mariadb_repo_setup | sudo bash
```

### 3. Встановити СУБД MariaDB:

```bash
sudo apt-get update
sudo apt-get install -y mariadb-server
```

### 4. Запустити MariaDB та налаштувати автозапуск:

```bash
sudo systemctl start mariadb
sudo systemctl enable mariadb
```

### 5. Перевірити, чи працює MariaDB:

```bash
sudo systemctl status mariadb
```

**Примітка** Якщо базу даних запущено, можна переходити до виконання наступних кроків.
Інакше – потрібно перевірити чи не було допущено помилку при виконанні одного з попередніх кроків.

### 6. Створити базу даних та користувача. Для цього необхідно:

6.1. Увійти у консоль MariaDB:

```bash
sudo mysql
```

6.2. Створити базу даних:
```sql
CREATE DATABASE IF NOT EXISTS your_db_name CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```
де: `your_db_name` - бажана назва БД.

6.3. Створити користувача:
```sql
CREATE USER IF NOT EXISTS 'your_db_user'@'%' IDENTIFIED BY 'your_db_password';
```
де:
- `your_db_user` – логін користувача БД;
- `your_db_password`– пароль для даного користувача.

6.4. Надати користувачеві повні права на базу даних, замінивши `your_db_name` на назву раніше створеної  БД а `your_db_user` на логін створеного на попередньому кроці користувача:
```sql
GRANT ALL PRIVILEGES ON your_db_name.* TO 'your_db_user'@'%';
```

6.5. Примусово оновити привілеї:

```sql
FLUSH PRIVILEGES;
```

Базу даних та користувача успішно створено.

6.6. Вийти з консолі MariaDB:

```bash
exit
```

### 7. Клонувати репозиторій

```bash
git clone https://github.com/kshypachov/FastAPI_trembita_service.git
```

### 8. Перейти до директорії з вебсервісом:

```bash
cd FastAPI_trembita_service
```

### 9. Створити віртуальне середовище:

```bash
python3 -m venv venv
```

### 10. Активувати віртуальне середовище:

```bash
source venv/bin/activate
```

### 11. Встановити залежності:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 12. Виконати конфігурацію вебсервісу згідно [настанов з конфігурації](/docs/configuration.md)

### 13. Створити структуру бази даних, для чого необхідно:

13.1. Створити початкову міграцію:

```bash
alembic revision --autogenerate -m "Init migration"
```

13.2. Застосувати міграції для створення структури бази даних:

```bash
alembic upgrade head
```

### 14. Створити systemd unit-файл для запуску вебсервісу:

**Примітка** Перед виконанням команди необхідно перевірити за допомого `pwd` що ви знаходитесь у директорії `FastAPI_trembita_service`. 

Створіть systemd unit-файл для запуску сервісу:

```bash
sudo bash -c "cat > /etc/systemd/system/fastapi_trembita_service.service" << EOL
[Unit]
Description=FastAPI Trembita Service
After=network.target

[Service]
User=$USER
WorkingDirectory=$PWD
ExecStart=$PWD/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOL
```

### 15.	Перезавантажити конфігурацію systemd:

```bash
sudo systemctl daemon-reload
```

### 16. Додати сервіс до автозапуску:

```bash
sudo systemctl enable fastapi_trembita_service
```

##
Матеріали створено за підтримки проєкту міжнародної технічної допомоги «Підтримка ЄС цифрової трансформації України (DT4UA)».
