import psycopg2


class RaceInfo():
    def __init__(self):
        self.race_id = None
        self.no = None
        self.name = None
        self.time = None
        self.kind = None
        self.length = None
        self.direction = None
        self.weather = None
        self.state = None
        self.course = None
        self.etc_1 = None
        self.etc_2 = None
        self.etc_3 = None
        self.etc_4 = None
        self.etc_5 = None
        self.etc_6 = None
        self.etc_7 = None
        self.etc_8 = None


class RaceResult_Row():
    def __init__(self):
        self.race_id = None
        self.rank = None
        self.waku = None
        self.umaban = None
        self.horse_name = None
        self.horse_sex = None
        self.horse_age = None
        self.jockey_weight = None
        self.jockey_name = None
        self.time_1 = None
        self.time_2 = None
        self.odds_1 = None
        self.time_3 = None
        self.passage_rate = None
        self.trainer_place = None
        self.trainer_name = None
        self.horse_weight = None
        self.horse_weight_delta = None
        self.odds_2 = None
        self.horse_id = None
        self.jockey_id = None
        self.trainer_id = None


class RaceResult():
    def __init__(self):
        self.race_id = None
        self.race_info: RaceInfo = None
        self.race_order: list[RaceResult_Row] = None
        self.payout = None
        self.rap_pace = None

    def show_race_result(self):
        print("==== レース情報 ====")
        print(f"{self.race_info.no}R")
        print(f"{self.race_info.name}")
        print(
            f"{self.race_info.kind}{self.race_info.length}m（{self.race_info.direction}）")
        print(f"{self.race_info.time}")
        print(f"{self.race_info.weather}")
        print(f"{self.race_info.state}")
        print(f"{self.race_info.course}")
        print(f"{self.race_info.etc_1}")
        print(f"{self.race_info.etc_2}")
        print(f"{self.race_info.etc_3}")
        print(f"{self.race_info.etc_4}")
        print(f"{self.race_info.etc_5}")
        print(f"{self.race_info.etc_6}")
        print(f"{self.race_info.etc_7}")
        print(f"{self.race_info.etc_8}")
        print("==== レース結果 ====")
        for row in self.race_order:
            print("{:>2} {:>2} {:>2} {}{} {} {} {} {} {} {} {} {} {}{} {}({})".format(
                row.rank,
                row.waku,
                row.umaban,
                row.horse_sex,
                row.horse_age,
                row.jockey_weight,
                row.jockey_name,
                row.time_1,
                row.time_2,
                row.odds_1,
                row.odds_2,
                row.time_3,
                row.passage_rate,
                row.trainer_place,
                row.trainer_name,
                row.horse_weight,
                row.horse_weight_delta
            ))
        print("==== 払い戻し ====")
        print("  単勝：{:>7} {} {}".format(
            self.payout['tansho'][0]['payout'],
            self.payout['tansho'][0]['ninki'],
            self.payout['tansho'][0]['result'],
        ))
        print("  複勝：{:>7} {} {}".format(
            self.payout['fukusho'][0]['payout'],
            self.payout['fukusho'][0]['ninki'],
            self.payout['fukusho'][0]['result'],
        ))
        print("        {:>7} {} {}".format(
            self.payout['fukusho'][1]['payout'],
            self.payout['fukusho'][1]['ninki'],
            self.payout['fukusho'][1]['result'],
        ))
        print("        {:>7} {} {}".format(
            self.payout['fukusho'][2]['payout'],
            self.payout['fukusho'][2]['ninki'],
            self.payout['fukusho'][2]['result'],
        ))
        print("  枠連：{:>7} {} {}".format(
            self.payout['wakuren'][0]['payout'],
            self.payout['wakuren'][0]['ninki'],
            self.payout['wakuren'][0]['result'],
        ))
        print("  馬連：{:>7} {} {}".format(
            self.payout['umaren'][0]['payout'],
            self.payout['umaren'][0]['ninki'],
            self.payout['umaren'][0]['result'],
        ))
        print("ワイド：{:>7} {} {}".format(
            self.payout['wide'][0]['payout'],
            self.payout['wide'][0]['ninki'],
            self.payout['wide'][0]['result'],
        ))
        print("        {:>7} {} {}".format(
            self.payout['wide'][1]['payout'],
            self.payout['wide'][1]['ninki'],
            self.payout['wide'][1]['result'],
        ))
        print("        {:>7} {} {}".format(
            self.payout['wide'][2]['payout'],
            self.payout['wide'][2]['ninki'],
            self.payout['wide'][2]['result'],
        ))
        print("３連複：{:>7} {} {}".format(
            self.payout['fuku3'][0]['payout'],
            self.payout['fuku3'][0]['ninki'],
            self.payout['fuku3'][0]['result'],
        ))
        print("３連単：{:>7} {} {}".format(
            self.payout['tan3'][0]['payout'],
            self.payout['tan3'][0]['ninki'],
            self.payout['tan3'][0]['result'],
        ))
        print("==== ラップタイム ====")
        for col in self.rap_pace:
            print("{:>7} ".format(col['header']), end="")
        print("")
        for col in self.rap_pace:
            print("{:>7} ".format(col['haron_time_1']), end="")
        print("")
        for col in self.rap_pace:
            print("{:>7} ".format(col['haron_time_2']), end="")
        print("")


