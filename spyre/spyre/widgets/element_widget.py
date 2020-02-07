from PyQt5 import QtWidgets, QtCore, QtGui

class EventFilter(QtCore.QObject):

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.MouseButtonPress:
            event.accept()
            return True
        else:
            return super().eventFilter(obj, event)

class ElementResizerItem(QtWidgets.QGraphicsRectItem):

    grid_size = 10

    def __init__(self, element_item, parent=None):
        super().__init__(parent=parent)
        self.element_item = element_item
        self.setFlag(self.ItemIsMovable, True)
        self.setFlag(self.ItemSendsGeometryChanges, True)
        self.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0)))
        self.setBrush(QtGui.QBrush(QtGui.QColor(255, 255, 255)))
        return

    def mouseMoveEvent(self, ev):
        new_pos = ev.pos()

        x, y = new_pos.x(), new_pos.y()
        x = self.grid_size * round(x / self.grid_size)
        y = self.grid_size * round(y / self.grid_size)
        new_pos = QtCore.QPointF(x, y)


        container = self.element_item.container
        proxy = self.element_item.proxy
        header = self.element_item

        border = self.element_item.border
        header_height = self.element_item.header_height
        resizer_size = self.element_item.resizer_size

        rect = container.rect()
        x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
        container.setRect(x, y, new_pos.x(), new_pos.y())
        proxy.setGeometry(QtCore.QRectF(0, 0, new_pos.x() - 2 * border, new_pos.y() - 2 * border))
        header.setRect(x, y - header_height, new_pos.x(), y + header_height + border)
        self.setRect(x + w - resizer_size / 2, y + h - resizer_size / 2, resizer_size, resizer_size)
        ev.accept()
        return

class ElementItem(QtWidgets.QGraphicsRectItem):

    header_height = 16
    border = 5
    resizer_size = 5
    grid_size = 10

    def __init__(self, element, parent=None):
        super().__init__(parent=parent)
        w = element()
        self.container_widget = QtWidgets.QWidget()
        self.event_filter = EventFilter()
        self.container_widget.installEventFilter(self.event_filter)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        w.setSizePolicy(sizePolicy)
        layout = QtWidgets.QHBoxLayout(self.container_widget)
        layout.addWidget(w)
        layout.setContentsMargins(0, 0, 0, 0)
        self.container_widget.setLayout(layout)

        self.proxy = QtWidgets.QGraphicsProxyWidget()
        self.proxy.setWidget(self.container_widget)
        # self.proxy.setGeometry(QtCore.QRectF(0, 0, 600, 600))

        self.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0)))
        self.setBrush(QtGui.QBrush(QtGui.QColor(200, 200, 200)))
        self.setFlag(self.ItemIsMovable, True)
        self.setFlag(self.ItemSendsGeometryChanges, True)
        self.setFlag(self.ItemIsSelectable, True)

        x, y, w, h = self.container_widget.x(), self.container_widget.y(), self.container_widget.width(), self.container_widget.height()

        rect = [
            x - self.border,
            y - self.border - self.header_height,
            w + 2 * self.border,
            self.header_height,
        ]
        self.setRect(*rect)

        self.header_text = QtWidgets.QGraphicsTextItem(element.name)
        self.header_text.setPos(-5, -24)
        # font = QtGui.QFont('Consolas', 8)
        font = QtGui.QFont()
        font = QtGui.QFont(font.defaultFamily(), 9)
        color = QtGui.QColor(0, 0, 0)
        self.header_text.setFont(font)
        self.header_text.setDefaultTextColor(color)

        self.container = QtWidgets.QGraphicsRectItem()
        self.container.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0)))
        self.container.setBrush(QtGui.QBrush(QtGui.QColor(100, 100, 100)))

        rect = [
            x - self.border,
            y - self.border,
            w + 2 * self.border,
            h + 2 * self.border,
        ]
        self.container.setRect(*rect)

        self.resizer = ElementResizerItem(self)
        crect = self.container.rect()
        cx, cy, ch, cw = crect.x(), crect.y(), crect.height(), crect.width()
        rect = [
            cx + cw - self.resizer_size / 2,
            cy + ch - self.resizer_size / 2,
            self.resizer_size,
            self.resizer_size,
        ]
        self.resizer.setRect(*rect)
        self.resizer.setParentItem(self.container)
        self.proxy.setParentItem(self.container)
        self.container.setParentItem(self)
        self.header_text.setParentItem(self)
        return

    def itemChange(self, change, value):
        if change == self.ItemPositionChange:
            new_pos = value.toPoint()
            x, y = new_pos.x(), new_pos.y()
            x = self.grid_size * round(x / self.grid_size)
            y = self.grid_size * round(y / self.grid_size)
            value = QtCore.QPointF(x, y)
        return super().itemChange(change, value)
