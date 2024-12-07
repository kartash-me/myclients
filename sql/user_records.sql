SELECT
    users.name,
    companies.name,
    branches.name,
    services.title,
    services.price,
    schedules.date,
    schedules.time,
    records.record_id
FROM records
INNER JOIN users ON records.worker = users.user_id
INNER JOIN companies ON records.company = companies.company_id
INNER JOIN branches ON records.branch = branches.branch_id
INNER JOIN services ON records.service = services.service_id
INNER JOIN schedules ON records.schedule = schedules.schedule_id
