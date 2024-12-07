SELECT
    concat(users.name, ' ', users.surname) AS Клиент,
    records.status AS Статус,
    services.title AS Услуга,
    schedules.date AS Дата,
    schedules.time AS Время,
    services.price AS Стоимость,
    records.comments AS Комментарии
FROM records
INNER JOIN users ON records.user = users.user_id
INNER JOIN services ON records.service = services.service_id
INNER JOIN schedules ON records.schedule = schedules.schedule_id
