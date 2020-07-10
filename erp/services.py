from datetime import datetime

import cx_Oracle
import os
from cx_Oracle import Connection, Cursor

from eeflow.settings import ORACLE_IP


class OracleService:
    def __init__(self):
        self.con: Connection = self.init_env()
        self.cursor: Cursor = self.con.cursor()

    def init_env(self) -> Connection:
        os.environ["NLS_LANG"] = ".AL32UTF8"
        dsn_tns = cx_Oracle.makedsn(ORACLE_IP, '1521', service_name='KCDB')
        return cx_Oracle.connect(user=r'SYSTEM', password='Kcfeed12#$', dsn=dsn_tns)

    def get_result(self, query: str, columns: list) -> list:
        result: list = []
        self.cursor.execute(query)
        rows: list = self.cursor.fetchall()
        max_len = len(columns) - 1
        for row in rows:
            dict_temp: dict = {}
            for i, column in enumerate(columns):
                column_name: str = list(columns[i].values())[0]
                value = row[i]

                if type(row[i]) == str:
                    value = value.strip()

                if type(row[i]) == datetime:
                    value = value.strftime('%Y-%m-%d')

                dict_temp[column_name] = value

                if max_len == i:
                    result.append(dict_temp)
        return result

    def create_select_query(self, columns: list, table: str, wheres: list) -> str:
        select_query: str = 'select '
        from_query: str = f' from {table} '
        where_query: str = " where 1 = 1 "

        if wheres:
            for where in wheres:
                where_query += f' and {where}'

        for column in columns:
            for k, v in column.items():
                select_query += f'{k} as {v} ,'
        if table == 'var_receipt1':
            return select_query[0:-1] + from_query + where_query + 'order by RPICU, RPSFX'
            # return select_query[0:-1] + from_query + where_query
            # return select_query[0:-1] + from_query + where_query

        return select_query[0:-1] + from_query + where_query + 'order by RPICU, RPDOC'

    def execute_insert_query(self, table: str, columns: list, values: list) -> None:
        assert len(columns) == len(values), 'insert 시 column과 values의 값은 같아야함'
        query: str = f" INSERT INTO {table} "
        column_query: str = '('
        value_query: str = ' VALUES ('

        for column in columns:
            column_query += f'{column},'

        column_query = column_query[0:-1] + ')'

        for value in values:
            value_query += f'{value},'

        value_query = value_query[0:-1] + ')'
        self.cursor.execute(query + column_query + value_query)
        self.con.commit()

    def execute_delete_query(self, table: str, wheres: int) -> None:
        query: str = f" DELETE FROM {table} "
        where_query: str = f" WHERE BATNO = {wheres} "
        self.cursor.execute(query + where_query)
        self.con.commit()

    def execute_update_query(self, query: str) -> None:
        self.cursor.execute(query)
        self.con.commit()

    def get_erp_invoices_todo_count(self, users: str):
        query = f" select sum(nvl(cnt1,0)) cnt1,sum(nvl(cnt2,0)) cnt2,sum(nvl(cnt3,0)) cnt3," \
                f"sum(nvl(cnt4,0)) cnt4,sum(nvl(cnt5,0)) cnt5 \
                from \
                     (select decode(no,'1',cnt) cnt1,decode(no,'2',cnt) cnt2,decode(no,'3',cnt) cnt3,decode(no,'4',cnt)" \
                f" cnt4,decode(no,'5',cnt) cnt5 \
                      from \
                           ( \
                            select '1' no,a.rptorg,count(*) cnt \
                            from \
                                   (select distinct rptorg,rpicu \
                                    from   proddta.f0411 \
                                    where  rppost <> 'D' \
                                    and    rptorg in ({users}) \
                                    and    not exists (select batno from kcfeed.eabatno kkk where kkk.batno = rpicu)) a \
                            group  by rptorg \
                            union all \
                            select '2' no,a.rmtorg rptorg,count(*) cnt \
                            from \
                                   (select distinct rmtorg,rmicu \
                                    from   proddta.f0413 \
                                    where  rmistp <> 'D' \
                                    and    rmtorg in ({users}) \
                                    and    not exists (select batno from kcfeed.eabatno kkk where kkk.batno = rmicu)) a \
                            group  by rmtorg \
                            union all \
                            select '3' no,a.rptorg,nvl(count(*),0) cnt \
                            from \
                                   (select distinct rptorg,rpicu \
                                    from   proddta.f03b11 \
                                    where  rppost <> 'D' \
                                    and    rptorg in ({users}) \
                                    and    not exists (select batno from kcfeed.eabatno kkk where kkk.batno = rpicu) \
                                    and    not exists(select glicu from proddta.f0911 where glicu = rpicu " \
                f"and glpdct = '  ' and gldcto = 'SO' " \
                f"and gldgj >= (to_number(to_char(sysdate,'yyddd')) + 100000) -30)) a \
                             group  by rptorg \
                             union all \
                                select '4' no,a.rztorg rptorg,count(*) cnt \
                                from \
                                (select distinct rztorg, rzicu \
                                from proddta.f03b14 \
                                where  rzpost <> 'D' \
                                and rztorg in ({users}) \
                                and not exists(select batno from kcfeed.eabatno kkk where kkk.batno = rzicu) \
                                and rzicu not in (select distinct rzicu from proddta.f03b14 where rzaid = '00000055') \
                                and lpad(rzan8, 6, '0') | | rzaid not in (select lpad(aban8, '0', 6) | | '00000012' \
                                from proddta.f0101 where \
                                abat1 = 'C' and abmcu >= '       13310' and abmcu <= '       14250')) a \
                                group by rztorg \
                             union all \
                             select '5' no,a.gltorg rptorg,count(*) cnt \
                             from \
                                    (select distinct gltorg,glicu \
                                     from   proddta.f0911 \
                                     where  glpost <> 'P' \
                                     and    gllt = 'AA' \
                                     and    glicut = 'G' \
                                     and    gltorg in ({users}) \
                                     and    not exists (select batno from kcfeed.eabatno kkk where kkk.batno = glicu)) a \
                             group  by gltorg \
                            ) a \
                        )b "
        self.cursor.execute(query)
        rows: list = self.cursor.fetchall()
        return rows[0]
