import taipy as tp
from taipy.gui import Gui

from taipy import Core
from pages import *


pages = {"/": root_page, "DriftDetection": Drift}


if __name__ == "__main__":
    gui = Gui(pages=pages)
    gui.run(title="Drift Detection")
