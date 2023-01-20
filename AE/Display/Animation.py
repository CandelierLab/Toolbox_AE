"""
Simple tools for displaying 2D animations

Animation2d
-----------

The :class:`Animation2d` wraps a  ``QGraphicsView`` and ``QGraphicsScene``
as well as all necessary tools for display (scene limits, antialiasing, etc.)
It also contains a timer triggering the :py:meth:`.Animation2d.update` 
method at a regular pace. In subclasses, this allows to change elements' 
positions or features (color, size, etc.) to create animations.

Elements
--------

The elements are the items displayed in the scene (*e.g.* circles, lines, ...).
The generic class :class:`element` is used to create such elements, which have to be 
stored in the :py:attr:`Animation2d.elm` dictionnary.

Simple animation window
-----------------------

The :class:`Window` class creates a simple window with the :py:meth:`Animation2d.Qview` 
widget. It manages the ``QApplication``, size on screen, shortcuts and timer trig.
As ``QApplications`` have to be created before any ``QWidget``, :class:`Window` can 
be used with two syntaxes::

  window = Animation.Window()
  window.anim = Animation.Animation2d(window=window)    
  window.show()

or::

  anim = Animation.Animation2d(window=Animation.Window())
  anim.window.show()
"""

import numpy as np
from collections import defaultdict

from PyQt5.QtCore import Qt, QTimer, QElapsedTimer, QPointF
from PyQt5.QtGui import QKeySequence, QPalette, QColor, QPainter, QPen, QBrush, QPolygonF
from PyQt5.QtWidgets import QApplication, QShortcut, QGraphicsScene, QGraphicsView, QGraphicsItem, QGraphicsItemGroup, QGraphicsLineItem, QGraphicsEllipseItem, QGraphicsPolygonItem, QGraphicsRectItem

# === ELEMENTS =============================================================

