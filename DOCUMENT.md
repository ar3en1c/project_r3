# مستندات جامع پروژه «ونتا»

پروژه **ونتا** یک وب‌سایت ردیابی فیلم و سریال (Tracker) به زبان فارسی است که با جنگو (Django) ساخته شده و الهام گرفته از سرویس simkl.com است. کاربر می‌تواند فیلم‌ها و سریال‌ها را در وضعیت‌های مختلف (در حال تماشا، برنامه تماشا، تکمیل شده، رها شده) ردیابی کند، به آن‌ها امتیاز دهد، نظر ثبت کند، به علاقه‌مندی اضافه کند و از پیشنهادهای شخصی‌سازی‌شده بهره ببرد.

طراحی ظاهری پروژه یک **تم ترمینالی/سایبرپانکی** است: فونت تک‌فاصله، رنگ سبز نئونی (`#3DD68C`)، پس‌زمینه تیره، عنوان‌های آندرلاین‌دار و کامندهایی مثل `ادامه_تماشا` و `برنامه_تماشا`. کل استایل‌ها با **Sass/SCSS** نوشته می‌شوند و به CSS کامپایل می‌شوند (قبل از تغییر هر استایل باید فایل SCSS تغییر کند، نه CSS).

---

## فهرست مطالب

1. [نصب و راه‌اندازی](#نصب-و-راه‌اندازی)
2. [ساختار کلی پروژه](#ساختار-کلی-پروژه)
3. [تنظیمات (settings)](#تنظیمات-settings)
4. [مسیرها (URLs) و ویوها](#مسیرها-urls-و-ویوها)
5. [مدل‌های داده (Models)](#مدلهای-داده-models)
6. [سیستم ردیابی (Tracking)](#سیستم-ردیابی-tracking)
7. [صفحه اصلی (Home)](#صفحه-اصلی-home)
8. [صفحات فیلم و سریال](#صفحات-فیلم-و-سریال)
9. [احراز هویت و پروفایل](#احراز-هویت-و-پروفایل)
10. [جستجو](#جستجو)
11. [برترین‌ها (Top 250)](#برترینها-top-250)
12. [قالب‌های سراسری (Base / Header / Sidebar / Footer)](#قالبهای-سراسری)
13. [سیستم تم (Theme)](#سیستم-تم-theme)
14. [اسکریپت‌های جمع‌آوری داده](#اسکریپتهای-جمعآوری-داده)
15. [یادداشت‌های فنی](#یادداشتهای-فنی)

---

## نصب و راه‌اندازی

1. **پیش‌نیازها:** پایتون 3.13+، PostgreSQL، و Sass (کامپایلر SCSS).
2. **مجازی‌ساز:** در ریشه پروژه دو پوشه مجازی‌ساز وجود دارد؛ `venv` (مقصد اصلی برای اجرا و تست) و `l_venv` (نسخه آزمایشی/سیستمی).
   ```powershell
   .\venv\Scripts\Activate.ps1
   pip install -r req.txt
   ```
3. **متغیرهای محیطی:** فایل `.env` در ریشه پروژه — مقادیر زیر باید تعریف شوند:
   ```
   SECRET_KEY=...
   DB_NAME=...   DB_USER=...   DB_PASSWORD=...   DB_HOST=...   DB_PORT=5432
   TVDB_API_KEY=...   # فقط برای اسکریپت‌های جمع‌آوری داده
   ```
4. **پایگاه داده:** پروژه از PostgreSQL استفاده می‌کند (اطلاعات اتصال از `.env` خوانده می‌شود).
   ```powershell
   python manage.py migrate
   python manage.py createsuperuser
   ```
5. **کامپایل SCSS:** بعد از هر تغییر در `static/scss/*.scss` باید CSS تولید شود:
   ```powershell
   sass --no-source-map static/scss/home.scss static/css/home.css
   ```
6. **اجرا:**
   ```powershell
   python manage.py runserver
   ```
   - صفحه اصلی: `http://127.0.0.1:8000/` (نیازمند ورود)
   - پنل ادمین: `http://127.0.0.1:8000/admin/`

---

## ساختار کلی پروژه

```
project_r3/
├── config/          # پیکربندی مرکزی (settings, urls, wsgi/asgi)
├── home/            # صفحه اصلی داشبورد کاربر
├── series/          # اپ سریال‌ها (مدل، ویو، قالب، کامنت)
├── movies/          # اپ فیلم‌ها (مدل، ویو، قالب، کامنت)
├── tracking/        # اپ ردیابی (مدل Track + اکشن‌های وضعیت/پیشرفت/امتیاز/علاقه + filtering.py مشترک)
├── users/           # اپ کاربران (مدل User سفارشی، ورود/ثبت‌نام، پروفایل و لیست‌های پخش)
├── search/          # جستجوی سراسری هدر
├── top250/          # فهرست ۲۵۰ فیلم/سریال برتر IMDb
├── templates/       # قالب‌های سراسری (base, header, sidebar, footer)
├── static/          # فایل‌های استاتیک
│   ├── scss/        # فایل‌های Sass (منبع استایل — باید ویرایش شوند)
│   ├── css/         # خروجی کامپایل‌شده Sass (دستی تغییر نمی‌دهیم)
│   ├── javascript/  # جاوااسکریپت‌ها (series.js)
│   ├── assets/      # کتابخانه‌های htmx و Alpine.js
│   ├── fonts/       # فونت وزیر
│   └── images/      # لوگو، پوستر جایگزین، لوگوی فیلیمو/نماوا
├── scripts/         # اسکریپت‌های جمع‌آوری/وارد کردن داده از TVDB و IMDb
├── datas/           # فایل‌های خام داده (JSONL فشرده، CSV رتبه‌بندی، نسخه پشتیبان ترجمه)
├── media/           # فایل‌های آپلودی کاربران (تصویر پروفایل)
├── graphify-out/    # خروجی گراف دانش پروژه (دستگاه Graphify)
├── manage.py
├── req.txt          # وابستگی‌های پایتون
└── .env             # متغیرهای محیطی (در git نیست)
```

---

## تنظیمات (settings)

فایل: `config/settings.py`

| تنظیم | مقدار | توضیح |
|---|---|---|
| `AUTH_USER_MODEL` | `users.User` | مدل کاربر سفارشی |
| `LANGUAGE_CODE` | `fa-IR` | فارسی |
| `TIME_ZONE` | `Asia/Tehran` | تهران |
| `DATABASES` | PostgreSQL | از `.env` خوانده می‌شود |
| `PASSWORD_HASHERS` | Argon2 (اولویت) + PBKDF2 (پشتیبان) | مطابق توصیه OWASP |
| `LOGIN_URL` / `LOGIN_REDIRECT_URL` / `LOGOUT_REDIRECT_URL` | `users:login` / `series:mainSeries` | پس از ورود/خروج به فهرست سریال‌ها برمی‌گردد |
| `STATICFILES_DIRS` | `BASE_DIR / "static"` | فایل‌های استاتیک پروژه |
| `MEDIA_ROOT` / `MEDIA_URL` | `media/` / `/media/` | آپلود کاربران |
| `INSTALLED_APPS` | اپ‌های پروژه + `django_render_partial` + اپ‌های پیش‌فرض جنگو | |

**مدل کاربر سفارشی** (`users/models.py`) — `AbstractUser` به‌علاوه:
- `phone_number` — شماره تلفن (اختیاری)
- `profile_picture` — تصویر پروفایل (ImageField)
- `create_at` / `update_at` — زمان‌ها

---

## مسیرها (URLs) و ویوها

### نقشه کامل URL

| مسیر | نام (name) | اپ | توضیح |
|---|---|---|---|
| `/` | `mainPage` | home | صفحه اصلی (داشبورد کاربر) |
| `/admin/` | — | admin | پنل مدیریت |
| `/series/` | `series:mainSeries` | series | فهرست سریال‌ها |
| `/series/filter/` | `series:series_filter` | series | اندپوینت HTMX پنل فیلتر سریال‌ها |
| `/series/header/` · `/series/footer/` | `series:header` · `series:footer` | series | پارشال‌های هدر/فوتر |
| `/series/<slug>/` | `series:series_detail` | series | جزئیات سریال |
| `/series/<slug>/comment/` | `series:series_comment` | series | ثبت نظر سریال |
| `/series/person/<tvdb_id>/` | `series:person_detail` | series | صفحه بازیگر/شخص |
| `/movies/` | `movie_list` | movies | فهرست فیلم‌ها (بدون namespace!) |
| `/movies/filter/` | `movie_filter` | movies | اندپوینت HTMX پنل فیلتر فیلم‌ها |
| `/movies/<slug>/` | `movie_detail` | movies | جزئیات فیلم |
| `/movies/<slug>/comment/` | `movie_comment` | movies | ثبت نظر فیلم |
| `/tracking/series/<slug>/status/` | `tracking:series_status` | tracking | تغییر وضعیت سریال |
| `/tracking/series/<slug>/progress/` | `tracking:series_progress` | tracking | تنظیم پیشرفت |
| `/tracking/series/<slug>/progress/increment/` | `tracking:series_progress_increment` | tracking | +۱ قسمت (صفحه اصلی) |
| `/tracking/series/<slug>/rating/` | `tracking:series_rating` | tracking | امتیاز سریال |
| `/tracking/series/<slug>/favorite/` | `tracking:series_favorite` | tracking | علاقه سریال |
| `/tracking/movies/<slug>/status/` | `tracking:movie_status` | tracking | تغییر وضعیت فیلم |
| `/tracking/movies/<slug>/rating/` | `tracking:movie_rating` | tracking | امتیاز فیلم |
| `/tracking/movies/<slug>/favorite/` | `tracking:movie_favorite` | tracking | علاقه فیلم |
| `/tracking/favorites/` | `tracking:favorites` | tracking | صفحه علاقه‌مندی‌ها |
| `/tracking/favorite/remove/` | `tracking:remove_favorite` | tracking | حذف علاقه (HTMX) |
| `/account/` | `users:profile` | users | پروفایل خود کاربر (ردیرکت به صفحه عمومی) |
| `/account/u/<user_id>/` | `users:public_profile` | users | پروفایل عمومی/قابل اشتراک‌گذاری |
| `/account/login/` · `/account/signup/` · `/account/logout/` | `users:login` · `users:signup` · `users:logout` | users | احراز هویت |
| `/account/series/<slug>/stage/` | `users:series_stage` | users | تغییر وضعیت از پروفایل |
| `/account/series/<slug>/step/` | `users:series_step` | users | ±قسمت از پروفایل |
| `/account/movies/<slug>/stage/` | `users:movie_stage` | users | تغییر وضعیت فیلم از پروفایل |
| `/account/rate/` | `users:rate` | users | امتیازدهی یکپارچه (type+slug) |
| `/search/q/` | `search:query` | search | جستجوی زنده هدر (HTMX) |
| `/top250/` | `top250:top250` | top250 | ۲۵۰ فیلم/سریال برتر |

> **نکته مهم:** اپ `movies` در `movies/urls.py` مقدار `app_name` ندارد؛ بنابراین در قالب‌ها از `{% url 'movie_detail' %}` (بدون پیشوند) استفاده می‌شود، در حالی که بقیه اپ‌ها namespace دارند (`series:...`، `users:...` و…).

### تعاملات HTMX و دکوراتورها

- همه اکشن‌های ردیابی و کامنت فقط POST هستند (`@require_POST`).
- `htmx_login_required` (در `tracking/views.py`) — مانند `login_required` ولی برای درخواست‌های HTMX هدر `HX-Redirect` برمی‌گرداند تا صفحه ورود داخل المان قالب جا نزند.
- `django_render_partial` برای رندر هدر/فوتر در همه صفحات استفاده می‌شود.

---

## مدل‌های داده (Models)

### اپ series (`series/models.py`)

| مدل | فیلدهای اصلی | توضیح |
|---|---|---|
| `Series` | `tvdb_id`, `name`, `slug`, `image`, `year`, `overview`, `original_country`, `original_language`, `status`, `episode_count`, `season_count`, `rate`, `filimo`, `namava`, `name_en`, `overview_en`, `name_fa` | سریال. نام فارسی در `name_fa` و نام انگلیسی در `name` ذخیره می‌شود. |
| `Genre` | `tvdb_id`, `name`, `slug` | ژانر (مشترک بین سریال و فیلم) |
| `SeriesGenre` | `series`, `genre` | رابطه چند‌به‌چند سریال–ژانر (جدول `series_genres`) |
| `RemoteId` | `series`, `remote_id`, `id_type`, `source_name` | شناسه‌های خارجی (مثلاً IMDb) |
| `Person` | `tvdb_id`, `name`, `image` | بازیگر/شخص |
| `Character` | `series`, `person`, `character_name`, `character_image`, `people_type` | کاراکتر یک سریال |
| `TagOption` | `series`, `tag`, `tag_name`, `name` | تگ‌های TVDB |
| `Comment` | `person`, `series`, `comment`, `is_active`, `created_at` | نظر روی سریال |

### اپ movies (`movies/models.py`)

| مدل | فیلدهای اصلی | توضیح |
|---|---|---|
| `Movies` | مثل `Series` (به‌جز `episode_count`/`season_count`) | فیلم. جدول `movies` |
| `MovieGenre` | `movies`, `genre` | رابطه فیلم–ژانر (جدول `movies_genre_links`) |
| `RemoteId` | `movies`, `remote_id`, `id_type`, `source_name` | شناسه خارجی فیلم |
| `Character` | `movies`, `person`, ... | کاراکتر فیلم |
| `TagOption` | `movies`, ... | تگ فیلم |
| `Comment` | `person`, `movies`, `comment`, `is_active`, `created_at` | نظر روی فیلم |

### اپ tracking (`tracking/models.py`) — مدل کلیدی پروژه

```python
class Track:
    typeOfWatch   # "Series" | "Movie"
    user          # FK → User
    serial        # FK → Series (اختیاری)
    movies        # FK → Movies (اختیاری)
    status        # "completed" | "watching" | "dropped" | "plan to watch"
    progress      # Integer — چند قسمت دیده شده (فقط برای سریال)
    user_rate     # Decimal(3,1) — امتیاز کاربر 0 تا 10
    favorite      # Boolean
    created_at / updated_at
```

- **قید یکتایی شرطی:** برای هر کاربر حداکثر یک رکورد فیلم و یک رکورد سریال (UniqueConstraint شرطی روی `typeOfWatch`).
- **`Track.clean()`** — اعتبارسنجی: نوع محتوا باید دقیقاً به یک FK اشاره کند؛ **فیلم‌ها اتمیک هستند** یعنی `progress` برای فیلم معنی ندارد و رد می‌شود (فقط وضعیت).
- **`Track.movie_status`** — وضعیت‌های مجاز فیلم: `completed`، `dropped`، `plan to watch` (بدون `watching` چون فیلم حالت میانی ندارد). سریال‌ها از `progress_status` کامل استفاده می‌کنند.

### نمودار روابط

```
User (1) ──< Track >── (1) Series
                 └────── (1) Movies
Series >── SeriesGenre <── Genre
Movies  >── MovieGenre  <── Genre
Series/Movies >── Character >── Person
Series/Movies >── RemoteId
Series/Movies >── Comment >── User
```

---

## سیستم ردیابی (Tracking)

قلب پروژه — همه عملیات کاربر روی محتوا از طریق `Track` انجام می‌شود.

### دکمه‌های وضعیت

- **سریال** (`series/partials/status_buttons.html`): چهار دکمه — تکمیل شده، در حال تماشا، رها شده، برنامه تماشا. با `status="completed"` پیشرفت خودکار به `episode_count` می‌رسد.
- **فیلم** (`movies/partials/status_buttons.html`): سه دکمه — بدون «در حال تماشا» (از `Track.movie_status`).

### پیشرفت سریال

- `set_series_progress` — تنظیم مستقیم شماره قسمت.
- `increment_series_progress` — دکمه «+۱ قسمت» در صفحه اصلی؛ پاسخ فقط متن `X / Y قسمت` است که یک `<span>` را به‌روز می‌کند (OOB نیست، target مستقیم).
- در صفحه پروفایل: `users:series_step` با `delta` مثبت/منفی؛ اگر به انتهای سریال برسد وضعیت به `completed` تغییر می‌کند و اگر از completed عقب بیاید به `watching` برمی‌گردد.

### امتیازدهی

- اسلایدر + پاپ‌آپ در `series.js` (`set_rating`, `toggle_rating_popover`, بستن با Escape).
- امتیاز ۰ = پاک کردن امتیاز (`users:rate` در پروفایل). محدوده ۱ تا ۱۰ در اکشن‌های جزئیات.

### علاقه‌مندی

- `favorite` یک Boolean روی Track است. صفحه `tracking/favorites` به دو تب فیلم/سریال تقسیم شده و حذف علاقه با HTMX کل لیست را دوباره رندر می‌کند (`tracking/partials/fav_list.html`).

### میانگین امتیاز کاربران

در صفحه جزئیات، میانگین `user_rate` همه کاربرانی که امتیاز داده‌اند محاسبه و نمایش داده می‌شود (`avg_rate`).

---

## صفحه اصلی (Home)

فایل: `home/views.py` + `home/templates/home/index.html`

صفحه اصلی فقط برای کاربران واردشده است (`@login_required`) و شامل ۵ بخش است:

1. **ادامه تماشا** — سریال‌های کاربر با وضعیت `watching`، مرتب‌شده بر اساس آخرین به‌روزرسانی (۱۰ مورد). هر کارت: پوستر، نام، نوار پیشرفت (`progress / episode_count`) و دکمه `+۱ قسمت` (HTMX).
2. **برنامه تماشا — فیلم‌ها** — فیلم‌های کاربر با وضعیت `plan to watch`، مرتب بر اساس `-movies__rate` (حداکثر ۵۰). ردیف افقی با اسکرول افقی (`.movie-row-scroll`).
3. **برنامه تماشا — سریال‌ها** — مثل بالا برای سریال‌ها (`-serial__rate`، حداکثر ۵۰).
4. **پیشنهاد بر اساس ژانر محبوب (فیلم)** — پرمصرف‌ترین ژانر در Track های فیلم کاربر با `Counter` محاسبه می‌شود، سپس فیلم‌های همان ژانر با `order_by("-year", "-rate")` پیشنهاد می‌شوند (۲۰ مورد).
5. **پیشنهاد بر اساس ژانر محبوب (سریال)** — همان منطق برای سریال‌ها (`serial__series_genres`).

**قالب کارت‌ها** — از پارشال‌های مشترک استفاده می‌شود:
- `movies/partials/card.html` (پوستر + بج امتیاز + نام + سال)
- `series/partials/card.html` (پوستر + بج امتیاز + تعداد قسمت + نام + سال)

در ردیف افقی، کارت‌ها با اندازه ثابت `140×210` پیکسل (نسبت ۲:۳) پین می‌شوند تا همه پوسترها یک‌اندازه دیده شوند (صرف‌نظر از نسبت تصویر منبع).

---

## صفحات فیلم و سریال

### فهرست‌ها (`series/list.html` و `movies/list.html`)

هر دو از یک الگو پیروی می‌کنند:

1. **هیرو (Hero)** — ۸ محتوای برتر (سریال: `rate > 8`؛ فیلم: `year > 2020` و `rate > 8`) به‌صورت اسلایدشوی آلپاین‌جی‌اس با چرخش خودکار هر ۴ ثانیه.
2. **ژانرها** — چیپ‌های ژانر.
3. **پنل فیلتر** — پنل فیلتر پیشرفته (توضیح کامل در ادامه).
4. **برترین‌های ژانر** — برای ژانرهای `drama`, `action`, `comedy` (۸ مورد، مرتب بر اساس امتیاز).
5. **برترین‌های کشور** — آمریکا، ایران، کره جنوبی (۸ مورد).
6. **بازیگران معروف** — لیست ثابت اسامی در ویو (دوزبان/ایرانی) که فقط در صورت وجود در DB نمایش داده می‌شوند.

### پنل فیلتر (Filter Panel)

فیلتر مشترک بین هر دو صفحه فهرست — قالب مشترک `templates/filter_panel.html` با ردیف‌های `movies/partials/filter_row.html` و `series/partials/filter_row.html`:

- **فیلترها:** ژانر (چیپ‌های فعال‌شونده با `active`)، کشور، سال (دقیق)، حداقل امتیاز (`rate__gte`).
- **مرتب‌سازی:** امتیاز، سال، جدیدترین (بر اساس `created_at`)، نام.
- **صفحه‌بندی:** آفست (۲۴ مورد در هر صفحه) با دکمه «بیشتر +».
- **تعامل:** همه کنترلها با HTMX یک GET به همان URL می‌فرستند و پنل با `outerHTML` سواپ میشود؛ بنابراین فیلترها جمع می‌شوند و در URL باقی می‌مانند (قابل اشتراک).
- **منطق:** `tracking/filtering.py` → `filter_qs(qs, request, countries, sort_opts)` — فیلتر ژانر با کلید داینامیک (`movie_genres__genre__slug` یا `series_genres__genre__slug`) ساخته می‌شود؛ محتواهای بدون تصویر یا امتیاز حذف می‌شوند.
- **ویوها:** `_movie_filter_ctx` / `_series_filter_ctx` (بافت پنل) + اندپوینت‌های HTMX `movies:movie_filter` و `series:series_filter` که فقط خود پنل را برمی‌گردانند.
- **رندر اولیه:** ویو فهرست، HTML پنل را با `render_to_string` می‌سازد و در `filter_panel|safe` در قالب درج می‌کند (بین بخش ژانرها و برترین‌ها).
- **استایل:** `static/scss/filter.scss` (پنل + ردیف‌های نتیجه).

### جزئیات (`series/index.html` و `movies/index.html`)

- **هیرو:** عنوان، سال، بج برترین‌ها (در صورت حضور در Top 250)، تگ‌های ژانر، کنترل ردیابی (وضعیت/پیشرفت/امتیاز/علاقه) و لینک‌های «تماشا در فیلیمو/نماوا».
- **ستون سمت راست (RTL):** کارت امتیاز (اسلایدر + میانگین کاربران + امتیاز IMDb)، کارت وضعیت (پایان‌یافته/در حال پخش + سال انتشار)، کارت متادیتا (آیدی IMDb، زبان، کشور).
- **ستون سمت چپ:** تب‌های جزئیات/نظرات (آلپاین‌جی‌اس) — خلاصه داستان، بازیگران (گرید با هاور)، و سیستم کامنت با HTMX.

### صفحه شخص (`series/person.html`)

نمایش کاراکترها و همه آثار (سریال + فیلم) یک بازیگر با `people_type="Actor"`، همراه وضعیت ردیابی هر اثر برای کاربر جاری.

---

## احراز هویت و پروفایل

### فرم‌ها (`users/forms.py`)

- `LoginForm` — از `AuthenticationForm` با کلاس `terminal-input`.
- `SignupForm` — از `UserCreationForm` (نام کاربری + ایمیل اجباری + دو رمز).

### پروفایل (`users/index.html`)

- **آمار کلی:** تعداد سریال/فیلم، در حال تماشا، برنامه تماشا، تکمیل شده، میانگین امتیاز.
- **پنل سریال‌ها:** گروه‌بندی بر اساس وضعیت (در حال تماشا، برنامه تماشا، رها شده، تکمیل شده) با دکمه‌های ±قسمت و اسلایدر امتیاز (همه HTMX، رندر مجدد پارشال `panel.html`).
- **پنل فیلم‌ها:** وضعیت‌ها بدون «در حال تماشا» (فقط: برنامه تماشا، تکمیل شده، رها شده).
- **پروفایل عمومی (`/account/u/<id>/`):** هر کسی (حتی بدون ورود) می‌تواند لیست‌های پخش کاربر را ببیند؛ در حالت `read_only` دکمه‌های تغییر غیرفعال می‌شوند.

---

## جستجو

فایل: `search/views.py` + `search/templates/search/results.html`

- جستجوی زنده در هدر (`keyup` با تأخیر ۳۰۰ms و HTMX).
- جستجو در: نام سریال، نام فیلم (با `name`, `name_fa`, `name_en`)، نام شخص، و **آیدی IMDb** (از `RemoteId`ها).
- محدودیت‌ها: ۸ مورد در هر گروه، ۵ مورد IMDb.

---

## برترین‌ها (Top 250)

فایل: `top250/views.py` + `top250/rank.py`

- رتبه‌بندی از دو فایل CSV در پوشه `datas/` خوانده می‌شود: `imdb_movies_top250.csv` و `imdb_series_top250.csv`.
- با تطبیق آیدی IMDb بین CSV و جدول `RemoteId`ها، رتبه هر فیلم/سریال پیدا می‌شود (آیتم‌هایی که در DB نیستند نادیده گرفته می‌شوند).
- `SERIES_RANKS` / `MOVIES_RANKS` دیکشنری رتبه‌ها را برای بج «برترین‌ها» در صفحات جزئیات فراهم می‌کنند.
- قالب: تب فیلم/سریال + ردیف‌های رتبه‌بندی شده.

---

## قالب‌های سراسری

### `base.html`

- `lang="fa" dir="rtl"`، فونت وزیر، بلاک‌های `title`, `head`, `body`, `script`.
- قبل از اولین رندر، تم ذخیره‌شده در `localStorage` روی `<html data-theme="...">` اعمال می‌شود (بدون فلش).
- لود همیشگی: `theme.css`, `header.css`, `footer.css`.

### `header.html`

- لوگو، لینک‌های ناوبری (خانه، برترین‌ها، سریال‌ها، فیلم‌ها، لیست‌های من).
- دکمه تغییر تم (تیره/روشن) با ذخیره در `localStorage`.
- جعبه جستجوی HTMX + نمایش نتایج.
- بخش ورود/خروج (با کاربر جاری و دکمه خروج).

### `sidebar.html`

سایدبار ثابت راست با برند «ونتا / سیستم_فعال_01» و آیتم‌های: داشبورد (بدون لینک)، فیلم‌ها، سریال‌ها، لیست پخش، مورد علاقه‌ها، تنظیمات (بدون لینک).

### `footer.html`

فوتر کامل با لینک‌ها، سال جاری شمسی به اعداد فارسی (از `_jalali_year()` با `jdatetime`).

---

## سیستم تم (Theme)

| فایل | نقش |
|---|---|
| `static/scss/theme.scss` | تعریف متغیرهای CSS (`:root` تیره + `[data-theme="light"]` روشن) |
| `static/scss/_var.scss` | تبدیل متغیرهای CSS به متغیرهای Sass (`$primary`, `$background`, ...) + میکسین‌ها |
| `static/scss/*.scss` | استایل هر صفحه با `@use 'var' as *` |

- همه رنگ‌ها به‌صورت CSS Custom Property تعریف شده‌اند تا تغییر تم در زمان اجرا بدون کامپایل مجدد کار کند.
- هر رنگ یک جفت `*-rgb` دارد برای استفاده داخل `rgba()`.
- تم پیش‌فرض «تیره» ترمینالی است: پس‌زمینه `#090B0A`، سبز اصلی `#3DD68C`، سبز ثانویه `#53DBCA`.
- میکسین‌های پرکاربرد: `section-header`, `btn-primary-outline`, `submit-pill`, `modal-panel`, `card-hover`, `surface-card`, `status-dot`, `truncate`, `imdb-badge`.

---

## اسکریپت‌های جمع‌آوری داده

پوشه `scripts/` — وارد کردن داده از **TVDB** (API v4) و **IMDb**:

| اسکریپت | کار |
|---|---|
| `series_crawler.py` | خزش تمام سریال‌های TVDB (آی‌دی ۱ تا ۹۰۰۰۰۰) و ذخیره به `tvdb_data.jsonl.gz` |
| `movies_crawler.py` | خزش فیلم‌های TVDB |
| `import_data.py` | وارد کردن سریال‌ها از JSONL به DB (ژانر، شخص، کاراکتر، تگ) |
| `import_movies.py` | وارد کردن فیلم‌ها با پشتیبانی ادامه‌پذیر (checkpoint) |
| `import_imdb_raitings.py` / `import_imdb_raitings_movies.py` | وارد کردن امتیازهای IMDb |
| `import_movie_images.py` | دریافت تصاویر فیلم‌ها |
| `movie_images_crawler.py` | خزش تصاویر |
| `import_series_status.py` / `series_status_crawler.py` | دریافت وضعیت پخش و تعداد قسمت سریال‌ها |
| `translate_tvdb.py` | ترجمه نام/خلاصه به فارسی با Checkpoint و پشتیبانی ژانرهای ترجمه‌شده |

داده‌های خام در `datas/` ذخیره می‌شوند (`tvdb_data.jsonl.gz`, `tvdb_movies.jsonl.gz`, `imdb_movies_top250.csv` و…).

---

## یادداشت‌های فنی

1. **هشدار امنیتی:** `DEBUG=True` و `ALLOWED_HOSTS=[]` فعلاً برای توسعه است؛ برای انتشار باید تغییر کند.
2. **نام فیلم‌ها:** `name` = انگلیسی، `name_fa` = فارسی، `name_en` = جایگزین انگلیسی. در قالب‌ها اولویت با `name_fa` است (`{{ m.name_fa|default:m.name }}`).
3. **ورود مورد نیاز:** صفحه اصلی، پروفایل و اکشن‌های ردیابی نیازمند ورود هستند؛ صفحات جزئیات و پروفایل عمومی قابل بازدید هستند.
4. **HTMX + Alpine.js:** اکشن‌های ردیابی/نظر/جستجو با HTMX، و تعاملات تب/اسلایدر/پاپ‌آپ با Alpine.js.
5. **قرارداد نام‌گذاری عناوین:** عنوان‌های ترمینالی با آندرلاین نوشته می‌شوند (`ادامه_تماشا`, `برنامه_تماشا`, `پیشنهاد_درام`).
6. **db.sqlite3 خالی در ریشه** برای توسعه است؛ دیتابیس واقعی PostgreSQL است.
7. **Graphify:** خروجی گراف دانش پروژه در `graphify-out/` (پس از هر کامیت به‌روزرسانی می‌شود) — برای پرس‌وجوهای ساختاری مفید است.
