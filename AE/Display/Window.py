import os
import AE.Display.Animation2d as Animation2d

from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QApplication, QWidget, QShortcut

class Window(QWidget):
  """
  Animation-specific window

  Creates a new window containing an animation.
  
  Attributes:
    title (str): Title of the window.
    app (``QApplication``): Underlying ``QApplication``.
    anim (:class:`Animation2d`): Animation to display.
  """

  def __init__(self, title='Animation', animation = None):
    """
    Window constructor

    Defines the ``QApplication``, window title and animation to display.

    Args:
      title (str): Title of the window. Default is 'Animation'.
    """

    # Attributes
    self.title = title
    
    # Qapplication
    self.app = QApplication([])

    # Call widget parent's constructor
    # (otherwise no signal can be caught)
    super().__init__()

    # --- Style

    # Modified qdarkstyle
    with open(os.path.dirname(os.path.abspath(__file__))+'/Style/dark.css', 'r') as f:
      css = f.read()
      self.app.setStyleSheet(css)

    # Animation
    self.animation = animation
    
  def show(self):
    """
    Creates the animation window
    
    Create the window to display the animation, defines the shortcuts,
    initialize and start the animation.

    Args:
      size (float): Height of the ``QGraphicsView`` widget, defining the 
        height of the window.
    """

    # --- Animation

    if self.animation is None:
      self.animation = Animation2d(window=self)

    # --- Layout -----------------------------------------------------------

    self.widget = QWidget()
    self.widget.setLayout(self.animation.layout)

    # --- Settings ---------------------------------------------------------
    
    # Window title
    self.widget.setWindowTitle(self.title)

    # --- Shortcuts

    self.shortcut = {}

    # Quit
    self.shortcut['esc'] = QShortcut(QKeySequence('Esc'), self.widget)
    self.shortcut['esc'].activated.connect(self.close)

    # Play/pause
    self.shortcut['space'] = QShortcut(QKeySequence('Space'), self.widget)
    self.shortcut['space'].activated.connect(self.animation.play_pause)

    # Decrement
    self.shortcut['previous'] = QShortcut(QKeySequence.MoveToPreviousChar, self.widget)
    self.shortcut['previous'].activated.connect(self.animation.decrement)

    # Increment
    self.shortcut['next'] = QShortcut(QKeySequence.MoveToNextChar, self.widget)
    self.shortcut['next'].activated.connect(self.animation.increment)

    # --- Display animation ------------------------------------------------

    self.widget.show()
    if self.animation.autoplay:
      self.animation.play_pause()
    
    self.app.exec()

  def close(self):

    self.animation.stop()
    self.app.quit()