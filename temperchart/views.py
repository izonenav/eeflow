from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.request import Request
import pymssql


@api_view(['GET'])
def get_chart_data(request: Request) -> Response:
    startDate = request.query_params.get('startDate', None)
    endDate = request.query_params.get('endDate', None)

    if not startDate and not endDate:
        return Response(data=[], status=status.HTTP_200_OK)

    conn: pymssql.Connection = pymssql.connect(host=r"nwws2-022.cafe24.com", user='kcfeed', password='kcfeed400401',
                                               database='kcfeed', charset='utf8')
    query = f"select CONVERT(CHAR(10),sztime,23) 일자,CONVERT(CHAR(5),sztime,24) 시분,cchk,round(nsettemp,1) 설정온도, \
            round(ntemp,1) 현재온도,szTime 현재시간 ,datediff(mi,MIN(sztime) over (partition by szdate),sztime) as 가동시간 \
            from   kcfeed.templog \
            where  sztime >= '{startDate}' AND sztime <= '{endDate}' \
            order  by sztime"

    cursor: pymssql.Cursor = conn.cursor()
    cursor.execute(query)

    # 데이타 하나씩 Fetch하여 출력
    result = cursor.fetchall()
    conn.close()
    return Response(data=result, status=status.HTTP_200_OK)