class RaceResultDAO():
    def __init__(self):
        self.conn = psycopg2.connect(
            "postgresql://user:postgres@keibaai-db-1:5432/keibaai")

    def __del__(self):
        self.conn.close()

    def insert_race_info(self, race_info: RaceInfo) -> None:
        try:
            race_info.no = int(race_info.no)
        except TypeError:
            race_info.no = None
        except ValueError:
            race_info.no = None

        try:
            race_info.length = int(race_info.length)
        except TypeError:
            race_info.length = None
        except ValueError:
            race_info.length = None

        sql = """
        INSERT INTO race_info (
            race_id,    -- varchar(255)     Not Null
            no,         -- integer
            kind,       -- varchar(255)
            length,     -- integer
            direction,  -- varchar(255)
            name,       -- varchar(255)
            start,      -- time
            weather,    -- varchar(255)
            state,      -- varchar(255)
            course,     -- varchar(255)
            etc_1,      -- varchar(255)
            etc_2,      -- varchar(255)
            etc_3,      -- varchar(255)
            etc_4,      -- varchar(255)
            etc_5,      -- varchar(255)
            etc_6,      -- varchar(255)
            etc_7,      -- varchar(255)
            etc_8       -- varchar(255)
        ) VALUES (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s
        )
        """
        with self.conn.cursor() as curs:
            curs.execute(sql, (
                race_info.race_id,
                race_info.no,
                race_info.kind,
                race_info.length,
                race_info.direction,
                race_info.name,
                race_info.time,
                race_info.weather,
                race_info.state,
                race_info.course,
                race_info.etc_1,
                race_info.etc_2,
                race_info.etc_3,
                race_info.etc_4,
                race_info.etc_5,
                race_info.etc_6,
                race_info.etc_7,
                race_info.etc_8,
            ))
        self.conn.commit()

    def insert_race_result(self, row: RaceResult_Row) -> None:
        try:
            row.rank = int(row.rank)
        except ValueError:
            row.rank = None

        try:
            row.waku = int(row.waku)
        except ValueError:
            row.waku = None

        try:
            row.umaban = int(row.umaban)
        except ValueError:
            row.umaban = None

        try:
            row.horse_age = int(row.horse_age)
        except ValueError:
            row.horse_age = None

        try:
            row.jockey_weight = float(row.jockey_weight)
        except ValueError:
            row.jockey_weight = None

        try:
            row.umaban = int(row.umaban)
        except ValueError:
            row.umaban = None

        try:
            row.time_3 = float(row.time_3)
        except ValueError:
            row.time_3 = None

        try:
            row.odds_1 = int(row.odds_1)
        except ValueError:
            row.odds_1 = None

        try:
            row.odds_2 = float(row.odds_2)
        except ValueError:
            row.odds_2 = None

        try:
            row.horse_weight = int(row.horse_weight)
        except ValueError:
            row.horse_weight = None

        try:
            row.horse_weight_delta = int(row.horse_weight_delta)
        except ValueError:
            row.horse_weight_delta = None
        except TypeError:
            row.horse_weight_delta = None

        sql = """
        INSERT INTO race_result (
            race_id,
            rank,
            waku,
            umaban,
            horse_name,
            horse_sex,
            horse_age,
            jockey_weight,
            jockey_name,
            time,
            chakusa,
            popular,
            odds,
            agari,
            passage_rate,
            trainer_place,
            trainer_name,
            horse_weight,
            horse_weight_delta,
            horse_id,
            jockey_id,
            trainer_id
        ) VALUES (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s
        )
        """
        with self.conn.cursor() as curs:
            curs.execute(sql, (
                row.race_id,
                row.rank,
                row.waku,
                row.umaban,
                row.horse_name,
                row.horse_sex,
                row.horse_age,
                row.jockey_weight,
                row.jockey_name,
                row.time_1,
                row.time_2,
                row.odds_1,
                row.odds_2,
                row.time_3,
                row.passage_rate,
                row.trainer_place,
                row.trainer_name,
                row.horse_weight,
                row.horse_weight_delta,
                row.horse_id,
                row.jockey_id,
                row.trainer_id,
            ))
        self.conn.commit()

    def get_horse_id(self):
        sql = "SELECT DISTINCT horse_id FROM race_result"
        with self.conn.cursor() as curs:
            curs.execute(sql)
            rows = curs.fetchall()
        return rows
