# How to test (local)

См. также `backend/README.md`.

```
cd 04-development/backend
.venv\Scripts\activate
python manage.py test loyalty
python manage.py runserver
```

Касса: cashier1 / devpass  
Админ: admin / devpass  

Чек 1000 → начисление 100 бонусов (10%).  
Списание: в 1С скидку вручную на ту же сумму.

Пароли только для локальной машины. Не production.
