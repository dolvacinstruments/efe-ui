from PySide6.QtCore import Qt, QPoint, QRectF, Signal
from PySide6.QtGui import (
    QFont,
    QMouseEvent,
    QPainter,
    QPen,
    QWheelEvent,
)
from PySide6.QtWidgets import QWidget


class DigitEdit(QWidget):
    value_changed = Signal(float)

    _COL_W = 24
    _SEP_W = 8
    _ARROW_H = 8
    _DIGIT_H = 22
    _PAD = 1

    def __init__(
        self,
        integer_digits: int = 1,
        decimal_places: int = 3,
        initial_value: float = 0.0,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._integer_digits = integer_digits
        self._decimal_places = decimal_places
        self._scale = 10**decimal_places
        self._total_digit_cols = integer_digits + decimal_places
        self._min_raw = 0
        self._max_raw = 2500
        self._hovered_col: int | None = None
        self._connected = False

        self._value = initial_value
        self._font = QFont("monospace", 12)
        self._font.setBold(True)

        total_w = (
            self._total_digit_cols * self._COL_W
            + (self._total_digit_cols - 1) * self._PAD
        )
        if decimal_places > 0:
            total_w += self._SEP_W
        total_h = self._ARROW_H * 2 + self._DIGIT_H
        self.setFixedSize(total_w, total_h)
        self.setMouseTracking(True)

    def set_connected(self, connected: bool) -> None:
        self._connected = connected
        self.update()

    def value(self) -> float:
        return self._value

    def set_value(self, value: float) -> None:
        self._value = max(0.0, min(value, self._max_raw / self._scale))
        self.value_changed.emit(self._value)
        self.update()

    def _raw(self) -> int:
        return round(self._value * self._scale)

    def _scale_for_col(self, col: int) -> int:
        return 10 ** (self._total_digit_cols - 1 - col)

    def _col_x(self, col: int) -> float:
        x = col * (self._COL_W + self._PAD)
        if self._decimal_places > 0 and col >= self._integer_digits:
            x += self._SEP_W
        return float(x)

    def _sep_x(self) -> float:
        return float(self._integer_digits * (self._COL_W + self._PAD) - self._PAD // 2)

    def _col_at(self, x: float) -> int | None:
        for col in range(self._total_digit_cols):
            cx = self._col_x(col)
            if cx <= x <= cx + self._COL_W:
                return col
        return None

    def _zone_at(self, y: float) -> str | None:
        if y < self._ARROW_H:
            return "up"
        if y < self._ARROW_H + self._DIGIT_H:
            return "digit"
        return "down"

    def _change(self, col: int, delta: int) -> None:
        if not self._connected:
            return
        raw = self._raw()
        step = self._scale_for_col(col)
        new_raw = raw + delta * step
        if new_raw < self._min_raw or new_raw > self._max_raw:
            return
        self._value = new_raw / self._scale
        self.value_changed.emit(self._value)
        self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        pos = event.pos()
        col = self._col_at(pos.x())
        if col is None:
            return
        zone = self._zone_at(pos.y())
        if zone == "up":
            self._change(col, 1)
        elif zone == "down":
            self._change(col, -1)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        col = self._col_at(event.pos().x())
        if col != self._hovered_col:
            self._hovered_col = col
            self.update()

    def leaveEvent(self, event) -> None:
        if self._hovered_col is not None:
            self._hovered_col = None
            self.update()

    def wheelEvent(self, event: QWheelEvent) -> None:
        col = self._col_at(event.position().x())
        if col is None:
            return
        delta = 1 if event.angleDelta().y() > 0 else -1
        self._change(col, delta)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        color = self.palette().text().color()
        raw = self._raw()

        for col in range(self._total_digit_cols):
            cx = self._col_x(col)
            scale = self._scale_for_col(col)
            digit = (raw // scale) % 10
            hovered = col == self._hovered_col

            # digit text
            digit_rect = QRectF(
                cx,
                float(self._ARROW_H),
                float(self._COL_W),
                float(self._DIGIT_H),
            )
            p.setPen(color)
            p.setFont(self._font)
            p.drawText(digit_rect, Qt.AlignmentFlag.AlignCenter, str(digit))

            # arrows on hover
            if hovered and self._connected:
                self._draw_arrow(p, cx, 2, True)
                self._draw_arrow(p, cx, self._ARROW_H + self._DIGIT_H + 2, False)

        # decimal point
        if self._decimal_places > 0:
            sx = self._sep_x()
            sep_rect = QRectF(
                sx,
                float(self._ARROW_H),
                float(self._SEP_W),
                float(self._DIGIT_H),
            )
            p.setPen(color)
            p.setFont(self._font)
            p.drawText(sep_rect, Qt.AlignmentFlag.AlignCenter, ".")

        p.end()

    def _draw_arrow(self, p: QPainter, col_x: float, y: float, up: bool) -> None:
        color = self.palette().text().color()
        p.setPen(QPen(color, 1))
        p.setBrush(color)
        cx = col_x + self._COL_W / 2
        aw = 8
        ah = 4
        if up:
            points = [
                QPoint(int(cx), int(y)),
                QPoint(int(cx - aw / 2), int(y + ah)),
                QPoint(int(cx + aw / 2), int(y + ah)),
            ]
        else:
            points = [
                QPoint(int(cx), int(y + ah)),
                QPoint(int(cx - aw / 2), int(y)),
                QPoint(int(cx + aw / 2), int(y)),
            ]
        p.drawPolygon(points)
