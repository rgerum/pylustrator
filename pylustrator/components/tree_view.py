from typing import TYPE_CHECKING, Optional

import qtawesome as qta

if TYPE_CHECKING:
    from PyQt5 import QtCore, QtGui, QtWidgets
else:
    from qtpy import QtCore, QtGui, QtWidgets

from matplotlib.artist import Artist
from matplotlib.spines import Spine
from matplotlib.axis import XAxis, YAxis
from matplotlib.text import Text


class myTreeWidgetItem(QtGui.QStandardItem):
    entry: Artist | None = None
    expanded: bool = False

    def __init__(self, text: str):
        """a tree view item to display the contents of the figure"""
        QtGui.QStandardItem.__init__(self, text)

    def parent(self) -> Optional["myTreeWidgetItem"]:
        parent = super().parent()
        if parent is None:
            return parent
        if isinstance(parent, myTreeWidgetItem):
            return parent
        raise TypeError("myTreeWidgetItem has invalid parent")


class MyTreeView(QtWidgets.QTreeView):
    # item_selected = lambda x, y: 0
    def item_clicked(x, y):
        return 0

    def item_activated(x, y):
        return 0

    def item_hoverEnter(x, y):
        return 0

    def item_hoverLeave(x, y):
        return 0

    last_selection = None
    last_hover = None
    model: QtGui.QStandardItemModel

    def item_selected(self, x):
        if not self.fig.no_figure_dragger_selection_update:
            if getattr(self.fig, "figure_dragger", None) is not None:
                self.fig.figure_dragger.select_element(x)

    def __init__(self, signals, layout: QtWidgets.QLayout):
        """A tree view to display the contents of a figure

        Args:
            parent: the parent widget
            layout: the layout to which to add the tree view
            fig: the target figure
        """
        super().__init__()
        # self.setMaximumWidth(300)

        signals.figure_changed.connect(self.setFigure)
        signals.figure_element_selected.connect(self.select_element)
        signals.figure_element_child_created.connect(
            lambda x: self.updateEntry(x, update_children=True)
        )

        layout.addWidget(self)

        # start a list for backwards search (from marker entry back to tree entry)
        self.marker_modelitems = {}
        self.marker_type_modelitems = {}

        # model for tree view
        self.model = QtGui.QStandardItemModel(0, 0)

        # some settings for the tree
        self.setUniformRowHeights(True)
        self.setHeaderHidden(True)
        self.setAnimated(True)
        self.setModel(self.model)
        self.expanded.connect(self.TreeExpand)
        self.clicked.connect(self.treeClicked)
        self.activated.connect(self.treeActivated)

        selectionModel = self.selectionModel()
        if selectionModel is None:
            raise ValueError("")
        selectionModel.selectionChanged.connect(self.selectionChanged)

        # add context menu
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)

        # add hover highlight
        viewport = self.viewport()
        if viewport is None:
            raise ValueError("")
        viewport.setMouseTracking(True)
        viewport.installEventFilter(self)

        self.item_lookup = {}

    def select_element(self, element: Artist):
        """select an element"""
        if element is None:
            self.setCurrentIndex(self.fig)
        else:
            self.setCurrentIndex(element)

    def setFigure(self, fig):
        self.fig = fig
        self.model.removeRows(0, self.model.rowCount())
        self.expand(None)

        self.deleteEntry(self.fig)
        self.expand(None)
        self.expand(self.fig)
        self.setCurrentIndex(self.fig)

    def selectionChanged(
        self, selection: QtCore.QItemSelection, y: QtCore.QItemSelection
    ):
        """when the selection in the tree view changes"""
        model = None
        if len(selection.indexes()):
            model = selection.indexes()[0].model()
        entry = None
        if model is not None and isinstance(model, QtGui.QStandardItemModel):
            selected_entry = model.itemFromIndex(selection.indexes()[0])
            if isinstance(selected_entry, myTreeWidgetItem):
                entry = selected_entry.entry
        if self.last_selection != entry:
            self.last_selection = entry
            self.item_selected(entry)

    def setCurrentIndex(self, entry: Artist):
        """set the currently selected entry"""
        while entry:
            item = self.getItemFromEntry(entry)
            if item is not None:
                try:
                    super().setCurrentIndex(item.index())
                except RuntimeError:  # maybe find out why we run into this error when the figure is changed
                    pass
                return

            tree_parent = getattr(entry, "tree_parent", None)
            if isinstance(tree_parent, Artist):
                entry = tree_parent
            else:
                return

    def treeClicked(self, index: QtCore.QModelIndex):
        """upon selecting one of the tree elements"""
        model = index.model()
        if model is not None and isinstance(model, QtGui.QStandardItemModel):
            selected_entry = model.itemFromIndex(index)
            if isinstance(selected_entry, myTreeWidgetItem):
                data = selected_entry.entry
                return self.item_clicked(data)
        return self.item_clicked(None)

    def treeActivated(self, index: QtCore.QModelIndex):
        """upon selecting one of the tree elements"""
        model = index.model()
        if model is not None and isinstance(model, QtGui.QStandardItemModel):
            selected_entry = model.itemFromIndex(index)
            if isinstance(selected_entry, myTreeWidgetItem):
                data = selected_entry.entry
                return self.item_activated(data)
        return self.item_activated(None)

    def eventFilter(
        self, a0: Optional[QtCore.QObject], a1: Optional[QtCore.QEvent]
    ) -> bool:
        """event filter for tree view port to handle mouse over events and marker highlighting"""
        if a1 is None:
            return False
        if a1.type() == QtCore.QEvent.Type.HoverMove and isinstance(
            a1, QtGui.QHoverEvent
        ):
            # HoverMove events have pos() method
            pos = a1.pos()
            index = self.indexAt(pos)
            try:
                model = index.model()
                if isinstance(model, QtGui.QStandardItemModel):
                    item = model.itemFromIndex(index)
                    if isinstance(item, myTreeWidgetItem):
                        entry = item.entry
                    else:
                        entry = None
                else:
                    entry = None
            except AttributeError:
                entry = None

            # check for new item
            if entry != self.last_hover:
                # deactivate last hover item
                if self.last_hover is not None:
                    self.item_hoverLeave(self.last_hover)

                # activate current hover item
                if entry is not None:
                    self.item_hoverEnter(entry)

                self.last_hover = entry
                return True

        return False

    def queryToExpandEntry(self, entry: Artist) -> list:
        """when expanding a tree item"""
        if entry is None:
            return [self.fig]
        return entry.get_children()

    def getParentEntry(self, entry: Artist) -> Artist | None:
        """get the parent of an item"""
        return getattr(entry, "tree_parent", None)

    def getNameOfEntry(self, entry: Artist | None) -> str:
        """convert an entry to a string"""
        try:
            return str(entry)
        except AttributeError:
            return "unknown"

    def getIconOfEntry(self, entry: Artist) -> QtGui.QIcon:
        """get the icon of an entry"""
        draggable = getattr(entry, "_draggable", None)
        if draggable:
            if draggable.connected:
                return qta.icon("fa5.hand-paper-o")
        return QtGui.QIcon()

    def getKey(self, entry: Artist) -> Artist:
        """get the key of an entry, which is the entry itself"""
        return entry

    def getItemFromEntry(self, entry: Artist | None) -> Optional[myTreeWidgetItem]:
        """get the tree view item for the given artist"""
        if entry is None:
            return None
        key = self.getKey(entry)
        try:
            return self.item_lookup[key]
        except KeyError:
            return None

    def setItemForEntry(self, entry: Artist, item: myTreeWidgetItem):
        """store a new artist and tree view widget pair"""
        key = self.getKey(entry)
        self.item_lookup[key] = item

    def expand(self, entry: Artist | None, force_reload: bool = True):
        """expand the children of a tree view item"""
        if entry is None:
            return
        query = self.queryToExpandEntry(entry)
        parent_item = self.getItemFromEntry(entry)
        parent_entry = entry

        if parent_item:
            if parent_item.expanded is False:
                # remove the dummy child
                parent_item.removeRow(0)
                parent_item.expanded = True
            # force_reload: delete all child entries and re query content from DB
            elif force_reload:
                # delete child entries
                parent_item.removeRows(0, parent_item.rowCount())
            else:
                return

        # add all marker types
        row = -1
        for row, entry in enumerate(query):
            entry.tree_parent = parent_entry
            if 1:
                if (
                    isinstance(entry, Spine)
                    or isinstance(entry, XAxis)
                    or isinstance(entry, YAxis)
                ):
                    continue
                if isinstance(entry, Text) and entry.get_text() == "":
                    continue

                patch = getattr(parent_entry, "patch", None)
                if patch and entry == patch:
                    continue

                try:
                    label = entry.get_label()
                    if label == "_tmp_snap" or label == "grabber":
                        continue
                except AttributeError:
                    pass
            self.addChild(parent_item, entry)

    def addChild(self, parent_item: myTreeWidgetItem | None, entry: Artist, row=None):
        """add a child to a tree view node"""
        # add item
        item = myTreeWidgetItem(self.getNameOfEntry(entry))
        item.expanded = False
        item.entry = entry

        item.setIcon(self.getIconOfEntry(entry))
        item.setEditable(False)

        if parent_item is None:
            if row is None:
                row = self.model.rowCount()
            self.model.insertRow(row)
            self.model.setItem(row, 0, item)
        else:
            if row is None:
                parent_item.appendRow(item)
            else:
                parent_item.insertRow(row, item)
        self.setItemForEntry(entry, item)

        # add dummy child
        if self.queryToExpandEntry(entry) is not None and len(
            self.queryToExpandEntry(entry)
        ):
            child = myTreeWidgetItem("loading")
            child.entry = None
            child.setEditable(False)
            child.setIcon(qta.icon("fa5s.hourglass-half"))
            item.appendRow(child)
            item.expanded = False
        return item

    def TreeExpand(self, index):
        """expand a tree view node"""
        # Get item and entry
        item = index.model().itemFromIndex(index)
        entry = item.entry
        thread = None

        # Expand
        if item.expanded is False:
            self.expand(entry)
            # thread = Thread(target=self.expand, args=(entry,))

        # Start thread as daemonic
        if thread:
            thread.setDaemon(True)
            thread.start()

    def updateEntry(
        self,
        entry: Artist,
        update_children: bool = False,
        insert_before: Artist | None = None,
        insert_after: Artist | None = None,
    ):
        """update a tree view node"""
        # get the tree view item for the database entry
        item = self.getItemFromEntry(entry)
        # if we haven't one yet, we have to create it
        if item is None:
            # get the parent entry
            parent_entry = self.getParentEntry(entry)
            # if we have a parent and are not at the top level try to get the corresponding item
            if parent_entry:
                parent_item = self.getItemFromEntry(parent_entry)
                # parent item not in list or not expanded, than we don't need to update it because it is not shown
                if parent_item is None or parent_item.expanded is False:
                    if parent_item:
                        parent_item.setText(self.getNameOfEntry(parent_entry))
                    return
            else:
                parent_item = None

            # define the row where the new item should be
            row = None
            if insert_before:
                before_entry = self.getItemFromEntry(insert_before)
                if before_entry:
                    row = before_entry.row()
            if insert_after:
                after_entry = self.getItemFromEntry(insert_after)
                if after_entry:
                    row = after_entry.row() + 1

            # add the item as a child of its parent
            self.addChild(parent_item, entry, row)
            if parent_item:
                if row is None:
                    parent_item.sortChildren(0)
                if parent_entry:
                    parent_item.setText(self.getNameOfEntry(parent_entry))
        else:
            # check if we have to change the parent
            parent_entry = self.getParentEntry(entry)
            parent_item = self.getItemFromEntry(parent_entry)
            if parent_item != item.parent():
                # remove the item from the old position
                item_parent = item.parent()
                if item_parent is None:
                    self.model.takeRow(item.row())
                else:
                    item_parent.takeRow(item.row())

                # determine a potential new position
                row = None
                if insert_before:
                    before_entry = self.getItemFromEntry(insert_before)
                    if before_entry:
                        row = before_entry.row()
                if insert_after:
                    after_entry = self.getItemFromEntry(insert_after)
                    if after_entry:
                        row = after_entry.row() + 1

                # move the item to the new position
                if parent_item is None:
                    if row is None:
                        row = self.model.rowCount()
                    self.model.insertRow(row)
                    self.model.setItem(row, 0, item)
                else:
                    if row is None:
                        parent_item.appendRow(item)
                    else:
                        parent_item.insertRow(row, item)

            # update the items name, icon and children
            item.setIcon(self.getIconOfEntry(entry))
            item.setText(self.getNameOfEntry(entry))
            if update_children:
                self.expand(entry, force_reload=True)

    def deleteEntry(self, entry: Artist):
        """delete an entry from the tree"""
        # get the tree view item for the database entry
        item = self.getItemFromEntry(entry)
        if item is None or not isinstance(item, myTreeWidgetItem):
            return

        parent_item = item.parent()
        # if parent_item:
        #    parent_entry = parent_item.entry

        key = self.getKey(entry)
        del self.item_lookup[key]

        # delete row from the treeview
        if parent_item is None:
            self.model.removeRow(item.row())
        else:
            parent_item.removeRow(item.row())
            # parent_item.removeRow(item.row(), parent_entry) # this is not working

        # update the label of parent item ## parent item does not have an attribute setLabel
        # if parent_item:
        #    name = self.getNameOfEntry(parent_entry)
        #    if name is not None:
        #        parent_item.setLabel(name)
