import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from tkinter import filedialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

class TradingApp(ttk.Frame): # class is extension of a tkinter frame
    def __init__(self, master_window): # main setup
        super().__init__(master_window)
        self.pack(fill=BOTH, expand=YES)
        self.colors = master_window.style.colors

        self.labels = {} # dictionary to store labels that need updating


        # Generate stocks section frame
        self.stock1_name = ttk.StringVar(value="Enter ticker") # for storing stock 1 name / placeholer text
        self.stock2_name = ttk.StringVar(value="Enter ticker") # for storing stock 2 name / placeholer text
        self.file_path1 = ttk.StringVar() # stores stock 1 file path
        self.file_path2 = ttk.StringVar() # stores stock 2 file path

        stocks_frame = ttk.Frame(self, width=370, height=170)
        stocks_frame.grid(row=0, column=0, padx=40, pady=40, sticky="nw")

        self.create_stock_widget(stocks_frame, self.stock1_name, 0, self.file_path1)
        self.create_stock_widget(stocks_frame, self.stock2_name, 1, self.file_path2)


        # Generate graphs section
        self.fig1 = None # Strategy plot
        self.fig2 = None # Portfolio plot
        self.analysis_graph = None # Strategy graph
        self.portfolio_graph = None # Portfolio graph
        self.analysis_toolbar = None
        self.portfolio_toolbar = None

        graphs_frame = ttk.Frame(self, width=720, height=940, relief="solid") # graphs frame
        graphs_frame.grid(row=0, column=2, sticky="e", padx = 10, pady=40, rowspan=4)
        graphs_frame.grid_propagate(False)


        # Generate Test/Reset buttons
        self.create_submit_reset(graphs_frame) # pass graphs frame to be used in graph creation function


        # Generate stats section
        self.correlation = ttk.DoubleVar() # variable for the calculated correlation between the two stocks
        self.num_stdevs = ttk.DoubleVar(value=1.5) # number of standard deviations for trade entry/exit threshold
        self.capital = ttk.DoubleVar(value=10000) # starting capital amount
        self.order_size= ttk.IntVar(value=10) # number of stocks to buy/sell for each trade
        self.num_trades = ttk.IntVar(value=0) # number of trades taken during testing
        self.sharpe_ratio = ttk.DoubleVar()
        self.return_pct = ttk.DoubleVar()

        self.create_stats()


        # Generate settings section
        self.threshold_setting = ttk.BooleanVar(value=False) # True = show stdev thresholds, False = don't
        self.mean_setting = ttk.BooleanVar(value=False) # True = show stocks mean prices, False = don't
        self.signal_setting = ttk.BooleanVar(value=False) # True = show trade entries and exits, False = don't
        
        self.create_settings()


    def create_stock_widget(self, frame, stock_name, widget_number, file_path_var):
        """
        Creates widget for inputing stock name and file path and returns it
        Parameters:
            stock_name (strVar): variable holding name of the stock user inputs
            widget_number (int): starting at 0, the number of widgets created, used for labels and ordering grid layout
            file_path (str): the file path collected when user chooses file from folder
        """

        # Create label
        stock_label = ttk.Label(master=frame, text=f"Stock {widget_number+1}", foreground="white", font=("Helvetica Neue", 20))
        stock_label.grid(row=0, column=widget_number, sticky="nw", padx=10, pady=5)
        
        stock_name_input = ttk.Entry(master=frame, textvariable = stock_name, foreground="gray")
        stock_name_input.grid(row=1, column=widget_number, padx=10, pady=5)

        def on_entry_click(event):
            """
            Clears the default text of stock_name_input field when user clicks and changes colour
            """
            if stock_name_input.get() == "Enter ticker":
                stock_name_input.delete(0, ttk.END) # removes placeholder text
                stock_name_input.config(foreground="") # changes text colour

        def on_focus_out(event):
            """
            Restore default text if stock_name_input field is empty
            """
            if stock_name_input.get() == "":
                stock_name_input.insert(0, "Enter ticker") # set placeholder text
                stock_name_input.config(foreground="gray") # set placeholder font colour
            
        # Bind events for stock name entry field
        stock_name_input.bind("<FocusIn>", on_entry_click)
        stock_name_input.bind("<FocusOut>", on_focus_out)

        # File input
        def open_file(file_path_var):
            file_path = filedialog.askopenfilename(title="Select File", filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")])
            if file_path:
                file_label.config(text=f"File {widget_number+1}: {file_path}")
                file_path_var.set(file_path)
        
        file_btn = ttk.Button(frame, text="Select File", bootstyle="outline", command=lambda: open_file(file_path_var)) # use lambda to pass file path parameter without executing the open file function immediatly
        file_btn.grid(row=2, column=widget_number, pady=5)

        file_label = ttk.Label(frame, text=f"File {widget_number+1}: None selected", foreground="#461a8a", wraplength=200, justify="left", )
        file_label.grid(row=3, column=widget_number, pady=5)
        self.labels[f"file{widget_number+1}"] = file_label


    def analyze_stocks(self, stock1_name: str, file_path1: str, stock2_name: str, file_path2: str):
        """
        Takes the two stocks file locations and performs analysis, returning statistics and graphs.
        Uses format from NASDAQ
        """
        # Read and clean stock1 data
        stock1_df = pd.read_csv(file_path1, usecols = ["Date", "Close/Last"])
        stock1_df["Close/Last"] = stock1_df["Close/Last"].replace({"\\$": ""}, regex=True)  # Remove '$' symbol
        stock1_df["Close/Last"] = pd.to_numeric(stock1_df["Close/Last"], errors="coerce")  # Convert to numbers

        # Read and clean stock2 data
        stock2_df = pd.read_csv(file_path2, usecols = ["Date", "Close/Last"])
        stock2_df["Close/Last"] = stock2_df["Close/Last"].replace({"\\$": ""}, regex=True)  # Remove '$' symbol
        stock2_df["Close/Last"] = pd.to_numeric(stock2_df["Close/Last"], errors="coerce")  # Convert to numbers

        # Merge into one df
        stock1_price_col = f"{self.stock1_name.get()} Price" # the name of the column containing the historical prices of stock 1
        stock2_price_col = f"{self.stock2_name.get()} Price" # the name of the column containing the historical prices of stock 2

        df = pd.merge(stock1_df, stock2_df, on = "Date", how = "inner")
        df.rename(columns={"Close/Last_x": stock1_price_col, "Close/Last_y": stock2_price_col}, inplace = True)
        df = df.iloc[::-1] # Sort from oldest to newest

        df["Spread"] = abs(df[stock1_price_col] - df[stock2_price_col]) # calculate spreads column

        # Calculate statistics
        self.correlation = df[stock1_price_col].corr(df[stock2_price_col]) # correlation betwen stock1 and stock2

        stock1_mean_price = df[stock1_price_col].mean() # historical mean price of stock1
        stock2_mean_price = df[stock2_price_col].mean() # historical mean price of stock2

        mean_spread = df["Spread"].mean() # historical mean spread
        spread_stdev = df["Spread"].std() # calculate standard deviation
        upper_threshold = mean_spread + (self.num_stdevs.get() * spread_stdev)
        lower_threshold = mean_spread - (self.num_stdevs.get() * spread_stdev)


        # Simulate trades
        capital = self.capital.get()
        order_size = self.order_size.get()
        num_trades = self.num_trades.get()
        trade_active = 0 # 0 = not in trade, -1 = trade on lower, 1 = trade on upper
        stock1_position = 0 # -1 is short, 1 is long
        stock2_position = 0 # use enum?

        for index, row in df.iterrows(): # iterate through each day
            # Open trades
            if trade_active == 0:
                if row["Spread"] > upper_threshold: # spread is above -> buy Pep, short KO
                    stock1_position = -1
                    capital += row[stock1_price_col] * order_size

                    stock2_position = 1
                    capital -= row[stock2_price_col] * order_size

                    trade_active = 1
                    df.loc[index, "Entries"] = df.loc[index, "Spread"]
            
                elif row["Spread"] < lower_threshold: # spread is below -> buy KO, short PEP
                    stock1_position = 1
                    capital -= row[stock1_price_col] * order_size

                    stock2_position = -1
                    capital += row[stock2_price_col] * order_size

                    trade_active = -1
                    df.loc[index, "Entries"] = df.loc[index, "Spread"]
            
            # Close trades
            elif trade_active == -1 and row["Spread"] > lower_threshold:
                stock1_position = 0
                capital += row[stock1_price_col] * order_size # sell

                stock2_position = 0
                capital -= row[stock2_price_col] * order_size # buy to cover

                trade_active = 0
                num_trades += 1
                df.loc[index, "Exits"] = df.loc[index, "Spread"]

            elif trade_active == 1 and row["Spread"] < upper_threshold:
                stock1_position = 0
                capital -= row[stock1_price_col] * order_size # buy to cover

                stock2_position = 0
                capital += row[stock2_price_col] * order_size # sell

                trade_active = 0
                num_trades += 1
                df.loc[index, "Exits"] = df.loc[index, "Spread"]

            # Get portfolio value --> cash + holdings
            holdings_value = 0
            if stock1_position == 1:
                holdings_value = row[stock1_price_col] * order_size

            elif stock2_position == 1:
                holdings_value = row[stock2_price_col] * order_size

            df.loc[index, "Portfolio Value"] = capital + holdings_value


        # Calculate Performance
        print("trade active at end?: " + str(trade_active)) # flag if trade still active at end of simulation

        final_value = df["Portfolio Value"].iloc[-1]

        self.return_pct = (final_value - 10000) / 10000 * 100

        self.sharpe_ratio = df["Portfolio Value"].pct_change(fill_method=None).mean() / df["Portfolio Value"].pct_change(fill_method=None).std()

        self.num_trades.set(num_trades) # set with updated value


        # Update rcParams to set all text colours to white
        plt.rcParams.update({
            "figure.facecolor": "#190831",
            "axes.facecolor": "#190831",
            "legend.facecolor": "#190831",
            "text.color": "white",
            "axes.labelcolor": "white",
            "xtick.color": "white",
            "ytick.color": "white",
            "axes.titlecolor": "white",
            "legend.edgecolor": "white",
            "font.size": 8
        })


        # Graph historical prices and spread
        self.fig1, ax1 = plt.subplots(figsize=(7, 4))
        ax1.plot(df["Date"], df[stock1_price_col], linestyle = "-", label=stock1_price_col, color="darkorange", marker=None)
        ax1.plot(df["Date"], df[stock2_price_col], linestyle = "--", label=stock2_price_col, color="dodgerblue", marker=None)
        ax1.plot(df["Date"], df["Spread"], linestyle = "-", label="Spread", color="violet", marker=None)

        if self.threshold_setting.get() is True: # shows stdev of spread threshold lines if setting on
            ax1.axhline(y = mean_spread, color = 'm', linestyle = '-') # mean spread
            ax1.axhline(y = upper_threshold, color = 'm', linestyle = '-') # + num_stdev spread
            ax1.axhline(y = lower_threshold, color = 'm', linestyle = '-') # - num_stdev spread
        
        if self.mean_setting.get() is True:
            ax1.axhline(y = stock1_mean_price, color = 'darkorange', linestyle = '-') # mean price stock1
            ax1.axhline(y = stock2_mean_price, color = 'dodgerblue', linestyle = '-') # mean price stock2

        if self.signal_setting.get() is True:
            ax1.scatter(df["Date"], df["Entries"], color="green", label="Entry Signal", marker="^", s=100)
            ax1.scatter(df["Date"], df["Exits"], color="red", label="Exit Signal", marker="v", s=100)
        
        ax1.xaxis.set_major_locator(mdates.YearLocator()) # Automatically sets yearly
        self.fig1.autofmt_xdate()
        ax1.set_xlabel("Date")
        ax1.set_ylabel("Stock Price (USD)")
        ax1.set_title(f"Historical Prices of {self.stock1_name.get()} & {self.stock2_name.get()}")
        ax1.legend()
        ax1.grid()


        # Graph portfolio value over time
        self.fig2, ax2 = plt.subplots(figsize=(7, 4))
        ax2.plot(df["Date"], df["Portfolio Value"], linestyle = "-", label="Portfolio Value", marker=None)
        ax2.xaxis.set_major_locator(mdates.YearLocator()) # Automatically sets yearly
        self.fig2.autofmt_xdate()
        ax2.set_xlabel("Date")
        ax2.set_ylabel("Value (USD)")
        ax2.set_title("Portfolio Value Over Time")
        ax2.legend()
        ax2.grid()


    def create_submit_reset(self, graphs_frame):
        """
        Creates submit(aka test) and reset button widget
        """
        # Submit and rest button frame
        submit_frame = ttk.Frame(self)
        submit_frame.grid(row=2, column=0)

        def submit():
            """
            Aka "Test" function
            Defining function that will get the two stock names and execute functionality when form submitted
            Updates displayed values
            """
            # Call function to analyze stocks
            self.analyze_stocks(self.stock1_name.get(), self.file_path1.get(), self.stock2_name.get(), self.file_path2.get())
            self.create_graphs(graphs_frame)

            # Update stats
            self.labels["correl"].config(text=round(self.correlation, 4))
            self.labels["sharpe"].config(text=round(self.sharpe_ratio, 4))
            self.labels["return"].config(text=f"{self.return_pct:.2f}%")
            self.labels["trades"].config(text=self.num_trades.get())


        # Create reset button
        def reset():
            """
            Clear fields
            """
            # reset entry forms
            self.stock1_name.set("")
            self.stock2_name.set("")

            # reset file select
            self.labels["file1"].config(text=f"File {1}: None selected")
            self.labels["file2"].config(text=f"File {2}: None selected")

            # reset file paths
            self.file_path1.set("")
            self.file_path2.set("")

            # reset settings
            self.capital.set(10000)  # set default starting capital
            self.order_size.set(10) # set default order size
            self.num_stdevs.set(1.5)
            self.threshold_setting.set(False)
            self.mean_setting.set(False)
            self.signal_setting.set(False)

            # reset statistics
            self.labels["correl"].config(text="")
            self.labels["sharpe"].config(text="")
            self.labels["return"].config(text="")
            self.labels["trades"].config(text="")

            # reset graphs if they exist
            if self.analysis_graph: 
                self.analysis_graph.get_tk_widget().destroy() # remove canvas from tkinter
                self.analysis_graph = None # reset reference
                self.analysis_toolbar.destroy() # remove toolbar
                self.analysis_toolbar = None # reset reference

                self.portfolio_graph.get_tk_widget().destroy()
                self.portfolio_graph = None
                self.portfolio_toolbar.destroy()
                self.portfolio_toolbar = None
                close_graphs() # close plots
            
        # Create reset button
        reset_btn = ttk.Button(submit_frame, text="Reset", command = reset)
        reset_btn.grid(row=0, column=0, sticky="se")

        # Create submit button
        submit_btn = ttk.Button(submit_frame, text="Test", command = submit)
        submit_btn.grid(row=0, column=1, sticky="se", padx=10)


    def create_graphs(self, graphs_frame):
        """
        Draws graphs in graphs_frame parameter which is initialized in __init__ and passed from create_submit_rest to this function
        """
        # Embed trade analysis graph
        self.analysis_graph = FigureCanvasTkAgg(self.fig1, master=graphs_frame)
        self.analysis_graph.get_tk_widget().grid(row=0, column=0, padx = 5, pady=5)
        self.analysis_graph.draw()

        # Embed portfolio graph
        self.portfolio_graph = FigureCanvasTkAgg(self.fig2, master=graphs_frame)
        self.portfolio_graph.get_tk_widget().grid(row=2, column=0, padx= 5, pady=5)
        self.portfolio_graph.draw()

        # Add toolbars for both graphs
        analysis_toolbar_frame = ttk.Frame(graphs_frame)
        analysis_toolbar_frame.grid(row=1, column=0)
        self.analysis_toolbar = NavigationToolbar2Tk(self.analysis_graph, analysis_toolbar_frame, pack_toolbar=False)
        self.analysis_toolbar.update()
        self.analysis_toolbar.pack(side="right", fill="y", expand=True)

        portfolio_toolbar_frame = ttk.Frame(graphs_frame)
        portfolio_toolbar_frame.grid(row=3, column=0)
        self.portfolio_toolbar = NavigationToolbar2Tk(self.portfolio_graph, portfolio_toolbar_frame, pack_toolbar=False)
        self.portfolio_toolbar.update()
        self.portfolio_toolbar.pack(side="right", fill="y", expand=True)


    def create_stats(self):
        """
        Creates statistics widget
        """
        stats_frame = ttk.Frame(self, width=600, height=170)
        stats_frame.grid(row=0, column=1, padx=20, pady=40, sticky="n")
        stats_frame.grid_propagate(False)

        correl_label = ttk.Label(stats_frame, text="Correlation:", foreground="white", font=("Helvetica Neue", 10))
        correl_label.grid(row=0, column=0, sticky="nw", padx=10, pady=10)

        correl_value_label = ttk.Label(stats_frame, text="", foreground="white", font=("Helvetica Neue", 10))
        correl_value_label.grid(row=0, column=1, sticky="nw", padx=10, pady=10)
        self.labels["correl"] = correl_value_label


        sharpe_label = ttk.Label(stats_frame, text="Sharpe Ratio:", foreground="white", font=("Helvetica Neue", 10))
        sharpe_label.grid(row=1, column=0, sticky="nw", padx=10, pady=10)

        sharpe_value_label = ttk.Label(stats_frame, text="", foreground="white", font=("Helvetica Neue", 10))
        sharpe_value_label.grid(row=1, column=1, sticky="nw", padx=10, pady=10)
        self.labels["sharpe"] = sharpe_value_label


        return_label = ttk.Label(stats_frame, text="Total Return:", foreground="white", font=("Helvetica Neue", 10))
        return_label.grid(row=2, column=0, sticky="nw", padx=10, pady=10)

        return_value_label = ttk.Label(stats_frame, text="", foreground="white", font=("Helvetica Neue", 10))
        return_value_label.grid(row=2, column=1, sticky="nw", padx=10, pady=10)
        self.labels["return"] = return_value_label

        num_trades_label = ttk.Label(stats_frame, text="Number of Trades:", foreground="white", font=("Helvetica Neue", 10))
        num_trades_label.grid(row=3, column=0, sticky="nw", padx=10, pady=10)

        num_trades_value_label = ttk.Label(stats_frame, text="", foreground="white", font=("Helvetica Neue", 10))
        num_trades_value_label.grid(row=3, column=1, sticky="nw", padx=10, pady=10)
        self.labels["trades"] = num_trades_value_label


    def create_settings(self):
        """
        Creates settings widget        
        """
        # Create frame for settings
        settings_frame = ttk.Frame(self) 
        settings_frame.grid(row=1, column=0, padx=40, pady=20, sticky="nw")

        settings_label = ttk.Label(settings_frame, text="Settings:", foreground="white", font=("Helvetica Neue", 20))
        settings_label.grid(row=0, column=0, sticky="nw", padx=10, pady=10)

        # Starting capital setting
        capital_label = ttk.Label(settings_frame, text="Starting Capital", foreground="white", font=("Helvetica Neue", 10))
        capital_label.grid(row=1, column=0, sticky="nw", padx=10, pady=10)

        starting_capital_input = ttk.Entry(settings_frame, textvariable = self.capital)
        starting_capital_input.grid(row=1, column=1, padx=10, pady=10)

        # Order size settings
        order_size_label = ttk.Label(settings_frame, text="Order Size", foreground="white", font=("Helvetica Neue", 10))
        order_size_label.grid(row=2, column=0, sticky="nw", padx=10, pady=10)

        order_size_input = ttk.Spinbox(settings_frame, from_=0, to=(self.capital.get()/200), increment=1, textvariable=self.order_size) # from 0 to starting capital/200
        order_size_input.grid(row=2, column=1, padx=10, pady=10)

        # Standard deviations threshold setting
        stdev_label = ttk.Label(settings_frame, text="SD Threshold", foreground="white", font=("Helvetica Neue", 10))
        stdev_label.grid(row=3, column=0, sticky="nw", padx=10, pady=10)

        stdev_input = ttk.Spinbox(settings_frame, from_=1, to=3, increment=0.5, textvariable=self.num_stdevs)
        stdev_input.grid(row=3, column=1, padx=10, pady=10)

        def check_setting_widget(frame, label_text: str, var, row_num: int):
            """
            Creates settings with label and checkbox
            - frame: the frame the widget is in
            - text (str): the text to display in the label
            - variable: the BooleanVar variable tied to the checkbox
            - row_num (int): the row in the frames grid to place the widget
            """
            check_label = ttk.Label(frame, text=label_text, foreground="white", font=("Helvetica Neue", 10))
            check_label.grid(row=row_num, column=0, sticky="nw", padx=10, pady=10)
            
            check = ttk.Checkbutton(frame, variable=var, padding=10)
            check.grid(row=row_num, column=1, padx=10, pady=5)

        check_setting_widget(settings_frame, "Show Thresholds", self.threshold_setting, 4) # Threshold line setting
        check_setting_widget(settings_frame, "Show Price Mean", self.mean_setting, 5) # Stock mean setting
        check_setting_widget(settings_frame, "Show Trade Signals", self.signal_setting, 6) # Trade signal setting
    

def close_graphs():
    plt.close("all") # closes all figures

if __name__ == "__main__":
    app = ttk.Window(title="Pairs Trading Tool", themename="vapor") # app is the master window
    app.geometry(f"{app.winfo_screenwidth()}x{app.winfo_screenheight()}")  # Set window size to screen size
    TradingApp(app) # initialize Trading app object with app as master window parameter

    app.protocol("WM_DELETEWINDOW", lambda: [close_graphs(), app.destory()]) # close when exit
    app.mainloop() # keep window running
    