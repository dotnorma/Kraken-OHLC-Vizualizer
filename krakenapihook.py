# Alexander Dominguez [dotnorma] Contact: androidaleccc@gmail.com
# The purpose of this project is to show proficiency in various skills for my portfolio. 
# The application queries Kraken APIs and parses the returned json objects for OHCL data (open, high, low, close) and ticker information.
# The data is then charted for the chosen interval using matplotlib libraries with some basic exception handling.
# Mouse input stream is captured to display a tooltip for the appropriate candle.

import requests
import tkinter as gui
from tkinter import ttk as gui2
import time
import mplfinance as mplf
import matplotlib.backends.backend_tkagg as mattk
import pandas as pd

class KrakenPriceGet:
#Unix timestamps less interval in seconds; constants needed for later functions
    oneday = (int(time.time()) - 86400) 
    oneweek = (int(time.time()) - 604800)
    onemonth = (int(time.time()) - 2592000)
    oneyear = (int(time.time()) - 31536000)
#Style parameters for the mpl candle chart 
    market_colors = mplf.make_marketcolors(up='#08D9D6', down='#FF2E63', edge='inherit', wick="inherit", volume='#252A34')
    chartstyl = mplf.make_mpf_style(
    marketcolors = market_colors,
    base_mpf_style='binance',
    y_on_right=False, 
    facecolor="#DBE2EF",     
    edgecolor="#112D4E",
    rc={
        'font.family': 'Calibri',
        'font.size': 10,
        'axes.labelcolor': '#112D4E',
        'xtick.color': '#112D4E',
        'ytick.color': '#112D4E',
        'text.color': '#112D4E'
    })

#Set up user interface with tkinter and pass in main window, constructed in vertically descending order
    def __init__(self, maingui):
        #Setting up frames and grid a bit
        self.maingui = maingui
        self.maingui.title("Cryptocurrency Price Charting Portfolio")
        self.maingui.geometry("700x600")
        self.maingui.columnconfigure(0, weight=1) #mainframe wil resize with window
        self.maingui.rowconfigure(0, weight=1)
        self.pystyle = gui2.Style()
        self.pystyle.configure("style1.TFrame", background="#EAEAEA") #Color of main frame
        self.mainframe = gui2.Frame(maingui, style="style1.TFrame") 
        self.mainframe.grid(column=0, row=0, sticky="NSEW")
        self.mainframe.rowconfigure(3, weight=1)
        self.mainframe.columnconfigure(0, weight=1)
        self.buttonframe = gui2.Frame(self.mainframe, style="style1.TFrame")
        self.buttonframe.grid(columnspan=2, row=4, padx="10", pady="10", sticky="NE")
        self.labelframeborder = gui2.Frame(self.mainframe, style="style00.TFrame", padding="2")
        self.labelframeborder.grid(columnspan=3, row=1, sticky="NSEW")
        self.labelframeborder.columnconfigure(0, weight=1)
        self.pystyle.configure("style0.TFrame", background="#AED6CF") #Color of label frame
        self.labelframe = gui2.Frame(self.labelframeborder, style="style0.TFrame") 
        self.pystyle.configure("style00.TFrame", background="#112D4E") #Color of label frame
        self.labelframe.grid(column=0, row=0, sticky="NSEW")
        self.labelframe.columnconfigure(3, weight=1)

        #Setting up variuous UI Variables
        self.dropdownvar = gui.StringVar()
        self.dropdownvar.set("XBT")
        self.assetlabelvar = gui.StringVar()
        self.assetlabelvar.set("Bitcoin")
        self.pricelabelvar = gui.StringVar()
        self.changeovertimevar = gui.StringVar()
        self.refreshimage = gui.PhotoImage(file=r"refresh.png")
        self.changeovertimevar.set("Choose an asset to get started...")
        self.font_dic = {'family': 'Calibri', 'size': 10, 'color': "#112D4E", 'weight': "bold" }
        self.font_dic_tick = {'family': 'Calibri', 'size': 10}
        self.periodglobal = 60

        #UI Labels
        gui2.Label(self.labelframe, textvariable=self.assetlabelvar, font=("Calibri", 24, "bold"), foreground="#112D4E", background="#AED6CF").grid(column=0, row=0, padx="10", sticky="WN")
        gui2.Label(self.labelframe, textvariable=self.pricelabelvar, font=("Calibri", 16, "bold"), background="#AED6CF", foreground="#112D4E").grid(column=0, row=1, padx="10", sticky="WN")
        self.changelabel = gui2.Label(self.labelframe, textvariable=self.changeovertimevar, font=("Calibri", 10, "italic"), foreground="#112D4E", background="#AED6CF")
        self.changelabel.grid(column=0, row=2, padx="10", sticky="WN")
        #UI Buttons
        self.button24 = gui2.Button(self.buttonframe, text="24h", command=lambda: self.interval_button(self.oneday))
        self.button24.grid(column=0, row=4, sticky="W")
        self.button7d = gui2.Button(self.buttonframe, text="1w", command=lambda: self.interval_button(self.oneweek))
        self.button7d.grid(column=1, row=4)
        self.button1m = gui2.Button(self.buttonframe, text="1m", command=lambda: self.interval_button(self.onemonth))
        self.button1m.grid(column=2, row=4)
        self.button1y = gui2.Button(self.buttonframe, text="1y", command=lambda: self.interval_button(self.oneyear))
        self.button1y.grid(column=3, row=4)
        self.refresh = gui2.Button(self.labelframe, image=self.refreshimage, command=lambda: self.refresh_button())
        self.refresh.grid(column=3, row=2, sticky="E", padx="10", pady="5")

        self.dropdown = gui2.Combobox(self.labelframe, textvariable=self.dropdownvar, state="readonly", width=40)
        self.dropdown.grid(column=3, row=0, pady=(5,5), padx="10", sticky="NE")

        self.droplist = []
        self.pricekey = {}
        #Binding dropdown choice here
        self.dropdown.bind('<<ComboboxSelected>>', self.combo_selected) 

        self.request_populate()

