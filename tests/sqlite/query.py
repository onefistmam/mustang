
import sqlite3



def getXpr():
    # conn = sqlite3.connect('../../order_book.db')
    # c = conn.cursor()
    # print ("Opened database successfully");
    #
    # cursor = c.execute("SELECT * FROM binance_xrpbtc_order;")
    # for row in cursor:
    #    print(row)
    # conn.close()
    table_name = "skk-we-wqqw"
    print(table_name)
    if '-' in table_name:
        table_name = table_name.replace('-', '_')
    print(table_name)

if __name__ == '__main__':
    getXpr()
