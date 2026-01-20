from matplotlib.axes import Axes
from matplotlib.patches import Patch

from pylustrator.QtGuiDrag import PlotWindow
from pylustrator.change_tracker import ChangeTracker
from pylustrator.drag_helper import DragManager, GrabbableRectangleSelection
from typing import Optional, Any, List, Callable, Tuple
from matplotlib.text import Text
from matplotlib.transforms import Transform

class Figure:
    window: PlotWindow
    change_tracker: ChangeTracker
    figure_dragger: DragManager
    selection: GrabbableRectangleSelection
    transFigure: Transform
    get_size_inches: Callable[[], Tuple[float, float]]
    set_size_inches: Callable[[float, float, Optional[bool]], None]
    dpi: float
    canvas: Any
    figure: Any
    axes: List[Axes]
    texts: List[Text]
    patches: List[Patch]
    def text(self, x: float, y: float, s: str, *args: Any, **kwargs: Any) -> Text: ...
    def savefig(self, fname: Any, *args: Any, **kwargs: Any) -> None: ...
    # signals: Any
    # no_figure_dragger_selection_update: bool

class SubFigure:
    bbox: Any

    axes: List[Axes]
    texts: List[Text]
    patches: List[Patch]

    transFigure: Transform
    transSubfigure: Transform
