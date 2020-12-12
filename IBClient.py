#!/usr/env/bin python3
"""
Created on Sat Sep 19 18:50:50 2020

@author: acasa
"""

from datetime import datetime
from threading import Thread
import time

from ibapi.contract import Contract
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.utils import iswrapper

from ibapi.order import Order


class GrowiiClient(EWrapper, EClient):
    ''' Serves as the client and the wrapper '''
    client_id = -1
    address = ''
    port = ''
    
    current_time = []
    historical_data = []  
    # nextValidOrderId = 0
    
    def __init__(self, addr, port, client_id):
        """
        CONSTRUCTOR
        
        Parameters
        ----------
        addr : str
            IP where TWS or IBGateway is running.
        port : int
            Firewall port where is allowed the connection
        client_id : int
            Number beetween 1 and 32. This allow several clients connected to
            a TWS session. This number should be fixed for the admin in the server
            For test, 1 is enought.
            
        """
        self.client_id = client_id
        self.address = addr
        self.port = port
        
        EClient. __init__(self, self)
        EWrapper.__init__(self)

        # Connect to TWS
        self.connect(addr, port, client_id)
        
        # Launch the client thread
        thread = Thread(target=self.run)
        thread.start()
        
        time.sleep(1)
        
    
    def check_conection(self):
        """
        This function checks if the connection with the TWS or IB Gateway 
        application and if it is not available, it reconnects.
        
        """
        retFlag = self.isConnected()
        
        # i = 0 # Falta añadir un máximo número de intentos
        while retFlag != True:
            print('{}    Conexión con el servidor no disponible'.format(datetime.now()))
            self.connect('127.0.0.1', 7497, 1)
            
            # Launch the client thread
            thread = Thread(target=self.run)
            thread.start()
            
            time.sleep(5)
            retFlag = self.isConnected()
        return

    def getCurrentTime(self):
        self.reqCurrentTime()
        time.sleep(0.5)
        return self.current_time



    def getHistoricalData(self, delay, contract, endDateTime, durationStr, barSizeSetting, whatToShow):
        """
        This function allows you to request a historical data from the server. 
        The greater the number of data, the greater the margin delay that must
        be provided to the server. In case the time does not reach, an empty 
        list is returned

        Parameters
        ----------
        contract : Contract
            TWS Contract object
        endDateTime : str
            End date of the request
        durationStr : TYPE
            Lenght of the requested data
        barSizeSetting : TYPE
            Step beetwen data
        whatToShow : TYPE
            Ask, bid o midpoint

        Returns
        -------
        hist_date : float list
            List with requested date
        hist_open : float list
            List with requested open values
        hist_high : float list
            List with requested high values
        hist_low : float list
            List with requested low values
        hist_close : float list
            List with requested close values
        hist_volume : float list
            List with requested volume of operations

        """
        self.historical_data = []
        self.reqHistoricalData(self.client_id, contract, endDateTime, durationStr, barSizeSetting, whatToShow, False, 1, False, [])
        time.sleep(delay)
        
        hist_date = [instant.date for instant in self.historical_data]
        hist_open = [instant.open for instant in self.historical_data]
        hist_high = [instant.high for instant in self.historical_data]
        hist_low = [instant.low for instant in self.historical_data]
        hist_close = [instant.close for instant in self.historical_data]
        hist_volume = [instant.volume for instant in self.historical_data]
        
        return (hist_date, hist_open , hist_high , hist_low , hist_close, hist_volume)
    
  
        
    def setOrder(self , contract , orderType , orderDict):
        """
        This function allows you to set market orders. 
        Consult TWS Api documentation to see how to adjust the parameters. 
        If you want to include types of orders not contemplated, contact 
        the administrator.

        Parameters
        ----------
        contract : Contract
            TWS Contract object
        orderType : str
            Type of order. Only used during the switch selection
        orderDict : Dictionary
            Dictionary that includes all the parameters necessary for the order

        Returns
        -------
        orderID : int
            ID of the launched order

        """
        self.reqIds(-1) # The parameter is always ignored.
        time.sleep(1)
        simplePlaceOid = self.nextValidOrderId  
        
        if orderType == 'market':
            # Dict sample: {'action':'BUY' , 'orderType':'MKT' , 'totalQuantity':100000 , 'transmit':False}
            order = Order()
            order.OrderId = simplePlaceOid
            # order.ClientId(self.client_id)
            order.action = orderDict['action']
            order.orderType = orderDict['orderType']
            order.totalQuantity = orderDict['totalQuantity']
            order.transmit = orderDict['transmit']
        
        elif orderType == 'limit_order':
            # Dict sample: {'action':lmt_action , 'orderType':'LMT' , 'totalQuantity':mainqty , 'lmtPrice': lmt_price , 'parentId':parentID , 'tif':'GTC' , 'transmit':False}
            order = Order()
            order.OrderId = simplePlaceOid+1
            order.action = orderDict['action']
            order.orderType = orderDict['orderType']
            order.totalQuantity = orderDict['totalQuantity']
            order.lmtPrice = orderDict['lmtPrice']
            order.parentId = orderDict['parentId']
            order.tif = orderDict['tif']
            order.transmit = orderDict['transmit']
        
        elif orderType == 'stop_loss':
            # Dict sample: {'action':stop_action , 'orderType':'STP' , 'totalQuantity':mainqty , 'auxPrice': stop_price , 'parentId':parentID , 'tif':'GTC' , 'transmit':True}
            order = Order()
            order.OrderId = simplePlaceOid+2
            order.action = orderDict['action']
            order.orderType = orderDict['orderType']
            order.totalQuantity = orderDict['totalQuantity']
            order.auxPrice = orderDict['auxPrice']
            order.parentId = orderDict['parentId']
            order.tif = orderDict['tif']
            order.transmit = orderDict['transmit']
            
            
        self.placeOrder(simplePlaceOid, contract , order)
        
        return order.OrderId
        
    @iswrapper
    def currentTime(self, cur_time):
        self.current_time = datetime.fromtimestamp(cur_time)
        
    
    @iswrapper
    def historicalData(self, req_id, bar):
        ''' Called in response to reqHistoricalData '''
        self.historical_data.append(bar)
    
            
    @iswrapper
    def historicalDataEnd(self, req_id, start, end):
        ''' Called after historical data has been received '''
        
        print("HistoricalDataEnd. ReqId:", req_id, "from", start, "to", end)
        
    @iswrapper
    def nextValidId(self, orderId):
        ''' Obtain an ID for the order '''
        super().nextValidId(orderId)
        self.nextValidOrderId = orderId
        print("NextValidId:", orderId)
        
    @iswrapper
    def error(self, req_id, code, msg):
        print('Error {}: {}'.format(code, msg))

def main():

    # Create the client and connect to TWS
    print ('Inicio conexion con el servidor')
    client = GrowiiClient('127.0.0.1', 7497, 0)
    print ('Conexion con el servidor completa\n')

    time.sleep(3)

    # Request the current time
    print ('Comprobación tiempo del servidor')
    current_time = client.getCurrentTime()
    print ('El momento actual es {}\n'.format(current_time))

    time.sleep(3)

    #Request data
    con = Contract()
    con.symbol = "EUR"
    con.secType = "CASH"
    con.exchange = "IDEALPRO"
    con.currency = "USD"

    endDateTime = datetime.now().strftime("%Y%m%d, %H:%M:%S")
    durationStr = str(10*60) + " S"
    barSizeSetting = "1 min"
    whatToShow = "MIDPOINT"

    delay = 1

    print('Comprobacion de descarga de datos')
    historical_date, historical_open, historical_high, historical_low, historical_close, historical_volume  = client.getHistoricalData(delay, con, endDateTime, durationStr, barSizeSetting, whatToShow)  
    print('\n')

    time.sleep(3)

    # Disconnect from TWS
    print('Procedo a la desconexión')
    client.disconnect()
    print('Desconexión realizada')


if __name__ == '__main__':
    main()