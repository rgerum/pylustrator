import io
import matplotlib.pyplot as plt

def rasterizeAxes(fig):
    restoreAxes(fig)
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=300)
    buf.seek(0)
    im = plt.imread(buf)
    buf.close()

    list_axes = fig.axes
    for ax in list_axes:
        bbox = ax.get_position()
        sx = im.shape[1]
        sy = im.shape[0]
        x1, x2 = int(bbox.x0*sx+1), int(bbox.x1*sx-1)
        y2, y1 = sy-int(bbox.y0*sy+1), sy-int(bbox.y1*sy-1)
        im2 = im[y1:y2, x1:x2]
        for attribute in ["lines", "texts", "images"]:
            setattr(ax, "pylustrator_"+attribute, getattr(ax, attribute))
            setattr(ax, attribute, [])
        ax.pylustrator_rasterized = ax.imshow(im2, extent=[ax.get_xlim()[0], ax.get_xlim()[1], ax.get_ylim()[0], ax.get_ylim()[1]], aspect="auto")

def restoreAxes(fig):
    list_axes = fig.axes
    for ax in list_axes:
        im = getattr(ax, "pylustrator_rasterized", None)
        if im is not None:
            try:
                im.remove()
            except ValueError:
                pass
            del im
        for attribute in ["lines", "texts", "images"]:
            if getattr(ax, "pylustrator_" + attribute, None) is not None:
                setattr(ax, attribute, getattr(ax, "pylustrator_"+attribute))
                setattr(ax, "pylustrator_"+attribute, None)
