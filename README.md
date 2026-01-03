## Configuration Development Environment

1. **Create .env file:**
   ```bash
   cp .env.example .env
   ```

2. **Create the virtual environment:**
   ```bash
   python3 -m venv venv
   ```

3. **Activate Env**
   ```bash
   source venv/bin/activate
   ```

4. **Install Dependencies:**
   ```bash
   pip install -r requirements/development.txt
   ```

5. **Run Migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create Super User**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run Server**
   ```bash
   python manage.py runserver
   ```

## Location Information

1. **Get Location Information**
```bash
   python manage.py loaddata apps/core/fixtures/ubigeo_data.json
```

## Coverage

1. **Run Tests with coverage**
   ```bash
   coverage run manage.py test --settings=config.settings.testing
   ```

2. **Generate report**
   ```bash
   coverage report --sort=cover
   ```

3. **Generate HTML report**
   ```bash
   coverage html
   ```

## Linting

1. **Install packages**
```bash
   pip install -r requirements/linters.txt
```

1. **Install pre-commit hooks**
```bash
   pre-commit install
```

2. **Run pre-commit hooks**
```bash
   pre-commit run --all-files
```

## Translations

1. **Generate translation files**
```bash
   python manage.py makemessages -l es --ignore "venv/*"
```

2. **Compile translation files**
```bash
   python manage.py compilemessages -l es --ignore "venv/*"
```
