SELECT
    concat(users.name, ' ', users.surname) AS main,
    schedule_id, date, time
FROM schedules
INNER JOIN users ON schedules.worker = users.user_id
INNER JOIN branches ON users.company = branches.branch_id
WHERE status = 'available' AND branches.company = ?
ORDER BY main