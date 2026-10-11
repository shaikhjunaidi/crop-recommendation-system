# Render Deployment Guide: Django Crop Recommendation System

This guide outlines the complete configuration, environment variables, build procedures, and deployment instructions for deploying the **Crop Recommendation System** on **Render** (as a Web Service) with an external **MySQL** database.

---

## 1. Discovered Project Architecture & Structure

```
crop/
├── crop/                                # Django Project Configuration
│   ├── __init__.py                     # Configures PyMySQL as MySQLdb
│   ├── asgi.py                         # ASGI entrypoint
│   ├── settings.py                     # Production-hardened settings (WhiteNoise, MySQL, Env vars)
│   ├── urls.py                         # Root URLconf (admin/ and app routes)
│   └── wsgi.py                         # WSGI entrypoint (used by Gunicorn)
├── recommender/                         # Core Django Application
│   ├── migrations/                     # Database migrations
│   │   ├── 0001_initial.py             # UserProfile & Prediction tables
│   │   └── 0002_alter_prediction_options.py # Ordering for predictions
│   ├── ml/                             # Machine Learning Module
│   │   ├── Crop_recommendation_RF.pkl  # Trained Random Forest Model (7.26 MB)
│   │   └── loader.py                   # LRU-cached lazy model loader & prediction runner
│   ├── static/                         # CSS, JS, and image assets
│   ├── templates/                      # Bootstrap 5 HTML templates
│   ├── apps.py                         # App configuration (BigAutoField)
│   ├── models.py                       # UserProfile & Prediction models
│   ├── tests.py                        # Automated test suite (11 unit/integration tests)
│   ├── urls.py                         # Recommender URL routing
│   └── views.py                        # Views: Auth, Profile, Predict, Admin Dashboard
├── build.sh                            # Render executable build script
├── manage.py                           # Django CLI
├── requirements.txt                    # Python dependencies
├── .env.example                        # Template for required environment variables
├── .gitignore                          # Git ignore rules for Django, models, and cache
└── LICENSE                             # MIT License
```

---

## 2. Dependencies & Runtime