#Pull and parse datafeeds from Kraken API as json objects
    def request_populate(self):

        
        datafeed = requests.get('https://api.kraken.com/0/public/Ticker')
        namefeed = requests.get('https://api.kraken.com/0/public/AssetPairs')
        datajson = datafeed.json()
        namejson = namefeed.json() 
        dataresult = datajson['result']

        self.droplistset = set()
        self.reference_dic = {}
    
        if int(datafeed.status_code) > 299: #http codes above 299 are bad responses - very basic error handling
            print('HTTP Status Error #' + str(datafeed.status_code))
        else:
#Dictionary key C holds last trade closed, position 0 holds value. Also must parse out USD pairings and strip duplicates
            for crypto_pair, crypto_price in dataresult.items():
                market_price = crypto_price["c"][0] 
                if ("USDC" in crypto_pair[-4:] or "USDT" in crypto_pair[-4:] or "USD" in crypto_pair[-3:]) and (crypto_pair in namejson['result']):
                    altname = namejson['result'][crypto_pair]["altname"]
                    if crypto_pair[-3:] != "USD": 
                        self.droplistset.add(altname[:-4])
                        self.reference_dic[altname[:-4]] = crypto_pair # Reference dictionary as a quick fix for later use
                        self.pricekey.update({altname[:-4]: market_price}) 
                    elif crypto_pair[-3:] == "USD":
                        self.droplistset.add(altname[:-3])
                        self.reference_dic[altname[:-3]] = crypto_pair
                        self.pricekey.update({altname[:-3]: market_price})
                    
        self.droplist = sorted(list(self.droplistset))  #Sorting alphabetically
        self.dropdown['values'] = self.droplist

        self.historical_price("XXBTZUSD", 60, self.oneday)  #Pulling btc by default
        self.pricelabelvar.set(f"${self.pricekey["XBT"]}")

#Called on user dropbox selection
    def combo_selected(self, event): 
        for crypto_pair, crypto_price in self.pricekey.items():
            if crypto_pair == self.dropdownvar.get():
                self.pricelabelvar.set(f"${crypto_price}")
                self.historical_price(self.reference_dic[self.dropdownvar.get()], 60, self.oneday)  #This is why we need the reference dictionary: asset pair vs truncated asset name for user display
                self.assetlabelvar.set(self.dropdownvar.get())

#Pulls OHCL data (open, high, low, close) at fixed intevals
    def historical_price(self, asset, interval, since): 
        parameters = {                                      
            'pair': str(asset),
            'interval': int(interval),
            'since': int(since)
            }
        try:  #again, some pretty basic error handling, not 100% by any means
            tryforresponse = requests.get('https://api.kraken.com/0/public/OHLC', params=parameters, timeout=10)
            tryforresponse.raise_for_status()
            price_history = tryforresponse.json()
        except requests.exceptions.RequestException as e: #pull the exception to print for debug
            print(f"Couldnt connect to Kraken API: {e}")
            self.changeovertimevar.set("Error: Couldn't connect to Kraken API") #bit of the old polish

        if not price_history["result"][asset]:
            self.changeovertimevar.set("No data available for this period.") #check for empty list data
            
        
        columnsohcl = ['timestamp', 'open', 'high', 'low', 'close', 'vwap', 'volume', 'count']
        self.dfohcl = pd.DataFrame(data=price_history['result'][asset], columns=columnsohcl) #opening panda dataframe
        self.dfohcl['timestamp'] = pd.to_datetime(self.dfohcl['timestamp'], unit='s') #converting unix time to dattime object
        self.dfohcl = self.dfohcl.set_index('timestamp') #index dataframe by timestamp aka chronological
        self.dfohcl['open'] = self.dfohcl['open'].astype(float)
        self.dfohcl['high'] = self.dfohcl['high'].astype(float)
        self.dfohcl['low'] = self.dfohcl['low'].astype(float)
        self.dfohcl['close'] = self.dfohcl['close'].astype(float)
        self.dfohcl['vwap'] = self.dfohcl['vwap'].astype(float)
        self.dfohcl['volume'] = self.dfohcl['volume'].astype(float)

        if hasattr(self, 'inline_tk'):
            self.inline_tk.get_tk_widget().destroy() #clear existing chart
        
        self.inline_chart, axlist = mplf.plot(self.dfohcl, type='candle', returnfig=True, style=self.chartstyl)
        self.axisofevil = axlist[0] 

        self.inline_tk = mattk.FigureCanvasTkAgg(figure=self.inline_chart, master=self.mainframe) #convert our figure to a widget for ttk/tkinter
        self.inline_tk.get_tk_widget().grid(row=3, columnspan=2, pady="5", padx="10", sticky="NSEW")
        self.inline_tk.draw()
        self.pre_hover_event(self.inline_chart, self.axisofevil) #setup for hover tooltip
