# Electronic-dictionary
> mysql + python(tcp)
## dict_client.py
* 註冊
* 登陸
  * query : 查詢單詞
* 退出
* 提供歷史紀錄查詢
## dict_server.py
* 接受 client 端的 註冊、登陸、查詢、退出 請求
* 使用 pymysql
