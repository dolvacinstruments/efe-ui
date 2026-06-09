from PySide6.QtCore import Qt, QPoint, QRectF, Signal
from PySide6.QtGui import (
    QFont,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QPen,
    QWheelEvent,
)
from PySide6.QtWidgets import QWidget

_COL_W = 18
_SEP_W = 6
_ARROW_H = 8
_DIGIT_H = 22
_PAD = 0


class Readout(QWidget):
    def __init__(
        self,
        integer_digits: int = 1,
        decimal_places: int = 3,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._integer_digits = integer_digits
        self._decimal_places = decimal_places
        self._scale = 10**decimal_places
        self._total_digit_cols = integer_digits + decimal_places
        self._min_raw = 0
        self._max_raw = 2500
        self._raw = 0

        self._font = QFont("monospace", 12)
        self._font.setBold(True)

        total_w = self._total_digit_cols * _COL_W + (self._total_digit_cols - 1) * _PAD
        if decimal_places > 0:
            total_w += _SEP_W
        total_h = _ARROW_H * 2 + _DIGIT_H
        self.setFixedSize(total_w, total_h)

    def set_value(self, value: float) -> None:
        raw = round(value * self._scale)
        self._raw = max(self._min_raw, min(raw, self._max_raw))
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        color = self.palette().text().color()

        for col in range(self._total_digit_cols):
            cx = self._col_x(col)
            scale = 10 ** (self._total_digit_cols - 1 - col)
            digit = (self._raw // scale) % 10

            digit_rect = QRectF(
                cx,
                float(_ARROW_H),
                float(_COL_W),
                float(_DIGIT_H),
            )
            p.setPen(color)
            p.setFont(self._font)
            p.drawText(digit_rect, Qt.AlignmentFlag.AlignCenter, str(digit))

        if self._decimal_places > 0:
            sx = self._sep_x()
            sep_rect = QRectF(
                sx,
                float(_ARROW_H),
                float(_SEP_W),
                float(_DIGIT_H),
            )
            p.setPen(color)
            p.setFont(self._font)
            p.drawText(sep_rect, Qt.AlignmentFlag.AlignCenter, ".")

        p.end()

    def _col_x(self, col: int) -> float:
        x = col * (_COL_W + _PAD)
        if self._decimal_places > 0 and col >= self._integer_digits:
            x += _SEP_W
        return float(x)

    def _sep_x(self) -> float:
        return float(self._integer_digits * (_COL_W + _PAD) - _PAD // 2)


class DigitEdit(QWidget):
    value_changed = Signal(float)
    edit_committed = Signal()

    _COL_W = _COL_W
    _SEP_W = _SEP_W
    _ARROW_H = _ARROW_H
    _DIGIT_H = _DIGIT_H
    _PAD = _PAD

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
        self._cursor_col = 0
        self._cursor_visible = False
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
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def set_connected(self, connected: bool) -> None:
        self._connected = connected
        self.setEnabled(connected)
        if not connected:
            self._cursor_visible = False
            self._cursor_col = 0
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

    def _set_raw(self, raw: int) -> None:
        raw = max(self._min_raw, min(raw, self._max_raw))
        self._value = raw / self._scale
        self.value_changed.emit(self._value)
        self.update()

    def _change(self, col: int, delta: int) -> None:
        if not self._connected:
            return
        raw = self._raw()
        step = self._scale_for_col(col)
        new_raw = raw + delta * step
        if new_raw < self._min_raw or new_raw > self._max_raw:
            return
        self._cursor_visible = False
        self._set_raw(new_raw)
        self.edit_committed.emit()

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
        elif zone == "digit":
            self._cursor_col = col
            self._cursor_visible = True
            self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        col = self._col_at(event.pos().x())
        if col != self._hovered_col:
            self._hovered_col = col
            self.update()

    def leaveEvent(self, event) -> None:
        if self._hovered_col is not None:
            self._hovered_col = None
            self.update()
        if self._cursor_visible:
            self.edit_committed.emit()
        self._cursor_visible = False
        self._cursor_col = 0
        self.update()

    def enterEvent(self, event) -> None:
        self.setFocus()

    def wheelEvent(self, event: QWheelEvent) -> None:
        if not self._connected:
            return
        col = self._col_at(event.position().x())
        if col is None:
            return
        delta = 1 if event.angleDelta().y() > 0 else -1
        self._change(col, delta)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if not self._connected:
            return

        key = event.key()
        if Qt.Key.Key_0 <= key <= Qt.Key.Key_9:
            self._cursor_visible = True
            digit = key - Qt.Key.Key_0
            raw = self._raw()
            scale = self._scale_for_col(self._cursor_col)
            old = (raw // scale) % 10
            new_raw = raw - old * scale + digit * scale
            if new_raw > self._max_raw:
                new_raw = self._max_raw
            self._set_raw(new_raw)
            self._cursor_col += 1
            if self._cursor_col >= self._total_digit_cols:
                self._cursor_col = 0
                self._cursor_visible = False
                self.edit_committed.emit()
            self.update()
        elif key == Qt.Key.Key_Backspace or key == Qt.Key.Key_Delete:
            raw = self._raw()
            scale = self._scale_for_col(self._cursor_col)
            self._set_raw(raw - ((raw // scale) % 10) * scale)
            if self._cursor_col > 0:
                self._cursor_col -= 1
            self._cursor_visible = True
        elif key == Qt.Key.Key_Left:
            if self._cursor_col > 0:
                self._cursor_col -= 1
                self._cursor_visible = True
                self.update()
        elif key == Qt.Key.Key_Right:
            if self._cursor_col < self._total_digit_cols - 1:
                self._cursor_col += 1
                self._cursor_visible = True
                self.update()
        elif key == Qt.Key.Key_Home:
            self._cursor_col = 0
            self._cursor_visible = True
            self.update()
        elif key == Qt.Key.Key_End:
            self._cursor_col = self._total_digit_cols - 1
            self._cursor_visible = True
            self.update()
        elif key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
            self.edit_committed.emit()
            self._cursor_col = 0
            self._cursor_visible = False
            self.update()
        else:
            super().keyPressEvent(event)

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

            digit_rect = QRectF(
                cx,
                float(self._ARROW_H),
                float(self._COL_W),
                float(self._DIGIT_H),
            )
            p.setPen(color)
            p.setFont(self._font)
            p.drawText(digit_rect, Qt.AlignmentFlag.AlignCenter, str(digit))

            if col == self._cursor_col and self._cursor_visible and self._connected:
                underline = QRectF(
                    cx + 4,
                    float(self._ARROW_H + self._DIGIT_H - 3),
                    self._COL_W - 8,
                    2,
                )
                p.fillRect(underline, color)

            if hovered and self._connected:
                self._draw_arrow(p, cx, 2, True)
                self._draw_arrow(p, cx, self._ARROW_H + self._DIGIT_H + 2, False)

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
