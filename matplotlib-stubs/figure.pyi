from matplotlib.figure import _AxesStack  # ty:ignore[unresolved-import]
from matplotlib.axes import Axes
from matplotlib.legend import Legend
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
    def set_size_inches(
        self, w: float, h: float, *args: Any, **kwargs: Any
    ) -> None: ...
    dpi: float
    canvas: Any
    figure: Any
    bbox: Any
    axes: List[Axes]
    texts: List[Text]
    patches: List[Patch]
    legends: List[Legend]
    subfigs: List[SubFigure]
    def text(self, x: float, y: float, *args: Any, **kwargs: Any) -> Text: ...
    def savefig(self, fname: Any, *args: Any, **kwargs: Any) -> None: ...
    signals: Any
    _pyl_graphics_scene_snapparent: Any
    _axstack: _AxesStack
    dpi_scale_trans: Any
    def _make_key(self, ax: Axes) -> Any: ...
    no_figure_dragger_selection_update: bool

class SubFigure:
    bbox: Any

    axes: List[Axes]
    texts: List[Text]
    patches: List[Patch]
    legends: List[Legend]
    subfigs: List[SubFigure]

    transFigure: Transform
    transSubfigure: Transform

    dpi_scale_trans: Any