The project runs on **Python 3.12** and requires the following runtime dependencies pinned in [`requirements.txt`](file:///c:/Users/Junaid/Desktop/crop/requirements.txt):

| Package | Purpose |
| :--- | :--- |
| `Django==6.0.1` | Core Web Framework |
| `mysqlclient==2.2.8` | Native C-based MySQL adapter |
| `PyMySQL>=1.1.0` | Pure-Python MySQL adapter (configured in `crop/__init__.py`) |
| `cryptography>=42.0.0` | Required for MySQL 8 authentication (`caching_sha2_password`) |
| `scikit-learn==1.9.0` | ML model runtime (`RandomForestClassifier`) |
| `pandas==2.3.3` | Data processing dependency |
| `numpy==1.26.4` | Numerical array handling for predictions |
| `gunicorn>=22.0.0` | Production WSGI HTTP Server for Linux containers |
| `whitenoise>=6.6.0` | Static asset compression and caching |
| `python-dotenv>=1.0.0` | Local `.env` support for seamless local testing |
| `dj-database-url>=2.1.0` | Support for cloud `DATABASE_URL` strings |

---

## 3. Recommended Render Web Service Configuration

1. Log into [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** > **Web Service**.
3. Connect your GitHub repository: `https://github.com/shaikhjunaidi/crop-recommendation-system`.
4. Choose the `main` branch.
5. Configure the following fields:
   - **Name**: `crop-recommendation-system` (or your preferred name)
   - **Region**: Choose the region closest to your users / database
   - **Runtime**: `Python 3`
   - **Build Command**: `./build.sh` (or `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`)
   - **Start Command**: `gunicorn crop.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120`
   - **Plan**: Free (or Starter for persistent RAM)

---

## 4. Required Render Environment Variables

In your Render service dashboard, navigate to **Environment** and define the following variables:

| Variable Name | Required | Recommended Production Value / Description |
| :--- | :--- | :--- |
| `DJANGO_DEBUG` | **Yes** | `False` |
| `DJANGO_SECRET_KEY` | **Yes** | Long, cryptographically secure 50+ character string. Generate with `python -c "import secrets; print(secrets.token_urlsafe(50))"` |
| `DJANGO_ALLOWED_HOSTS` | **Yes** | `localhost,127.0.0.1,your-service-name.onrender.com` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | **Yes** | `https://your-service-name.onrender.com` |
| `PYTHON_VERSION` | Optional | `3.12.3` |

### Database Variables (Choose Option A or Option B)

#### Option A: Single Connection URL (Recommended for cloud providers)
| Variable Name | Description | Example |
| :--- | :--- | :--- |
| `DATABASE_URL` | Complete MySQL connection string | `mysql://user:password@host.aivencloud.com:15234/crop_recommender` |
| `DB_SSL_REQUIRE` | Enable SSL for managed cloud databases | `True` |

#### Option B: Discrete Parameters
| Variable Name | Description | Example |
| :--- | :--- | :--- |
| `DB_NAME` | Database name | `crop_recommender` |
| `DB_USER` | MySQL username | `avnadmin` |
| `DB_PASSWORD` | MySQL password | `your_secret_password` |
| `DB_HOST` | MySQL hostname / endpoint | `mysql-3a-crop.aivencloud.com` |
| `DB_PORT` | MySQL port | `3306` (or provider port) |
| `DB_SSL_MODE` | SSL Mode (`REQUIRED`, `PREFERRED`) | `REQUIRED` |

---

## 5. MySQL Connection Requirements & Provider Selection

> [!IMPORTANT]
> **Render does not offer a managed MySQL service** (Render only offers PostgreSQL and Redis).
> You **must** provision an external MySQL database.

### Recommended Managed MySQL Providers (with Free / Affordable Tiers):
1. **Aiven for MySQL**: Offers a free tier with 1 CPU, 1 GB RAM, 5 GB storage, SSL enabled.
2. **TiDB Cloud (Serverless)**: MySQL-compatible distributed SQL database with generous free tier (5 GiB storage).
3. **Clever Cloud**: Offers free MySQL database add-on.
4. **Railway**: Offers MySQL instances with pay-as-you-go billing.

### SSL Requirements:
Most cloud providers (like Aiven or AWS RDS) require encrypted SSL connections. Our configuration automatically supports this via:
- `DB_SSL_MODE=REQUIRED` (or setting `DATABASE_URL` with `DB_SSL_REQUIRE=True`).
- `PyMySQL` and `cryptography` handle the secure handshake without requiring manual C certificates.

---

## 6. Build & Migration Procedure

The project includes an automated build script [`build.sh`](file:///c:/Users/Junaid/Desktop/crop/build.sh):
```bash
#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
```

- When Render runs `./build.sh`, it will:
  1. Install all dependencies from `requirements.txt`.
  2. Run `collectstatic --noinput` to compile assets into `staticfiles/` via WhiteNoise.
  3. Run `migrate` to apply all migrations (`admin`, `auth`, `contenttypes`, `sessions`, `recommender`) to the remote MySQL database.

---

## 7. Machine Learning Model Considerations

1. **Model File Location & Size**:
   - Path: `recommender/ml/Crop_recommendation_RF.pkl`
   - File Size: **7.26 MB**.
   - Git Storage: Because 7.26 MB is well below GitHub's 100 MB file limit, the model artifact is checked directly into the Git repository. No external S3 / Cloud Storage download step is required.
2. **Lazy Loading Optimization**:
   - In [`recommender/views.py`](file:///c:/Users/Junaid/Desktop/crop/recommender/views.py#L68-L101), the model is loaded **only** when a prediction is submitted via `POST /predict/`.
   - Routine `GET /predict/` page visits do not load the 7 MB model into memory.
   - The model bundle is cached in RAM using `@lru_cache(maxsize=1)` once loaded, ensuring fast subsequent predictions.
3. **RAM Footprint**:
   - The Random Forest model consumes ~35 MB of RAM once loaded into memory.
   - Render's Free tier provides **512 MB of RAM**, which is plenty for this model.
   - Running Gunicorn with `--workers 2 --threads 4` keeps memory usage well under 250 MB total.

---

## 8. Verifying Application Workflows After Deployment

Once deployed, verify each workflow at `https://your-service-name.onrender.com`:

1. **User Registration**:
   - Visit `/signup/`. Register a test account. Verify redirect to `/predict/` and account creation in MySQL.
2. **User Login & Logout**:
   - Visit `/logout/`, then `/login/`. Confirm session persists and credentials authenticate.
3. **Crop Prediction**:
   - Enter soil metrics (`N`, `P`, `K`, `temperature`, `humidity`, `ph`, `rainfall`).
   - Submit form. Verify the recommended crop result is displayed (e.g., "The recommended crop: rice.").
4. **Prediction History**:
   - Visit `/user_history/`. Confirm the previous prediction appears with timestamps and values.
5. **Password Change**:
   - Visit `/change_password/`. Change password and verify the session remains authenticated (`update_session_auth_hash`).
6. **Admin Creation & Dashboard**:
   - In Render Dashboard, open the **Shell** tab of your service.
   - Run: `python manage.py createsuperuser`
   - Follow prompts to create an admin account.
   - Visit `/admin_login/`. Log in with your admin credentials.
   - Check the **Dashboard** charts (daily predictions, top crops) and user management at `/admin_users_view/`.

---

## 9. Common Deployment Issues & Solutions

### 1. `Invalid HTTP_HOST header: 'xxx.onrender.com'. You may need to add 'xxx.onrender.com' to ALLOWED_HOSTS.`
- **Cause**: Render hostname was not added to `DJANGO_ALLOWED_HOSTS`.
- **Fix**: The updated [`crop/settings.py`](file:///c:/Users/Junaid/Desktop/crop/crop/settings.py) automatically includes `RENDER_EXTERNAL_HOSTNAME`. If you use a custom domain, add it to `DJANGO_ALLOWED_HOSTS`.

### 2. `CSRF verification failed. Request aborted.`
- **Cause**: Origin header is HTTPS on Render's domain, but Django's `CSRF_TRUSTED_ORIGINS` was missing the origin.
- **Fix**: [`crop/settings.py`](file:///c:/Users/Junaid/Desktop/crop/crop/settings.py) automatically adds `https://{RENDER_EXTERNAL_HOSTNAME}` to `CSRF_TRUSTED_ORIGINS`. Add any custom domain to `DJANGO_CSRF_TRUSTED_ORIGINS`.

### 3. Infinite HTTPS Redirect Loop
- **Cause**: Render proxy terminates SSL and forwards requests to the app over HTTP. Without `SECURE_PROXY_SSL_HEADER`, Django redirects HTTP requests back to HTTPS endlessly.
- **Fix**: Already configured in [`crop/settings.py`](file:///c:/Users/Junaid/Desktop/crop/crop/settings.py):
  ```python
  SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
  ```

### 4. `django.db.utils.OperationalError: (2003, "Can't connect to MySQL server")`
- **Cause**: Incorrect database hostname/port, database firewall blocking Render's outgoing IPs, or database sleeping.
- **Fix**: Ensure your MySQL provider allows connections from `0.0.0.0/0` (Render uses dynamic IP addresses). Double check `DB_HOST`, `DB_PORT`, and credentials.

### 5. Render Free Tier Spin-Down (Cold Starts)
- **Behavior**: On Render Free tier, instances spin down after 15 minutes of inactivity. The first request after spin-down may take ~45–60 seconds to boot the container.
- **Remedy**: This is normal on free tier. To keep it awake 24/7 without delays, upgrade to Render Starter plan ($7/mo) or use a free uptime monitor (e.g., UptimeRobot) pinging the homepage every 10 minutes.
