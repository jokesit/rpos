from pathlib import Path
import os
import environ

# เริ่มต้น Environ
env = environ.Env(
    # กำหนดค่า Default และชนิดข้อมูล
    DEBUG=(bool, False)
)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))


# --- Security Configuration ---
SECRET_KEY = env('SECRET_KEY')

# แปลงค่า True/False/on/off จาก .env ให้เป็น Boolean
DEBUG = env('DEBUG')

# แปลง string คั่นด้วยลูกน้ำ ให้เป็น List
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')


# Application definition

INSTALLED_APPS = [
    'daphne', # ใส่ไว้บนสุดสำหรับ Channels

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # 3rd Party Apps
    'allauth',
    'allauth.account',
    'allauth.socialaccount', # ถ้าอนาคตอยากให้ login ผ่าน Google/Facebook
    'tailwind',
    'theme',
    'django_browser_reload',

    # My Apps
    'users.apps.UsersConfig',
    'restaurants.apps.RestaurantsConfig',
    'dining.apps.DiningConfig',
    'orders.apps.OrdersConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    
    # ⭐ ใส่ Middleware ของเราตรงนี้ (ลำดับสำคัญ) ⭐
    'users.middleware.MaintenanceModeMiddleware',  # 1. เช็คว่าปิดปรับปรุงไหม (ถ้าปิด คนทั่วไปจะหยุดตรงนี้)
    'users.middleware.ApprovalMiddleware',         # 2. เช็คอนุมัติ
    'users.middleware.AdminIPRestrictMiddleware',  # 3. เช็ค IP Admin

    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # ต้องมี Middleware ของ allauth
    'allauth.account.middleware.AccountMiddleware',

    "django_browser_reload.middleware.BrowserReloadMiddleware",
]

ROOT_URLCONF = 'config.urls'


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [ BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# --- Database (ดึงจาก .env) ---
# django-environ จะแปลง DATABASE_URL เป็น Dictionary ให้เองอัตโนมัติ
DATABASES = {
    'default': env.db('DATABASE_URL')
}


# Config การ Authentication
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]


# Config Allauth Behavior
SITE_ID = 1


# ==================================================
# 10 django-allauth Configuration (Secure & Modern)
# ==================================================

# 1. Login Methods: ใช้ Email + Password เท่านั้น
ACCOUNT_LOGIN_METHODS = {"email"}

# 2. ปิด Login by Code (Magic Link) ถาวร
ACCOUNT_LOGIN_BY_CODE_ENABLED = False

# 3. บังคับใช้ Password
ACCOUNT_LOGIN_BY_PASSWORD_ENABLED = True

# 4. Email Settings
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_VERIFICATION = "mandatory" # บังคับยืนยันอีเมลก่อนใช้งาน
ACCOUNT_CONFIRM_EMAIL_ON_GET = True # กดลิงก์แล้วยืนยันเลย (ลดขั้นตอนหน้าเว็บ)

# 5. Username Settings 
ACCOUNT_USER_MODEL_USERNAME_FIELD = "username"
# ACCOUNT_USERNAME_REQUIRED = True

# ไม่ต้องซีเรียสเรื่องตัวเล็กตัวใหญ่
ACCOUNT_PRESERVE_USERNAME_CASING = False

# 6. Signup Fields
ACCOUNT_SIGNUP_FIELDS = [
    "email*", # * ใน new style ไม่ต้องใส่ * แล้ว
    "username*",
    "password1*",
    "password2*",
]


# 7. UX & Security
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_EMAIL_SUBJECT_PREFIX = "[RPOS System] "
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# Model User ของเรา
AUTH_USER_MODEL = 'users.User' 

# --------------------------------------------------
# Email Configuration (Gmail SMTP)
# --------------------------------------------------
# ดึงค่าจาก .env แทนการ Hardcode (ปลอดภัยกว่า)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env("EMAIL_HOST_USER") # ดึง user
EMAIL_HOST_PASSWORD = env("EMAIL_AUTHEN") # ดึง app password
DEFAULT_FROM_EMAIL = f"RPOS Admin <{EMAIL_HOST_USER}>"


# --- Channels / Redis ---
ASGI_APPLICATION = 'config.asgi.application'
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Bangkok'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = 'static/'

# URL ที่จะใช้เรียกดูรูปใน browser
MEDIA_URL = '/media/'

# โฟลเดอร์จริงในเครื่องที่จะใช้เก็บไฟล์
MEDIA_ROOT = BASE_DIR / 'media'

ACCOUNT_LOGOUT_ON_GET = False
ACCOUNT_LOGOUT_REDIRECT_URL = 'home'

# Config Tailwind
TAILWIND_APP_NAME = 'theme'

INTERNAL_IPS = [
    "127.0.0.1",
]


# for maintenance
ADMIN_IP_RESTRICTION = env.bool('ADMIN_IP_RESTRICTION', default=False)
ADMIN_ALLOWED_IPS = env.list('ADMIN_ALLOWED_IPS', default=['127.0.0.1'])

# ⭐ เพิ่มบรรทัดนี้ ⭐
MAINTENANCE_MODE = env.bool('MAINTENANCE_MODE', default=False)

# -------