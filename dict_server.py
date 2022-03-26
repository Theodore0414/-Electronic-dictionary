from socket import *
import os
import time
import signal
import pymysql
import sys

# 定義需要的全局變量
DICT_TEXT = './dict.txt'

HOST = '0.0.0.0'
PORT = 8000
ADDR = (HOST, PORT)

#流程控制
def main():
    #創建數據庫連接
    db = pymysql.connect(host='localhost', user='hao', password='123456', database='dict')
    
    #創建套接字
    s = socket()
    s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    s.bind(ADDR)
    s.listen(5)
    
    #忽略子進程訊號
    signal.signal(signal.SIGCHLD, signal.SIG_IGN)
    
    while True:
        try:
            c, addr = s.accept()
            print('Connect from', addr)
        except KeyboardInterrupt:
            s.close()
            sys.exit('服務器退出')
        except Exception as e:
            print(e)
            continue
        # 創建子進程
        pid = os.fork()
        if pid == 0:
            s.close()
            do_child(c, db)
        else:
            c.close()
            continue

def do_child(c, db):
    # 循環接收客戶端請求
    while True:
        data = c.recv(128).decode()
        print(c.getpeername(), ':', data)
        if (not data) or data[0] == 'E':
            c.close()
            sys.exit(0)
        if data[0] == 'R':
            do_register(c, db, data)
        elif data[0] == 'L':
            do_login(c, db, data)
        elif data[0] == 'Q':
            do_query(c, db, data)
        elif data[0] == 'H':
            do_hist(c, db, data)
# 登陸
def do_login(c, db, data):
    print('登陸操作')
    l = data.split(' ')
    name = l[1]
    passwd = l[2]
    cursor = db.cursor()
    
    sql = "select * from user where name='%s' and passwd='%s'"%(name, passwd)
    
    cursor.execute(sql)
    r = cursor.fetchone()
    
    if r == None:
        c.send(b'FALL')
    else:
        print("%s登陸成功"%name)
        c.send(b'OK')

# 註冊
def do_register(c, db, data):
    print('註冊操作')
    l = data.split(' ')
    name = l[1]
    passwd = l[2]
    cursor = db.cursor()
    
    sql = "select * from user where name='%s'"%name
    cursor.execute(sql)
    r = cursor.fetchone()
    
    if r != None:
        c.send(b'EXISTS')
        return
    
    # 用戶不存在，插入用戶
    sql = "insert into user (name, passwd) values ('%s', '%s')"%(name, passwd)
    try:
        cursor.execute(sql)
        db.commit()
        c.send(b'OK')
    except:
        db.rollback()
        c.send(b'FALL')
    else:
        print('%s註冊成功'%name)

# 查詞
def do_query(c, db, data):
    print('查找操作')
    l = data.split(' ')
    name = l[1]
    word = l[2]
    cursor = db.cursor()
    
    # 內部函數
    def insert_histroy():
        tm = time.ctime()
        
        sql = 'insert into hist (name, word, time) values("%s", "%s", "%s")'%(name, word, tm)
        
        try:
            cursor.execute(sql)
            db.commit()
        except:
            db.rollback()
    
    # 文本查詢
    try:
        f = open(DICT_TEXT)
    except:
        c.send(b'FALL')
        return
    
    for line in f:
        tmp = line.split(' ')[0]
        if tmp > word:
            c.send(b'FALL')
        elif tmp == word:
            c.send(b'OK')
            time.sleep(0.1)
            c.send(line.encode())
            f.close()
            insert_history()
            return
    c.send(b'FALL')
    f.close()

# 歷史紀錄
def do_hist(c, db, data):
    print('歷史紀錄')
    l = data.split(' ')
    name = l[1]
    cursor = db.cursor()
    
    sql = 'select * from hist where name="%s"'%name
    cursor.execute(sql)
    r = cursor.fetchall()
    if not r:
        c.send(b'FALL')
    else:
        c.send(b'OK')
    
    for i in r:
        time.sleep(0.1)
        # i為一條紀錄，其中Index代表資料庫的各個字段
        msg = "%s    %s    %s"%(i[1], i[2], i[3])
        c.send(msg.encode())
    time.sleep(0.1)
    c.send(b'##')

if __name__ == '__main__':
    main()