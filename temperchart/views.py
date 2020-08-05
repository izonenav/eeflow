import datetime

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.request import Request
import pymssql
from rest_framework.views import APIView


class ChartMixin:
    def __init__(self):
        self.conn: pymssql.Connection = pymssql.connect(host=r"nwws2-022.cafe24.com", user='kcfeed',
                                                        password='kcfeed400401',
                                                        database='kcfeed', charset='utf8')
        self.cursor: pymssql.Cursor = self.conn.cursor()


class ChartData(ChartMixin, APIView):
    def get(self, request: Request):
        startDate = request.query_params.get('startDate', None)
        endDate = request.query_params.get('endDate', None)

        if not startDate and not endDate:
            return Response(data=[], status=status.HTTP_200_OK)

        query = f"select CONVERT(CHAR(10),sztime,23) 일자,CONVERT(CHAR(5),sztime,24) 시분,cchk,round(nsettemp,1) 설정온도, \
                round(ntemp,1) 현재온도,szTime 현재시간 ,datediff(mi,MIN(sztime) over (partition by szdate),sztime) as 가동시간 \
                from   kcfeed.templog \
                where  sztime >= '{startDate}' AND sztime <= '{endDate}' and cchk = 'Y' \
                order  by sztime"

        self.cursor.execute(query)

        result = self.cursor.fetchall()
        self.conn.close()
        return Response(data=result, status=status.HTTP_200_OK)


class CurrentChartData(ChartMixin, APIView):
    def get(self, request: Request):
        now = datetime.datetime.now()
        before_five_min = now - datetime.timedelta(minutes=2)
        query = f"select CONVERT(CHAR(10),sztime,23) 일자,CONVERT(CHAR(5),sztime,24) 시분,cchk,round(nsettemp,1) 설정온도, \
                round(ntemp,1) 현재온도,szTime 현재시간 ,datediff(mi,MIN(sztime) over (partition by szdate),sztime) as 가동시간 \
                from   kcfeed.templog \
                where  sztime >= '{str(before_five_min)[:-4]}' and cchk = 'Y'\
                order  by sztime DESC"

        self.cursor.execute(query)
        result = self.cursor.fetchone()
        self.conn.close()
        return Response(data=result, status=status.HTTP_200_OK)
