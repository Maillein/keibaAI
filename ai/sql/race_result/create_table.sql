CREATe TABLE IF NOT EXISTS race_info(
            race_id     varchar(255)     Not Null,
            no          integer,
            kind        varchar(255),
            length      integer,
            direction   varchar(255),
            name        varchar(255),
            start       time,
            weather     varchar(255),
            state       varchar(255),
            course      varchar(255),
            etc_1       varchar(255),
            etc_2       varchar(255),
            etc_3       varchar(255),
            etc_4       varchar(255),
            etc_5       varchar(255),
            etc_6       varchar(255),
            etc_7       varchar(255),
            etc_8       varchar(255)
)

CREATE TABLE IF NOT EXISTS race_result(
    race_id             varchar(128)     Not Null,
    rank                integer,
    waku                integer,
    umaban              integer,
    horse_name          varchar(128),
    horse_sex           char(1),
    horse_age           integer,
    jockey_weight       decimal,
    jockey_name         varchar(128),
    time                varchar(128),
    chakusa             varchar(128),
    popular             integer,
    odds                decimal,
    agari               decimal,
    passage_rate        varchar(128),
    trainer_place       varchar(128),
    trainer_name        varchar(128),
    horse_weight        integer,
    horse_weight_delta  integer,
    horse_id            varchar(128),
    jockey_id           varchar(128),
    trainer_id          varchar(128)
)