class element():
  """
  Elements of the animation

  Elements are the items displayed in the ``QGraphicsScene`` of the :class:`Animation2d`.
  A ``group`` element groups other elements for easier manipulation. 
  
  Other supported types are:
    * ``line``
    * ``circle``
    * *TO DO*: ``ellipse``
    * ``rectangle``
    * ``polygon``

  During animation, attributes can be modified with the methods:
    * :py:meth:`.element.rotate`: relative rotation
    * *TO DO* :py:meth:`.element.translate`: relative translation
    * *TO DO* s:py:meth:`.element.etOrientation`: Set absolute orientation
    * :py:meth:`.element.setPosition`: Set absolute position
    * *TO DO* :py:meth:`.element.setColors`: Set fill and stroke colors
    * *TO DO* :py:meth:`.element.setFill`: Set fill color
    * *TO DO* :py:meth:`.element.setStroke`: Set stroke color

  .. note:: The :py:meth:`element.convert` method is for internal use upon
    view initialization. It is normaly not called by a user.
  
  Attributes:
    elm ({:class:`element`}): All elements in the scene
    Qelm (*QGraphicsItem*): The underlying ``QGraphicsItem`` belonging to
      the ``QGraphicsScene`` of the view.
  """

  def __init__(self, type, **kwargs):
    """
    Element constructor

    An element should be fully determined upon definition, so the constructor has many options
    for the different types of elements.

    Args:
      type (str): Type of element, among ``group``, ``line``, ``circle``, 
        ``polygon`` or ``rectangle``.
      parent (*QGraphicsItem*): The parent ``QGraphicsItem``
      belowParent (bool): Determine if the element should be placed above
        the parent (``False``, default) or below (``True``).
      zvalue (float): Z-value of the element in the stack.
      rotation (float): Rotation of the element (rad)
      position ((float,float)): Position of the element (scene units). 
        *Only for ``lines``, ``circles``, ``polygons`` and ``rectangles``.*
      width (float): Width of the element. *Only for ``lines`` and 
        ``rectangles``.*
      height (float): Height of the element. *Only for ``lines`` and 
        ``rectangles``.*
      radius (float): Radius of the circle. *Only for ``circles``.*
      points ([(float,float)]): Points of the polygon. *Only for ``polygons``.*
      thickness (float): Stroke thickness
      color ([*color*, *color*]): Fill and stroke colors. Colors can be 
        whatever input of ``QColor`` (*e.g*: 'darkCyan', '#ff112233' or 
        (255, 0, 0, 127))
    """  

    # Common properties
    self.type = type
    self.view = None
    self.Qelm = None
    self.rotation = kwargs['rotation'] if 'rotation' in kwargs else 0
    self.parent = kwargs['parent'] if 'parent' in kwargs else None
    self.belowParent = kwargs['belowParent'] if 'belowParent' in kwargs else False
    self.zvalue = kwargs['zvalue'] if 'zvalue' in kwargs else None

    # Element-dependent properties
    match type:

      case 'line':
        self.position = kwargs['position'] if 'position' in kwargs else (0,0)
        self.width = kwargs['width'] if 'width' in kwargs else 0
        self.height = kwargs['height'] if 'height' in kwargs else 0
        
      case 'circle':
        self.position = kwargs['position'] if 'position' in kwargs else (0,0)
        self.radius = kwargs['radius'] if 'radius' in kwargs else 0

      case 'polygon':
        self.position = kwargs['position'] if 'position' in kwargs else (0,0)
        self.points = kwargs['points'] if 'points' in kwargs else None

      case 'rectangle':
        self.position = kwargs['position'] if 'position' in kwargs else (0,0)
        self.width = kwargs['width'] if 'width' in kwargs else 0
        self.height = kwargs['height'] if 'height' in kwargs else 0
        
    # --- Style

    # Stroke thickness
    self.thickness = kwargs['thickness'] if 'thickness' in kwargs else 0

    # Colors
    self.color = {}
    self.color['fill'] = kwargs['color'][0] if 'color' in kwargs else 'gray'
    self.color['stroke'] = kwargs['color'][1] if 'color' in kwargs else 'white'

  def convert(self, anim):
    """
    Conversion to ``QGraphicsItem``

    For internal use only.

    Attributes:
      anim (:class:`Animation2d`): Animation
    """

    self.anim = anim

    # --- Definition

    match self.type:

      case 'group':

        self.Qelm = QGraphicsItemGroup()

      case 'line':

        self.Qelm = QGraphicsLineItem(0,0,
          self.width*anim.factor,
          -self.height*anim.factor)

      case 'circle':

        self.Qelm = QGraphicsEllipseItem(
          -self.radius*anim.factor,
          self.radius*anim.factor,
          2*self.radius*anim.factor,
          -2*self.radius*anim.factor)

      case 'polygon':

        poly = []
        for p in self.points:
          poly.append(QPointF(p[0]*anim.factor, -p[1]*anim.factor))

        self.Qelm = QGraphicsPolygonItem(QPolygonF(poly))
        
      case 'rectangle':

        self.Qelm = QGraphicsRectItem(0,0,
          self.width*anim.factor,
          -self.height*anim.factor)


    # --- Position

    if type != 'group':
      if self.parent is None:
        self.Qelm.setPos(
          (self.position[0]-anim.sceneLimits['x'][0])*anim.factor, 
          -(self.position[1]-anim.sceneLimits['y'][0])*anim.factor)
      else:
        self.Qelm.setPos(
          self.position[0]*anim.factor, 
          -self.position[1]*anim.factor)

    # Rotation
    self.rotate(self.rotation)

    # --- Parent

    if self.parent is not None:
      self.Qelm.setParentItem(anim.elm[self.parent].Qelm)

    # --- Stack order

    if self.belowParent:
      self.Qelm.setFlags(self.Qelm.flags() | QGraphicsItem.ItemStacksbelowParent)

    if self.zvalue is not None:
      self.Qelm.setZValue(self.zvalue)

    # --- Colors

    if self.type!='line' and self.color['fill'] is not None:
      self.Qelm.setBrush(QBrush(QColor(self.color['fill'])))

    if self.color['stroke'] is not None:
      self.Qelm.setPen(QPen(QColor(self.color['stroke']), self.thickness))

  def rotate(self, angle):
    """
    Relative rotation

    Rotates the element relatively to its current orientation.
    
    Attributes:
      angle (float): Orientational increment (rad)
    """

    self.Qelm.setRotation(-angle*180/np.pi)

  def setPosition(self, x=None, y=None, z=None):
    """
    Absolute positionning

    Places the element to an absolute position.
    
    Attributes:
      x (float): :math:`x`-coordinate of the new position
      y (float): :math:`y`-coordinate of the new position
      z (float): A complex number :math:`z = x+jy`. Specifying ``z``
        overrides the ``x`` and ``y`` arguments.
    """

    # Convert from complex coordinates
    if z is not None:
      x = np.real(z)
      y = np.imag(z)

    self.Qelm.setPos((x-self.anim.sceneLimits['x'][0])*self.anim.factor,
      -(y-self.anim.sceneLimits['y'][0])*self.anim.factor)
  

