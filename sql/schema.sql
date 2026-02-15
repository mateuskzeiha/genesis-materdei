-- Schema base para quando você quiser plugar SQL de verdade

CREATE TABLE appointments (
    lead_id            INT PRIMARY KEY,
    created_date       DATE NOT NULL,
    appointment_date   DATE NULL,

    age                INT,
    is_60_plus         INT,

    channel            VARCHAR(50),
    unit               VARCHAR(100),
    specialty          VARCHAR(100),
    stage              VARCHAR(50),

    response_minutes   INT,
    days_ahead         INT,

    scheduled          INT,
    attended           INT,
    no_show            INT,

    price              DECIMAL(10,2)
);
