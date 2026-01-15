"""Type definitions for pylustrator."""

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Protocol, runtime_checkable

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.backend_bases import FigureCanvasBase
    from .change_tracker import ChangeTracker
    from .drag_helper import DragManager


@runtime_checkable
class PylustatorFigure(Protocol):
    """Protocol for Figure objects with pylustrator extensions."""

    # Standard matplotlib Figure attributes
    axes: List["Axes"]
    canvas: "FigureCanvasBase"

    # Pylustrator-specific attributes
    change_tracker: "ChangeTracker"
    figure_dragger: "DragManager"
    selection: Any  # GrabbableRectangleSelection
    signals: Any  # Signals object
    window: Any  # PlotWindow
    ax_dict: Dict[str, "Axes"]
    _pyl_scene: Any
    _pyl_graphics_scene_snapparent: Any
    color_artists: List[Any]
    _variable_name: Optional[str]
    _last_saved_figure: List[tuple]
    no_figure_dragger_selection_update: bool

    def get_size_inches(self) -> tuple: ...
    def set_size_inches(self, w: float, h: float = ..., forward: bool = ...) -> None: ...
    def savefig(self, fname: Any, **kwargs: Any) -> None: ...