#Logic for the percent change label color change (aka down or up over time period)
        open_price = self.dfohcl['open'].iloc[0]
        close_price = self.dfohcl['close'].iloc[-1]
        if open_price != 0:
            price_change = ((close_price - open_price) / open_price) * 100
            if price_change < 0:
                self.changelabel.config(foreground="#FF2E63")
                price_change_text = f"Change: {price_change:.2f}%"
            elif price_change > 0:
                self.changelabel.config(foreground="#3A6F43")
                price_change_text = f"Change: {price_change:.2f}%"
        else:
            price_change_text = "Change: N/A" # avoiding division by zero
        self.changeovertimevar.set(price_change_text)
        

#Calls historical price for new chosen interval
    def interval_button(self, interval):
        if interval == self.oneyear:
            self.historical_price(self.reference_dic[self.dropdownvar.get()], 10080, interval)
            self.periodglobal = "365" #used for refresh button, serves as a lazy memory of last choice
        elif interval == self.onemonth:
            self.historical_price(self.reference_dic[self.dropdownvar.get()], 1440, interval)
            self.periodglobal = "30"
        elif interval == self.oneweek:
            self.historical_price(self.reference_dic[self.dropdownvar.get()], 240, interval)
            self.periodglobal = "7"
        else:
            self.historical_price(self.reference_dic[self.dropdownvar.get()], 60, interval)
            self.periodglobal = "1"
#Added in a refresh button at the last minute
    def refresh_button(self):
        if self.periodglobal == "365":
            self.interval_button(self.oneyear)
        elif self.periodglobal == "30":
            self.interval_button(self.onemonth)
        elif self.periodglobal == "7":
            self.interval_button(self.oneweek)
        else:
            self.interval_button(self.oneday)
#Creating a hidden tooltip for the on_hover function to use later
    def pre_hover_event(self, inline_chart, axisofevil):
        self.annotay = axisofevil.annotate("",
        xy=(0,0), 
        xytext=(20, 20), 
        textcoords="offset points", 
        bbox=dict(boxstyle="round", 
        fc="w"), 
        arrowprops=dict(arrowstyle="->"))
        self.annotay.set_visible(False)
        self.inline_chart.canvas.mpl_connect("motion_notify_event", self.on_hover) #mpl provides convienent 

    def on_hover(self, event):
        if not event.inaxes or event.xdata is None: #if the mouse is NOT in chart then stay invisible
            if self.annotay.get_visible():
                self.annotay.set_visible(False)
                self.inline_chart.canvas.draw_idle() 
            return

        idx = int(round(event.xdata)) #get x cordinates of mouse and round to closest data point

        if idx < 0 or idx >= len(self.dfohcl): 
            if self.annotay.get_visible():
                self.annotay.set_visible(False)
                self.inline_chart.canvas.draw_idle() #required for to redraw
            return

        data_point = self.dfohcl.iloc[idx]

        x = data_point.name
        open_price = data_point['open']
        high_price = data_point['high']
        low_price = data_point['low']
        close_price = data_point['close']

        text_content = (
        f"Date: {x.strftime('%Y-%m-%d %H:%M')}\n"
        f"Open: ${open_price:.2f}\n"
        f"High: ${high_price:.2f}\n"
        f"Low: ${low_price:.2f}\n"
        f"Close: ${close_price:.2f}"
        )
        self.annotay.xy = (idx, close_price)
        self.annotay.set_text(text_content)
        self.annotay.set_visible(True)

        self.inline_chart.canvas.draw_idle()



#Check if this is an import or not
if __name__ == "__main__": 
    maingui = gui.Tk() 
    main = KrakenPriceGet(maingui) 
    maingui.mainloop()


