import taipy as tp
from taipy.gui import Gui

from taipy import Core
from pages import *


if __name__ == "__main__":
    gui = Gui(page=Drift)
    gui.run(title="Drift Detection")
