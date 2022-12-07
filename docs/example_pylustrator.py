# import matplotlib and numpy as usual
import matplotlib.pyplot as plt
import numpy as np

# now import pylustrator
import pylustrator

from icecream import install
install()
import matplotlib.pyplot as plt
import numpy as np

# now import pylustrator
import pylustrator

# activate pylustrator
pylustrator.start()

if 1:
    # build plots as you normally would
    np.random.seed(1)
    t = np.arange(0.0, 2, 0.001)
    y = 2 * np.sin(np.pi * t)
    a, b = np.random.normal(loc=(5., 3.), scale=(2., 4.), size=(100,2)).T
    b += a
    
    fig = plt.figure(1)
    plt.clf()
    fig.text(0.5, 0.5, "new", transform=plt.figure(1).transFigure)
    plt.subplot(131)
    plt.plot(t, y)
    plt.text(0.5, 0.5, "new", transform=plt.figure(1).axes[0].transAxes)
    plt.xlabel("bla")
    plt.ylabel("foo")
    plt.subplot(132)
    plt.plot(a, b, "o")

    plt.subplot(133)
    plt.bar(0, np.mean(a), label="a")
    plt.bar(1, np.mean(b), label="b")
    #plt.legend()
    plt.xticks
    plt.figure(1).axes[0].set(position=[0.125, 0.11, 0.2279, 0.77], xlim=(-0.09995, 3.), xlabel='blaa', xticks=[0., 1., 2., 3.], xticklabels=['0', '1', '2', '3'], ylim=(-3., 3.), ylabel='fooo', yticks=[-3., -2., -1., 0., 1., 2., 3.], yticklabels=['−3', '−2', '−1', '0', '1', '2', '3'])

    plt.figure(1).axes[0].spines[['right', 'top']].set_visible(False)

    #% start: automatic generated code from pylustrator
    plt.figure(1).ax_dict = {ax.get_label(): ax for ax in plt.figure(1).axes}
    import matplotlib as mpl
    getattr(plt.figure(1), '_pylustrator_init', lambda: ...)()
    plt.figure(1).axes[0].grid(True)
    plt.figure(1).axes[0].set(position=[0.1033, 0.1945, 0.2279, 0.77], xlim=(-0.09995, 10.))
    plt.figure(1).axes[0].texts[0].set(position=(0.2854, 0.5627))
    plt.figure(1).axes[1].spines[['right', 'top']].set_visible(False)
    plt.figure(1).axes[2].set(ylim=(0., 8.82))
    plt.figure(1).axes[2].spines[['right', 'top']].set_visible(False)
    #% end: automatic generated code from pylustrator
    plt.show()
    exit()
# activate pylustrator
pylustrator.start()

# build plots as you normally would
np.random.seed(1)
t = np.arange(0.0, 2, 0.001)
y = 2 * np.sin(np.pi * t)
a, b = np.random.normal(loc=(5., 3.), scale=(2., 4.), size=(100,2)).T
b += a

plt.figure(1)
sub_fig = plt.gcf().add_subfigure(plt.GridSpec(2, 1)[0, 0])
sub_fig2 = sub_fig.add_subfigure(plt.GridSpec(1, 2)[0, 0])
sub_fig2.add_subplot(121)
plt.plot(t, y)
plt.text(0.5, 0.5, "neu!")

sub_fig.add_subplot(122)
plt.plot(a, b, "o")

sub_fig = plt.gcf().add_subfigure(plt.GridSpec(2, 1)[1, 0])
sub_fig.add_subplot(111)
plt.bar(0, np.mean(a), label="A")
plt.bar(1, np.mean(b), label="B")


#plt.figure(1).axes[0].set(position=[0.213022, 0.498889, 0.227941, 0.381111], xlim=[0.7, 1448], xticks=[0.1, 0.001], xticklabels=["A", "B"])
#for name in dir(plt.figure(1).axes[0]):
#    if name.startswith("set_"):
#        print(name)

plt.show()

