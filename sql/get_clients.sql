SELECT
    name AS Имя,
    surname AS Фамилия,
    gender AS Пол,
    phone AS Телефон,
    date_of_birth AS 'Дата рождения'
FROM users
WHERE user_id IN (
    SELECT DISTINCT user
    FROM records
    WHERE company = ?
    )