# === Animation ============================================================

class Animation2d():
  """
  2D Animation

  Base class for two-dimensional animations.

  The :py:attr:`Animation2d.Qview` attribute is a ``QGraphicsView`` and can thus
  be used directly as a QWidget in any Qt application. For rapid display, the
  companion class :class:`Window` allows to easily create a new window for
  the animation.

  .. note:: Two times are at play in an animation: the *display* time, whose 
    increments are approximately the inverse of the :py:attr:`Animation2d.fps`
    attribute, and the *animation* time, which is a virtual quantity unrelated 
    to the actual time. This way, slow motion or fast-forward animations can
    be displayed. The :py:attr:`Animation2d.dt` attibute controls the increment
    of animation time between two display updates.
  
  Attributes:
    elm ({:class:`.element`}): All elements in the scene.
    sceneLimits ({'x', 'y', 'width', 'height'}): Limits of the scene.
    margin (float): Margin around the scene (pix).
    timeHeight (float): Position of the time display relative to the top of the
      scene (pix).
    fps (float): Display framerate (1/s).
    t (float): Current animation time (s).
    dt (float): Animation time increment (s) between two updates.
    disp_time (bool): If true, the animation time is overlaid to the animation.
    window (:class:`.Window`): If not None, a simple window containing the 
      animation.
    Qscene (``QGraphicsScene``): ``QGraphicsScene`` containing the elements.
    Qview (``QGraphicsView``): ``QGraphicsView`` widget representing the scene.
    timer (``QElapsedTimer``): Timer storing the display time since the 
      animation start.
    Qtimer (``QTimer``): Timer managing the display updates.
  """

  def __init__(self, dt=None, disp_time=False, window=None):
    """
    Animation constructor

    Defines all the attributes of the animation, especially the ``QGraphicsScene``
    and ``QGraphicsView`` necessary for rendering.

    Args:
      dt (float): Animation time increment (s) between two updates.
      disp_time (bool): If true, the animation time is overlaid to the animation.
      window (:class:`.Window`): If not None, a simple window containing the 
        animation.
    """
    # --- Time

    self.t = 0
    self.dt = dt
    self.disp_time = disp_time

    # Framerate
    self.fps = 25

    # --- Window

    self.window = window
    if self.window is not None:
      self.window.anim = self

    # -- Settings

    # Sizes
    self.sceneLimits = {'x':(0,1), 'y':(0,1), 'width':None, 'height':None}
    self.margin = 25
    self.timeHeight = 0.02*QApplication.desktop().screenGeometry().height()

    # --- Scene & view

    # Scene
    self.Qscene = QGraphicsScene()
    self.Qview = QGraphicsView()
    self.Qview.setScene(self.Qscene)

    self.elm = defaultdict()

    # --- Display

    # Dark background
    self.Qview.setBackgroundBrush(Qt.black)
    pal = self.Qview.palette()
    pal.setColor(QPalette.Window, Qt.black)
    self.Qview.setPalette(pal)

    # Antialiasing
    self.Qview.setRenderHints(QPainter.Antialiasing)

    # --- Animation
  
    self.qtimer = QTimer()
    self.qtimer.timeout.connect(self.update)
    self.timer = QElapsedTimer()
  
  def init(self, size=None):
    """
    Animation initialization

    Computes all necessary values for rendering.

    Args:
      size (float): Height of the ``QGraphicsView`` widget.
    """

    # Scene width and height
    self.sceneLimits['width'] = self.sceneLimits['x'][1]-self.sceneLimits['x'][0]
    self.sceneLimits['height'] = self.sceneLimits['y'][1]-self.sceneLimits['y'][0]

    # --- Scale factor and margin

    if size is None:
      self.factor = QApplication.desktop().screenGeometry().height()/self.sceneLimits['height']*0.6

    else:
      self.factor = size/self.sceneLimits['height']

    # Scene boundaries
    self.boundaries = QGraphicsRectItem(0,0,
      self.factor*self.sceneLimits['width'],
      -self.factor*self.sceneLimits['height'])
    self.boundaries.setPen(QPen(Qt.lightGray, 0)) 
    self.Qscene.addItem((self.boundaries))

    # Time display
    if self.disp_time:
      self.timeDisp = self.Qscene.addText("---")
      self.timeDisp.setDefaultTextColor(QColor('white'))
      self.timeDisp.setPos(0, -self.timeHeight-self.factor*self.sceneLimits['height'])

    # Elements
    for k,elm in self.elm.items():
      elm.convert(self)
      if elm.parent is None:
        self.Qscene.addItem(elm.Qelm)

  def startAnimation(self):
    """
    Start the animation

    Trigs the animation :py:attr:`Animation.Qtimer` ``QTimer``, which starts
    the animation.
    """
    self.qtimer.setInterval(int(1000/self.fps))
    self.qtimer.start()
    self.timer.start()

  def update(self):
    """
    Update animation state

    Update the animation time :py:attr:`Animation.t`. Subclass this method
    to implement the animation, *e.g.* moving elements or changing color.
    """

    # Update time
    if self.dt is None:
      self.t = self.timer.elapsed()/1000 
    else: 
      self.t += self.dt

    # Timer display
    if self.disp_time:
      self.timeDisp.setPlainText('{:06.02f} sec'.format(self.t))
    
