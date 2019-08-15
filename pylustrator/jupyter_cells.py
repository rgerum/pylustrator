
def setJupyterCellText(text):
    from IPython.display import Javascript, display
    text = text.replace("\n", "\\n").replace("'", "\\'")
    js = """
    var output_area = this;
    // find my cell element
    var cell_element = output_area.element.parents('.cell');
    // which cell is it?
    var cell_idx = Jupyter.notebook.get_cell_elements().index(cell_element);
    // get the cell object
    var cell = Jupyter.notebook.get_cell(cell_idx);
    cell.get_text();
    cell.set_text('"""+text+"""');
    console.log('"""+text+"""');
    """
    display(Javascript(js))

def setCellInput(i):
    global _i
    _i = i

def getIpythonCurrentCell():
    import IPython
    from pprint import pprint
    c = IPython.core.getipython.get_ipython()
    # pprint(dir(c))
    [i for i in c.runcode("import pylustrator")]
    [i for i in c.runcode("pylustrator.setCellInput(_ih[-1])")]
    return _i

global_files = {}
build_in_open = open
def open(filename, *args, **kwargs):
    if filename.startswith("<ipython"):
        class IPythonCell:
            text = None
            write_text = None
            is_cell = False

            def __init__(self, filename, mode, **kwargs):
                self.filename = filename.strip()

                if mode == "r":
                    if self.filename[0] == "<" and self.filename[-1] == ">":
                        self.is_cell = True
                        self.text = getIpythonCurrentCell()
                    else:
                        self.text = global_files[filename]
                if mode == "w":
                    self.write_text = ""

            def __iter__(self):
                text = self.text
                while len(text):
                    pos = text.find("\n")
                    if pos == -1:
                        yield text
                        break
                    yield text[:pos+1]
                    text = text[pos+1:]

            def write(self, line):
                if self.write_text is None:
                    self.write_text = ""
                self.write_text += line

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.write_text is not None:
                    if self.filename[0] == "<" and self.filename[-1] == ">":
                        setJupyterCellText(self.write_text)
                    else:
                        global_files[self.filename] = self.write_text

        return IPythonCell(filename, *args, **kwargs)
    else:
        return build_in_open(filename, *args, **kwargs)
