import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from matplotlib import collections as mc
from tkinter import *
from tkinter.filedialog import askopenfilename
from collections import defaultdict as dd


class EdgeFile:

    def __init__(self, edge_file):
        self.edge_file_name = edge_file
        self.edge_source = {}
        self.current_edges = dd(list)
        self.size = 0
        # keeping file open
        self.edge_file = self.load_file(edge_file)
        # parsing
        self.parse_edge()

    def __del__(self):
        # at least closing file while destroyed
        print("Destoying current edgefile object")
        if(self.edge_file):
            self.edge_file.close()

    def load_file(self, filename):
        if(filename):
            return(open(filename, 'r'))
        return(None)

    def add_edge(self, data):
        edge = {}
        edge["r1"] = data[0]
        edge["l1"] = data[1]
        edge["r2"] = data[2]
        edge["l2"] = data[3]
        edge["dir"] = data[4]
        edge["iso"] = data[5]

        ori = 1
        if(data[4] == "1"):
            ori = -1
        # Changing slightly the pos format to make "dash"
        seeds = [[(int(e1), int(e2)), (int(e1) + 16, int(e2) + 16 * ori)]
                 for e1, e2 in [element.split(",") for element in data[6:]]]
        edge["pos"] = list(seeds)

        # storing edge data using target as key.
        # we only store edge for one source read
        self.current_edges[data[2]] = edge

    def get_edges(self, source_read):

        self.current_edges.clear()
        pointer = self.edge_source[source_read]
        # jumping to pointer
        self.edge_file.seek(pointer)
        last_read = source_read
        for line in self.edge_file:
            data = line.rstrip("\n").split("\t")
            if(len(data) >= 2):
                # if we change read
                if(data[0] != last_read):
                    break
                else:
                    self.add_edge(data)

    def parse_edge(self):
        not_end = True if self.edge_file else False
        last_read = ""
        while not_end:
            current_pointer = self.edge_file.tell()
            line = self.edge_file .readline()
            if(len(line) == 0):
                not_end = False
            else:
                data = line.rstrip("\n").split("\t")
                if(len(data) >= 2):
                    if(data[0] != last_read):
                        # storing pointer in file for this read
                        self.edge_source[data[0]] = current_pointer
                    last_read = data[0]
        # Returning to start
        if(self.edge_file):
            self.edge_file.seek(0)


class mainFrame():
    def __init__(self):

        # Main window
        self.root = Tk()

        # Edge file name and object
        self.file_name = None
        self.edge_file = None

        # Current reads
        self.value_1 = None
        self.value_2 = None

        self.source_reads = []
        self.target_reads = []

        # MENUS
        container = Frame(self.root)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        menubar = Menu(container)
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(
            label="Load File", command=self.open_file)

        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=quit)
        menubar.add_cascade(label="File", menu=filemenu)
        Tk.config(self.root, menu=menubar)

        # READ SELECTION MENU
        selector = Frame(self.root)
        selector.pack(side="top", fill="both", expand=True)
        selector.grid_rowconfigure(0, weight=1)
        selector.grid_columnconfigure(0, weight=1)

        # Buttons
        self.r1_button = Button(
            selector, text="Select read 1",
            command=lambda: self.popup(self.root, 1))

        self.r2_button = Button(
            selector, text="Select read 2",
            command=lambda: self.popup(self.root, 2))

        self.r1_button.pack(fill=X, side=LEFT,)
        self.r2_button.pack(fill=X, side=RIGHT, )

        # GRAPH ZONE
        self.fig = Figure(figsize=(8, 8))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.draw()

        self.canvas.get_tk_widget().pack(side=BOTTOM,
                                         fill=BOTH,
                                         expand=True)

        toolbar = NavigationToolbar2Tk(self.canvas, self.root)
        toolbar.update()
        self.canvas._tkcanvas.pack(side=TOP, fill=BOTH, expand=True)

        self.plot()

        self.root.update()
        self.root.mainloop()

    def popup(self, parent, button_nb):

        top = self.top = Toplevel(parent)
        label_text = "Value for "
        label_text += ["source", "target"][button_nb - 1]
        label_text += " read."
        no_pack = False

        # If no source read is selected first
        if(button_nb == 2 and (self.value_1 is None or
                               len(self.target_reads) == 0)):
            label_text = "Select a source read before a target"
            no_pack = True

        # If we do not have loaded a file yet
        if(button_nb == 1 and len(self.source_reads) == 0):
            label_text = "Open a valid edge file before selecting a read"
            no_pack = True

        Label(top, text=label_text).pack()

        if(not no_pack):
            scrollbar = Scrollbar(top, orient=VERTICAL)
            self.listbox = Listbox(top, yscrollcommand=scrollbar.set)
            scrollbar.pack(side=RIGHT, fill=Y)
            self.listbox.pack(side=LEFT, fill=BOTH, expand=1)

            if(button_nb == 1):
                self.set_listbox(self.source_reads)
            elif(button_nb == 2):
                self.set_listbox(self.target_reads)

            b = Button(top, text="Ok", command=lambda: self.fetch(button_nb))
            b.pack()
        else:
            b = Button(top, text="Cancel", command=lambda: self.top.destroy())
            b.pack()

    def set_listbox(self, array):
        for item in array:
            self.listbox.insert(END, item)

    def fetch(self, button_nb):
        self.set_change(button_nb)
        # if(button_nb == 1):
        #     print("value 1 is", self.value_1)
        # elif(button_nb == 2):
        #     print("value 2 is", self.value_2)

        self.top.destroy()

    def set_change(self, button_nb):
        if(self.listbox.curselection()):
            now_id = self.listbox.curselection()[0]
            if(button_nb == 1):
                now = self.source_reads[now_id]
                if(now != self.value_1):
                    self.value_1 = now
                    # fetching edges for this read
                    self.load_targets()

            elif(button_nb == 2):
                now = self.target_reads[now_id]
                if(now != self.value_2):
                    self.value_2 = now
                    self.plot()

        else:
            print("No change")

    def load_targets(self):
        self.edge_file.get_edges(self.value_1)
        self.target_reads = list(self.edge_file.current_edges.keys())

    def open_file(self):

        file_name = askopenfilename()
        if(file_name):
            self.file_name = file_name
            self.edge_file = EdgeFile(self.file_name)
            if(self.file_name == self.edge_file.edge_file_name):
                print("LOADED EDGEFILE: ", self.file_name)
                self.source_reads = list(self.edge_file.edge_source.keys())
            else:
                print("Something went wrong, need to load an other file...")
        else:
            print("Need to load a valid file...")

    def plot(self):
        target = self.value_2
        self.fig.clear()
        yname = "Target"
        xname = "Source"
        if(self.edge_file and target is not None):
            lines = self.edge_file.current_edges[target]['pos']
            xname = self.value_1
            yname = self.value_2
        else:
            lines = [[(0, 0)], [(0, 0)]]

        lc = mc.LineCollection(lines, linewidths=2)

        a = self.fig.add_subplot(111)

        a.add_collection(lc)
        a.autoscale()
        a.margins(0.1)
        # line_ref = [i for i in range(lines[0][0][0], lines[-1][0][1])]
        # line_tgt = [i for i in range(lines[0][0][1], lines[-1][1][1])]

        # a.plot(line_ref, line_ref, color='r', label="expected")
        # a.invert_yaxis()

        a.set_title("Simple Dot Plot", fontsize=16)
        a.set_ylabel(yname, fontsize=14)
        a.set_xlabel(xname, fontsize=14)
        a.autoscale()

        self.canvas.draw()


mainFrame()
