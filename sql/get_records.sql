SELECT
    branches.name AS Филиал,
    concat(worker.name, ' ', worker.surname) AS Сотрудник,
    concat(user.name, ' ', user.surname) AS Клиент,
    records.status AS Статус,
    services.title AS Услуга,
    schedules.date AS Дата,
    schedules.time AS Время,
    services.price AS Стоимость,
    records.comments AS Комментарии
FROM records
INNER JOIN branches ON records.branch = branches.branch_id
INNER JOIN users worker ON records.worker = worker.user_id
INNER JOIN users user ON records.user = user.user_id
INNER JOIN services ON records.service = services.service_id
INNER JOIN schedules ON records.schedule = schedules.schedule_id