# === WINDOW ===============================================================

class Window():
  """
  Animation-specific window

  Creates a new window containing an animation.
  
  Attributes:
    title (str): Title of the window.
    app (``QApplication``): Underlying ``QApplication``.
    anim (:class:`Animation2d`): Animation to display.
  """

  def __init__(self, title='Animation'):
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

    # Animation
    self.anim = None
    
  def show(self, size=None):
    """
    Creates the animation window
    
    Create the window to display the animation, defines the shortcuts,
    initialize and start the animation.

    Args:
      size (float): Height of the ``QGraphicsView`` widget, defining the 
        height of the window.
    """
    # --- Animation

    if self.anim is None:
      self.anim = Animation2d(window=self)

    # Window title
    self.anim.Qview.setWindowTitle(self.title)

    # --- Shortcuts

    self.shortcut = defaultdict()

    # Quit
    self.shortcut['esc'] = QShortcut(QKeySequence('Esc'), self.anim.Qview)
    self.shortcut['esc'].activated.connect(self.app.quit)

    # --- Initialization

    # Initialize animation
    self.anim.init(size=size)

    # Window size
    self.anim.Qview.resize(
      int(self.anim.factor*self.anim.sceneLimits['width']+2*self.anim.margin), 
      int(self.anim.factor*self.anim.sceneLimits['height']+2*self.anim.margin+self.anim.timeHeight))

    self.anim.Qview.show()
    self.anim.startAnimation()
    self.app.exec()

  def close(self):
    self.app.quit()