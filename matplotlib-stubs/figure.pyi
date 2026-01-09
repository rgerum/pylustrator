
from pylustrator.QtGuiDrag import PlotWindow
from pylustrator.change_tracker import ChangeTracker
from pylustrator.drag_helper import DragManager, GrabbableRectangleSelection

class Figure:
    window: PlotWindow
    change_tracker: ChangeTracker
    figure_dragger: DragManager
    selection: GrabbableRectangleSelection
    # signals: Any
    # no_figure_dragger_selection_update: bool
