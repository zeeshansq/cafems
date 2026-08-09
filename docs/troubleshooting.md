# CafeMS — Troubleshooting & FAQ Guide

A quick reference guide for common issues, diagnostics, and fix commands.

---

## 1. Celery Worker / Redis Connection Issues

### Symptom: `Error 10061 connecting to localhost:6379. Connection refused.`
**Cause**: Redis server is not running locally.
**Diagnostic Command**:
```powershell
Test-NetConnection -ComputerName localhost -Port 6379
```
**Fix**: Start Redis service or Docker container:
```powershell
docker run -d -p 6379:6379 redis:alpine
```

### Symptom: Scheduled tasks (Celery Beat) not triggering
**Fix**: Ensure Celery Beat is started with the Django Database Scheduler:
```powershell
celery -A cafems beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

---

## 2. Django System Check Errors

### Symptom: `NameError` or `ImportError` on server startup
**Diagnostic Command**:
```powershell
python manage.py check --settings=cafems.settings.development
```
**Fix**: Inspect tracebacks. Common issues include unimported generic views (`TemplateView`) or role mixins (`CommitteeRequiredMixin`).

---

## 3. Database Migration Errors

### Symptom: Unapplied migrations or column missing errors
**Fix Commands**:
```powershell
python manage.py makemigrations
python manage.py migrate --settings=cafems.settings.development
```

---

## 4. Static Files & Offline Fonts 404

### Symptom: Icons or Inter font failing to load or rendering fallback browser font
**Diagnostic**: Check browser console for 404 on `/static/fonts/` or `/static/icons/`.
**Fix Command**:
```powershell
python manage.py collectstatic --noinput
```

---

## 5. Timezone & Cutoff Logic Verification

### Symptom: Request cutoff failing unexpectedly
**Diagnostic Command**: Run Django shell to inspect current PKT time vs cutoff:
```powershell
python manage.py shell -c "from apps.core.utils import get_now_pkt, is_before_cutoff; import datetime; print('Now PKT:', get_now_pkt()); print('Tomorrow before cutoff?:', is_before_cutoff(datetime.date.today() + datetime.timedelta(days=1)))"
```
