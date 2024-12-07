SELECT
    users.name AS Имя,
    surname AS Фамилия,
    gender AS Пол,
    branches.name AS Филиал,
    date_of_birth AS 'Дата рождения',
    phone AS Телефон
FROM users
INNER JOIN branches ON users.company = branches.branch_id
WHERE branches.company = ? AND role = 'worker'
